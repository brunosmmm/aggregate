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

    def _send_remote_key(self, remote_name, key_name, repeat_count=0):
        self.lirc_handler.send_key_once(remote_name, key_name, repeat_count)

    def _start_key_press(self, remote_name, key_name):
        self.lirc_handler.start_send_key(remote_name, key_name)

    def _stop_key_press(self, remote_name, key_name):
        self.lirc_handler.stop_send_key(remote_name, key_name)


def discover_module(**kwargs):
    #load methods and properties from file
    class LircdDriverProxy(LircdDriver):
        _, _properties, _methods = Module.build_module_structure_from_file(kwargs['plugin_path']+'lircd.json')

    return LircdDriverProxy
