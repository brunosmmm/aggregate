from periodicpy.plugmgr.plugin import Module, ModuleArgument, ModuleCapabilities
from periodicpy.plugmgr.plugin.prop import ModuleProperty, ModulePropertyPermissions
from periodicpy.plugmgr.plugin.method import ModuleMethod, ModuleMethodArgument
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
                                                   data_type=ModuleDataTypes.STRING),
                   'node_plugins' : ModuleProperty('Plugins active at node',
                                                   ModulePropertyPermissions.READ,
                                                   data_type=ModuleDataTypes.STRING_LIST)}

    _methods = {'call_plugin_method' : ModuleMethod(method_desc='Call a method provided by a node plugin',
                                                    method_args={'instance_name' : ModuleMethodArgument(argument_desc='Plugin instance name',
                                                                                                        required=True,
                                                                                                        data_type=ModuleDataTypes.STRING),
                                                                 'method_name' : ModuleMethodArgument(argument_desc='Method name',
                                                                                                      required=True,
                                                                                                      data_type=ModuleDataTypes.STRING),
                                                                 'method_args' : ModuleMethodArgument(argument_desc='Method arguments',
                                                                                                      required=False,
                                                                                                      data_type=ModuleDataTypes.DICT)},
                                                    method_return=ModuleDataTypes.VOID),
                'inspect_plugin' : ModuleMethod(method_desc='Inspect plugin structure',
                                                method_args={'instance_name' : ModuleMethodArgument(argument_desc='Plugin instance name',
                                                                                                    required=True,
                                                                                                    data_type=ModuleDataTypes.STRING)},
                                                method_return=ModuleDataTypes.DICT)}

    def __init__(self, **kwargs):
        super(PPNodeDriver, self).__init__(**kwargs)

        m = PERIODIC_PI_NODE_REGEX.match(kwargs['name'])
        self.node = PeriodicPiNode(m.group(1), [kwargs['address'], kwargs['port']])
        self.node.register_basic_information()

        #get available drivers
        driver_list = self.interrupt_handler('get_available_drivers')
        self.node.register_services(driver_list, kwargs['plugmgr'])

        #get plugin information, build structures
        self.node.register_node_plugins()

        #connect properties, methods
        self._automap_properties()
        self._automap_methods()

        #add to active
        self.interrupt_handler(call_custom_method=['ppagg.add_node', [m.group(1), self.node]])
        #done
        self.interrupt_handler(log_info='new Periodic Pi node: {}'.format(m.group(1)))

    #property getter
    def _get_node_element(self):
        return self.node.get_node_element()

    def _get_node_plugins(self):
        return self.node.get_node_plugins()

    def _call_plugin_method(self, instance_name, method_name, method_args=None):
        return self.node.call_plugin_method(instance_name, method_name, method_args)

    def _inspect_plugin(self, instance_name):
        return self.node.get_node_plugin_structure(instance_name)

    @classmethod
    def new_node_detected(cls, **kwargs):

        m = PERIODIC_PI_NODE_REGEX.match(kwargs['name'])
        if m == None:
            return False

        return True


def discover_module(module_manager_object):
    #install driver loading hook
    try:
        module_manager_object.attach_custom_hook('ppagg.node_discovered',
                                                  PPNodeDriver.new_node_detected,
                                                  ModuleManagerHookActions.LOAD_MODULE,
                                                  PPNodeDriver)
    except HookNotAvailableError:
        raise

    return PPNodeDriver
