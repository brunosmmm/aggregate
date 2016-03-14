from discover.discover import AvahiDiscoverLoop
from node.scan import scan_new_node
from node.node import PeriodicPiNode
import signal
import avahi
import re

PERIODIC_PI_NODE_REGEX = re.compile(r'^PeriodicPi node \[([a-zA-Z]+)\]')

class DuplicateNodeError(Exception):
    pass

class PeriodicPiAgg(object):
    def __init__(self, filter_iface=None):
        self.active_nodes = {}
        self.listen_iface = filter_iface

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
        new_node.register_basic_information(**scan_new_node(new_node.addr))

        self.active_nodes[m.group(1)] = new_node

        print 'new node = {} ({}) at {}'.format(new_node.node_element,
                                                new_node.description,
                                                new_node.location)

    def remove_node(self, **kwargs):

        #search and remove node
        pass

if __name__ == "__main__":

    aggregator = PeriodicPiAgg()
    discover_loop = AvahiDiscoverLoop(service_resolved_cb=aggregator.discover_new_node,
                                      service_removed_cb=aggregator.remove_node)

    #do stuff
    discover_loop.start()
    discover_loop.join()
