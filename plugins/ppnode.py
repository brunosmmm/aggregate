from node.service.driver import NodeServiceDriver, NodeServiceDriverArgument, DriverCapabilities
from node.service.prop import DriverProperty, DriverPropertyPermissions, PPDataTypes
from drvman.exception import HookNotAvailableError
from drvman import DriverManagerHookActions
import re
from node.node import PeriodicPiNode

PERIODIC_PI_NODE_REGEX = re.compile(r'^PeriodicPi node \[([a-zA-Z]+)\]')

#this node driver is just a gateway; other drivers are loaded once node discovery is finished
class PPNodeDriver(NodeServiceDriver):
    _module_desc = NodeServiceDriverArgument('ppnode', 'PeriodicPi node driver')
    _capabilities = [DriverCapabilities.MultiInstanceAllowed]
    _required_kw = [NodeServiceDriverArgument('address', 'node address'),
                    NodeServiceDriverArgument('port', 'node port'),
                    NodeServiceDriverArgument('name', 'node advertised name')]
    _properties = {'node_element' : DriverProperty('Node identifying element',
                                                   DriverPropertyPermissions.READ,
                                                   getter=None,
                                                   setter=None,
                                                   data_type=PPDataTypes.STRING)}


    def __init__(self, **kwargs):
        super(PPNodeDriver, self).__init__(**kwargs)

        m = PERIODIC_PI_NODE_REGEX.match(kwargs['name'])
        self.node = PeriodicPiNode(m.group(1), [kwargs['address'], kwargs['port']])
        self.node.register_basic_information()

        #get available drivers
        driver_list = self.interrupt_handler('get_available_drivers')
        self.node.register_services(driver_list, kwargs['drvman'])

        #add to active
        self.interrupt_handler(call_custom_hook=['ppagg.add_node', [m.group(1), self.node]])
        #done
        self.interrupt_handler(log_info='new Periodic Pi node: {}'.format(m.group(1)))

    @classmethod
    def new_node_detected(cls, **kwargs):

        m = PERIODIC_PI_NODE_REGEX.match(kwargs['name'])
        if m == None:
            return False

        return True


def discover_module(module_manager_object):
    #install driver loading hook
    try:
        module_manager_object.install_driver_hook('drvman.new_node',
                                                  PPNodeDriver.new_node_detected,
                                                  DriverManagerHookActions.LOAD_MODULE,
                                                  PPNodeDriver)
    except HookNotAvailableError:
        raise

    return PPNodeDriver
