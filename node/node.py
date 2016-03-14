
class PeriodicPiNode(object):
    def __init__(self, node_element, node_address):
        self.element = node_element
        self.addr = node_address
        #initial state
        self.scanned = False
