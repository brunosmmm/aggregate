from discover.discover import AvahiDiscoverLoop, SimpleSSDPDiscovery
from node.node import PeriodicPiNode
import signal
import avahi
import re
import importlib
import logging
from periodicpy.plugmgr import ModuleManager
from jsonsrv.server import PeriodicPiAggController
import pyjsonrpc
from periodicpy.zeroconf import ZeroconfService
import time
import socket

PERIODIC_PI_NODE_REGEX = re.compile(r'^PeriodicPi node \[([a-zA-Z]+)\]')
IPV4_REGEX = re.compile(r'(([0-9]{0,3})\.){3}[0-9]{0,3}')
IPV6_REGEX = re.compile(r'[0-9a-fA-F]{0,4}::(([0-9a-fA-F]{0,4}):){3}[0-9a-fA-F]{0,4}')

class DuplicateNodeError(Exception):
    pass

class PeriodicPiAgg(object):
    def __init__(self, filter_iface=None, aggregator_element='lithium'):
        self.active_nodes = {}
        self.listen_iface = filter_iface
        self.agg_element = aggregator_element
        self.running = False
        self.service_types = set(['_http._tcp'])
        self.ssdp_services = []

        self.logger = logging.getLogger('ppagg.ctrl')

        self.drvman = ModuleManager('ppagg', 'plugins', 'scripts')

        #install custom methods
        self.drvman.install_custom_method('ppagg.add_node', self.add_active_node)
        self.drvman.install_custom_method('ppagg.get_nodes', self.get_active_nodes)
        self.drvman.install_custom_method('ppagg.del_node', self.del_active_node)
        self.drvman.install_custom_method('ppagg.get_addr', self.get_server_address)
        self.drvman.install_custom_method('ppagg.add_mdns_kind', self.add_service_kind)
        self.drvman.install_custom_method('ppagg.add_ssdp_search', self.add_ssdp_search)

        #install custom hooks
        self.drvman.install_custom_hook('ppagg.node_discovered')
        self.drvman.install_custom_hook('ppagg.node_removed')
        self.drvman.install_custom_hook('ppagg.ssdp_discovered')
        self.drvman.install_custom_hook('ppagg.ssdp_removed')
        self.drvman.install_custom_hook('ppagg.agg_started')
        self.drvman.install_custom_hook('ppagg.agg_stopped')

        #discover modules
        self.logger.info('Initial plugin scan')
        self.drvman.discover_modules()
        self.available_drivers = []
        for driver in self.drvman.list_discovered_modules().values():
            self.available_drivers.append(driver.arg_name)

        #discover scriots
        self.logger.info('Initial script scan')
        self.drvman.discover_scripts()

        #service discover loop
        self.discover_loop = None
        self.json_server = None

    def startup(self):

        self.logger.info('Aggregator starting up...')
        #setup service discovery loop
        self.discover_loop = AvahiDiscoverLoop(root_logger='ppagg',
                                               service_resolved_cb=self.discover_new_node,
                                               service_removed_cb=self.remove_node,
                                               type_filter=self.service_types)

        self.ssdp_search = SimpleSSDPDiscovery(root_logger='ppagg',
                                               interval=3,
                                               removal_interval=10,
                                               service_discovered_cb=self.discover_ssdp,
                                               service_removed_cb=self.remove_ssdp)

        #setup json server
        self.json_server = PeriodicPiAggController(self.drvman, self.active_nodes)

        #start loop
        self.discover_loop.start()
        #publish aggregator
        self._publish_aggregator()

        #start json server
        self.json_server.start()

        self.ssdp_search.start()
        for ssdp_service in self.ssdp_services:
            self.ssdp_search.add_discovery_type(**ssdp_service)

        #trigger start hook
        self.drvman.trigger_custom_hook('ppagg.agg_started', address='', port=80)

        self.logger.info('Aggregator successfully started')
        self.running = True

    def shutdown(self):

        self.logger.info('Agregator shutting down...')

        #trigger stop hook
        self.drvman.trigger_custom_hook('ppagg.agg_stopped')

        #unpublish aggregator
        self._unpublish_aggregator()
        #wait for discovery loop to shutdown
        self.discover_loop.stop()
        self.discover_loop.join()

        #wait for json server to shutdown
        self.json_server.stop()
        self.json_server.join()

        self.ssdp_search.stop()
        self.ssdp_search.join()

    def module_tick(self):
        self.drvman.module_system_tick()

    def _unpublish_aggregator(self):
        self.avahi_service.unpublish()

    def _publish_aggregator(self):
        self.logger.debug('publishing aggregator service')
        self.avahi_service = ZeroconfService(name='PeriodicPi Aggregator [{}]'.format(self.agg_element),
                                             port=8080,
                                             stype='_http._tcp')
        self.avahi_service.publish()

    def get_active_nodes(self):
        return self.active_nodes.keys()

    def add_service_kind(self, service_kind):
        #for simplicity sake, only allow to insert types before startup (for now)
        if self.running:
            return False

        self.logger.debug('adding service type "{}" to scan filter'.format(service_kind))
        self.service_types.add(service_kind)
        return True

    def add_ssdp_search(self, host_addr, host_port, service_type):

        if self.running:
            return False

        self.ssdp_services.append({'host_addr': host_addr,
                                   'host_port': host_port,
                                   'service_type': service_type})

    def add_active_node(self, node_name, node_object):
        if node_name in self.active_nodes:
            raise DuplicateNodeError('node is already active')

        self.logger.debug('adding node "{}" to the active node list'.format(node_name))
        self.active_nodes[node_name] = node_object

    def del_active_node(self, node_name):
        if node_name not in self.active_nodes:
            self.logger.warn('node "{}" is not present'.format(node_name))
            return

        self.logger.debug('removing node "{}" from the active node list'.format(node_name))
        del self.active_nodes[node_name]

    def discover_new_node(self, **kwargs):
        #filter out uninteresting stuff
        #no IPv6
        if kwargs['proto'] != avahi.PROTO_INET:
            return

        if IPV6_REGEX.match(kwargs['address']):
            return

        #if kwargs['kind'] != '_http._tcp':
        #    return

        if self.listen_iface != None:
            if kwargs['iface'] != self.listen_iface:
                return

        self.logger.debug('discovered new service: {}'.format(kwargs['name']))
        self.drvman.trigger_custom_hook('ppagg.node_discovered', **kwargs)

    def remove_node(self, **kwargs):
        #no IPv6
        if kwargs['proto'] != avahi.PROTO_INET:
            return

        #search and remove node
        self.logger.debug('service was removed: {}'.format(kwargs['name']))
        self.drvman.trigger_custom_hook('ppagg.node_removed', **kwargs)

    def discover_ssdp(self, **kwargs):
        self.logger.debug('discovered service through ssdp with usn: {}'.format(kwargs['USN']))
        self.drvman.trigger_custom_hook('ppagg.ssdp_discovered', **kwargs)

    def remove_ssdp(self, **kwargs):
        self.logger.debug('ssdp service with usn {} was removed'.format(kwargs['USN']))
        self.drvman.trigger_custom_hook('ppagg.ssdp_removed', **kwargs)

    def get_server_address(self):
        return { 'address' : socket.gethostname(), 'port' : 80 }

if __name__ == "__main__":

    def _handle_signal(*args):
        aggregator.shutdown()
        exit(0)


    logging.basicConfig(level=logging.DEBUG,
                        filename='ppagg.log',
                        filemode='a',
                        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

    logger = logging.getLogger('ppagg')

    aggregator = PeriodicPiAgg()

    #setup signal
    signal.signal(signal.SIGTERM, _handle_signal)

    #do stuff
    aggregator.startup()

    #disable annoying log messages
    logging.getLogger("requests").setLevel(logging.WARNING)

    #wait forever
    while True:
        try:
            aggregator.module_tick()
            time.sleep(1)
        except KeyboardInterrupt:
            _handle_signal(None)
