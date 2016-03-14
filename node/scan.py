import requests
import json
from util.misc import NodeAddress, get_full_node_address

NODE_INFO_PATH = 'status/node'
NODE_SERVICES_PATH = 'status/services'

class NodeScanError(Exception):
    pass

def retrieve_json_data(node_address, path):

    #simple data retrieval
    r = requests.get(get_full_node_address(node_address)+path)

    if r.ok == False:
        raise NodeScanError('error while connecting to node')

    try:
        return r.json()
    except Exception:
        raise NodeScanError('malformed response from node')


def scan_new_node(node_address):
    return retrieve_json_data(node_address, NODE_INFO_PATH)

def scan_node_services(node_address):
    return retrieve_json_data(node_address, NODE_SERVICES_PATH)
