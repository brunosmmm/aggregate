from periodicpy.plugmgr.plugin import Module, ModuleArgument, ModuleCapabilities
from periodicpy.plugmgr.plugin.prop import ModuleProperty, ModulePropertyPermissions
from periodicpy.plugmgr.plugin.dtype import ModuleDataTypes
from periodicpy.plugmgr.plugin.method import ModuleMethod, ModuleMethodArgument
from periodicpy.irtools.lirc import LircClient

MODULE_VERSION = '0.1'

def module_version():
    return MODULE_VERSION

class LircdDriver(Module):
    _module_desc = ModuleArgument('lircd', 'lircd client driver')
    _capabilities = [ModuleCapabilities.MultiInstanceAllowed]
    _required_kw = [ModuleArgument('server_address', 'lircd server address'),
                    ModuleArgument('server_port', 'lircd server port')]
    _properties = {'version' : ModuleProperty(property_desc='Module Version',
                                              permissions=ModulePropertyPermissions.READ,
                                              getter=module_version,
                                              data_type=ModuleDataTypes.STRING),
                   'avail_remotes' : ModuleProperty(property_desc='Available Remotes',
                                                    permissions=ModulePropertyPermissions.READ,
                                                    data_type=ModuleDataTypes.STRING_LIST)}
    _methods = {'get_remote_actions' : ModuleMethod(method_desc='Retrieve available remote actions',
                                                    method_args={'remote_name' : ModuleMethodArgument(argument_desc='Remote name',
                                                                                                      required=True,
                                                                                                      data_type=ModuleDataTypes.STRING)},
                                                    method_return=ModuleDataTypes.STRING_LIST),
                'send_remote_key' : ModuleMethod(method_desc='Send a single remote control keypress',
                                                 method_args={'remote_name' : ModuleMethodArgument(argument_desc='Remote name',
                                                                                                   required=True,
                                                                                                   data_type=ModuleDataTypes.STRING),
                                                              'key_name' : ModuleMethodArgument(argument_desc='Key name',
                                                                                                required=True,
                                                                                                data_type=ModuleDataTypes.STRING)}),
                'start_key_press' : ModuleMethod(method_desc='Start sending repeated keypresses',
                                                 method_args={'remote_name' : ModuleMethodArgument(argument_desc='Remote name',
                                                                                                   required=True,
                                                                                                   data_type=ModuleDataTypes.STRING),
                                                              'key_name' : ModuleMethodArgument(argument_desc='Key name',
                                                                                                required=True,
                                                                                                data_type=ModuleDataTypes.STRING),
                                                              'repeat_count' : ModuleMethodArgument(argument_desc='Repeat count',
                                                                                                    required=False,
                                                                                                    data_type=ModuleDataTypes.INT)}),
                'stop_key_press' : ModuleMethod(method_desc='Stop sending repeated keypresses',
                                                 method_args={'remote_name' : ModuleMethodArgument(argument_desc='Remote name',
                                                                                                   required=True,
                                                                                                   data_type=ModuleDataTypes.STRING),
                                                              'key_name' : ModuleMethodArgument(argument_desc='Key name',
                                                                                                required=True,
                                                                                                data_type=ModuleDataTypes.STRING)})}

    def __init__(self, **kwargs):
        super(LircdDriver, self).__init__(**kwargs)

        #create lirc client instance
        self.lirc_handler = LircClient(self._loaded_kwargs['server_address'],
                                       self._loaded_kwargs['server_port'])

        #automap methods
        self._automap_methods()
        #automap properties
        self._automap_properties()

    def _get_avail_remotes(self):
        """Return available remotes at the location"""
        return self.lirc_handler.get_remote_list()

    def _get_remote_actions(self, remote_name):
        return self.lirc_handler.get_remote_key_list(remote_name)

    def _send_remote_key(self, remote_name, key_name):
        self.lirc_handler.send_key_once(remote_name, key_name)

    def _start_key_press(self, remote_name, key_name, repeat_count=0):
        self.lirc_handler.start_send_key(remote_name, key_name, repeat_count)

    def _stop_key_press(self, remote_name, key_name):
        self.lirc_handler.stop_send_key(remote_name, key_name)


def discover_module(*args):
    return LircdDriver

if __name__ == "__main__":

    #dump json file
    LircdDriver.dump_module_structure('lircd.json')
