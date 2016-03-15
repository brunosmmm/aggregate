from util.misc import NodeAddress
from scan import scan_new_node, scan_node_services
import logging
from service.exception import ModuleAlreadyLoadedError

class NodeElementError(Exception):
    pass

class PeriodicPiNode(object):
    def __init__(self, node_element, node_address):
        self.element = node_element
        self.addr = NodeAddress(*node_address)
        #initial state
        self.scanned = False
        self.scanned_services = {}
        self.service_drivers = {}

        self.logger = logging.getLogger('ppagg.node-{}'.format(node_element))

    def get_serializable_dict(self, simple=True):
        ret = {}

        ret['node_addr'] = self.addr.address
        ret['node_port'] = self.addr.port
        ret['node_descr'] = self.description
        ret['node_location'] = self.location
        if simple == False:
            ret['scanned_services'] = self.scanned_services
            ret['driver_instances'] = self.service_drivers

        return ret

    def register_basic_information(self):

        scan_result = scan_new_node(self.addr)

        if scan_result['node_element'] != self.element:
            raise NodeElementError('error while getting node information')

        self.__dict__.update(scan_result)

        self.scanned = True

    def register_services(self, available_drivers, driver_manager):

        scan_result = scan_node_services(self.addr)
        self.scanned_services = dict(scan_result)

        for service in scan_result['services']:
            self.logger.debug('discovered service "{}"'.format(service['service_name']))
            if service['enabled'] == False:
                self.logger.debug('service "{}" is disabled'.format(service['service_name']))
                continue

            loaded_mod_id = None
            if service['service_name'] in available_drivers:
                #do stuff!
                self.logger.debug('driver for "{}" is available'.format(service['service_name']))
                try:
                    loaded_mod_id = driver_manager.load_module(service['service_name'],
                                                               server_address=self.addr.address,
                                                               server_port=int(service['port']),
                                                               attached_node=self.element)
                except ModuleAlreadyLoadedError:
                    pass
                except TypeError:
                    #load without address (not needed)?
                    try:
                        loaded_mod_id = driver_manager.load_module(service['service_name'], attached_node=self.element)
                    except Exception:
                        #give up
                        raise

            else:
                self.logger.warn('no driver available for service {}'.format(service['service_name']))

            #save module information
            self.service_drivers[service['service_name']] = loaded_mod_id
