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

        m = PERIODIC_PI_NODE_REGEX.match(kwargs['name'])
        if m == None:
            return

        #duplicate node (add to logging when available)
        if m.group(1) in self.active_nodes:
            return

        #add node
        new_node = PeriodicPiNode(m.group(1), [kwargs['address'], kwargs['port']])
        #scan
        new_node.register_basic_information()
        new_node.register_services(self.available_drivers, self.drvman)

        self.active_nodes[m.group(1)] = new_node

        self.logger.info('new node: {} ({}) at {}'.format(new_node.node_element,
                                                          new_node.description,
                                                          new_node.location))

    def remove_node(self, **kwargs):

        #search and remove node
        pass

if __name__ == "__main__":

    logging.basicConfig(level=logging.DEBUG,
                        filename='ppagg.log',
                        filemode='a',
                        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

    #console = logging.StreamHandler()
    #console.setLevel(logging.INFO)
    #logging.getLogger('').addHandler(console)

    logger = logging.getLogger('ppagg')

    aggregator = PeriodicPiAgg()
    discover_loop = AvahiDiscoverLoop(service_resolved_cb=aggregator.discover_new_node,
                                      service_removed_cb=aggregator.remove_node)

    #JSON server
    json_server = PeriodicPiAggController(aggregator.drvman, aggregator.active_nodes)

    #do stuff
    discover_loop.start()
    json_server.start()

    json_server.join()
    discover_loop.join()
