import requests
import json
from util.misc import NodeAddress, get_full_node_address

NODE_INFO_PATH = 'status/node'
NODE_SERVICES_PATH = 'status/services'

class NodeScanError(Exception):
    pass

def scan_new_node(node_address):

    #simple data retrieval
    r = requests.get(get_full_node_address(node_address)+NODE_INFO_PATH)

    if r.ok == False:
        raise NodeScanError('error while connecting to node')

    try:
        return r.json()
    except Exception:
        raise NodeScanError('malformed response from node')
