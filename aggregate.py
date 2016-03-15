from discover.discover import AvahiDiscoverLoop
from node.node import PeriodicPiNode
import signal
import avahi
import re
import importlib
import logging
from drvman import DriverManager
from jsonsrv.server import PeriodicPiAggController
import pyjsonrpc
from periodicpy.zeroconf import ZeroconfService
import time

PERIODIC_PI_NODE_REGEX = re.compile(r'^PeriodicPi node \[([a-zA-Z]+)\]')

class DuplicateNodeError(Exception):
    pass

class PeriodicPiAgg(object):
    def __init__(self, filter_iface=None):
        self.active_nodes = {}
        self.listen_iface = filter_iface

        self.logger = logging.getLogger('ppagg.ctrl')

        self.drvman = DriverManager('ppagg')
        self.available_drivers = []
        for driver in self.drvman.list_discovered_modules():
            self.available_drivers.append(driver.arg_name)

        #install custom hook
        self.drvman.install_custom_hook('ppagg.add_node', self.add_active_node)

        #service discover loop
        self.discover_loop = None
        self.json_server = None

    def startup(self):

        self.logger.info('Aggregator starting up...')
        #setup service discovery loop
        self.discover_loop = AvahiDiscoverLoop(service_resolved_cb=aggregator.discover_new_node,
                                               service_removed_cb=aggregator.remove_node)

        #setup json server
        self.json_server = PeriodicPiAggController(self.drvman, self.active_nodes)

        #start loop
        self.discover_loop.start()
        #publish aggregator
        self._publish_aggregator()

        #start json server
        self.json_server.start()

        self.logger.info('Aggregator successfully started')

    def shutdown(self):

        self.logger.info('Agregator shutting down...')
        #unpublish aggregator
        self._unpublish_aggregator()
        #wait for discovery loop to shutdown
        self.discover_loop.stop()
        self.discover_loop.join()

        #wait for json server to shutdown
        self.json_server.stop()
        self.json_server.join()

    def _unpublish_aggregator(self):
        self.avahi_service.unpublish()

    def _publish_aggregator(self):
        self.logger.debug('publishing aggregator service')
        self.avahi_service = ZeroconfService(name='PeriodicPi Aggregator',
                                             port=8080,
                                             stype='_http._tcp')
        self.avahi_service.publish()

    def add_active_node(self, node_name, node_object):
        if node_name in self.active_nodes:
            raise DuplicateNodeError('node is already active')

        self.active_nodes[node_name] = node_object

    def discover_new_node(self, **kwargs):
        #filter out uninteresting stuff
        #no IPv6
        if kwargs['proto'] != avahi.PROTO_INET:
            return

        if kwargs['kind'] != '_http._tcp':
            return

        if self.listen_iface != None:
            if kwargs['iface'] != self.listen_iface:
                return

        self.logger.debug('discovered new service: {}'.format(kwargs['name']))

        self.drvman.new_node_discovered_event(**kwargs)

    def remove_node(self, **kwargs):

        #search and remove node
        pass

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

    #wait forever
    while True:
        try:
            time.sleep(1)
        except KeyboardInterrupt:
            _handle_signal(None)
