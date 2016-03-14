from collections import namedtuple

NodeAddress = namedtuple('NodeAddress', ['address', 'port'])

def get_full_node_address(node_address):
    return 'http://{}:{}/'.format(node_address.address, node_address.port)
