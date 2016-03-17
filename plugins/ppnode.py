from periodicpy.plugmgr.plugin import Module, ModuleArgument, ModuleCapabilities
from periodicpy.plugmgr.plugin.prop import ModuleProperty, ModulePropertyPermissions
from periodicpy.plugmgr.plugin.dtype import ModuleDataTypes
from periodicpy.plugmgr.exception import HookNotAvailableError
from periodicpy.plugmgr import ModuleManagerHookActions
import re
from node.node import PeriodicPiNode

PERIODIC_PI_NODE_REGEX = re.compile(r'^PeriodicPi node \[([a-zA-Z]+)\]')

#this node driver is just a gateway; other drivers are loaded once node discovery is finished
class PPNodeDriver(Module):
    _module_desc = ModuleArgument('ppnode', 'PeriodicPi node driver')
    _capabilities = [ModuleCapabilities.MultiInstanceAllowed]
    _required_kw = [ModuleArgument('address', 'node address'),
                    ModuleArgument('port', 'node port'),
                    ModuleArgument('name', 'node advertised name')]
    _properties = {'node_element' : ModuleProperty('Node identifying element',
                                                   ModulePropertyPermissions.READ,
                                                   data_type=ModuleDataTypes.STRING)}


    def __init__(self, **kwargs):
        super(PPNodeDriver, self).__init__(**kwargs)

        m = PERIODIC_PI_NODE_REGEX.match(kwargs['name'])
        self.node = PeriodicPiNode(m.group(1), [kwargs['address'], kwargs['port']])
        self.node.register_basic_information()

        #get available drivers
        driver_list = self.interrupt_handler('get_available_drivers')
        self.node.register_services(driver_list, kwargs['drvman'])

        #register properties
        self._register_properties()

        #add to active
        self.interrupt_handler(call_custom_hook=['ppagg.add_node', [m.group(1), self.node]])
        #done
        self.interrupt_handler(log_info='new Periodic Pi node: {}'.format(m.group(1)))

    def _register_properties(self):
        self._properties['node_element'].getter = self.node.get_node_element

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
                                                  ModuleManagerHookActions.LOAD_MODULE,
                                                  PPNodeDriver)
    except HookNotAvailableError:
        raise

    return PPNodeDriver
