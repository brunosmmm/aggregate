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
        self.node.register_services(driver_list, self.interrupt_handler)

        #get plugin information, build structures
        self.node.register_node_plugins()

        #connect properties, methods
        self._automap_properties()
        self._automap_methods()

        #attach to custom aggregator hooks
        self.interrupt_handler(attach_custom_hook=['ppagg.node_removed',
                                                   [self._node_removed,
                                                    ModuleManagerHookActions.UNLOAD_MODULE,
                                                    self._registered_id]])

        self.interrupt_handler(attach_custom_hook=['ppagg.agg_started',
                                                   [self._agg_started,
                                                    ModuleManagerHookActions.NO_ACTION,
                                                    None]])

        self.interrupt_handler(attach_custom_hook=['ppagg.agg_stopped',
                                                   [self._agg_stopped,
                                                    ModuleManagerHookActions.NO_ACTION,
                                                    None]])

        #install external interrupt handler
        self.interrupt_handler(install_interrupt_handler=['{}pp.inthandler'.format(m.group(1)),
                                                          self._node_interrupt_handler])

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

    def _node_removed(self, **kwargs):
        m = PERIODIC_PI_NODE_REGEX.match(kwargs['name'])

        if m == None:
            return False

        if m.group(1) == self._get_node_element():
            #got removed
            self.node.unregister_services(self.interrupt_handler)
            return True

        return False

    def _node_interrupt_handler(self, **kwargs):
        pass # for now

    def _agg_started(self, **kwargs):
        self.node.agg_startup(**kwargs)

    def _agg_stopped(self):
        self.node.agg_shutdown()

    @classmethod
    def new_node_detected(cls, **kwargs):

        m = PERIODIC_PI_NODE_REGEX.match(kwargs['name'])
        if m == None:
            return False

        return True


def discover_module(**kwargs):
    #install driver loading hook
    try:
        kwargs['modman'].attach_custom_hook('ppagg.node_discovered',
                                            PPNodeDriver.new_node_detected,
                                            ModuleManagerHookActions.LOAD_MODULE,
                                            PPNodeDriver)
    except HookNotAvailableError:
        raise

    return PPNodeDriver
