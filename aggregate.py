from discover.discover import AvahiDiscoverLoop
from node.node import PeriodicPiNode
import signal
import avahi
import re

PERIODIC_PI_NODE_REGEX = re.compile(r'^PeriodicPi node \[([a-zA-Z]+)\]')

class PeriodicPiAgg(object):
    def __init__(self, filter_iface=None):
        self.active_nodes = []
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

        #add node
        self.active_nodes.append(PeriodicPiNode(m.group(1), [kwargs['address'], kwargs['port']]))

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
