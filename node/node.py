from util.misc import NodeAddress
from scan import scan_new_node, scan_node_services
import logging

class NodeElementError(Exception):
    pass

class PeriodicPiNode(object):
    def __init__(self, node_element, node_address):
        self.element = node_element
        self.addr = NodeAddress(*node_address)
        #initial state
        self.scanned = False

        self.logger = logging.getLogger('ppagg.node-{}'.format(node_element))

    def register_basic_information(self):

        scan_result = scan_new_node(self.addr)

        if scan_result['node_element'] != self.element:
            raise NodeElementError('error while getting node information')

        self.__dict__.update(scan_result)

        self.scanned = True

    def register_services(self, available_drivers):

        scan_result = scan_node_services(self.addr)

        for service in scan_result['services']:
            self.logger.debug('discovered service "{}"'.format(service['service_name']))
            if service['service_name'] in available_drivers:
                #do stuff!
                self.logger.debug('driver for "{}" is available'.format(service['service_name']))
            else:
                self.logger.warn('no driver available for service {}'.format(service['service_name']))
