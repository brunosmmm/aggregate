
from util.misc import NodeAddress

class NodeElementError(Exception):
    pass

class PeriodicPiNode(object):
    def __init__(self, node_element, node_address):
        self.element = node_element
        self.addr = NodeAddress(*node_address)
        #initial state
        self.scanned = False

    def register_basic_information(self, **kwargs):

        if kwargs['node_element'] != self.element:
            raise NodeElementError('error while getting node information')

        self.__dict__.update(kwargs)
