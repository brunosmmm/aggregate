from node.service.driver import NodeServiceDriver, NodeServiceDriverArgument, DriverCapabilities
from node.service.prop import DriverProperty, DriverPropertyPermissions
from node.service.dtype import PPDataTypes
from node.service.method import DriverMethod, DriverMethodArgument
from periodicpy.irtools.lirc import LircClient

MODULE_VERSION = '0.1'

def module_version():
    return MODULE_VERSION

class LircdDriver(NodeServiceDriver):
    _module_desc = NodeServiceDriverArgument('lircd', 'lircd client driver')
    _capabilities = [DriverCapabilities.MultiInstanceAllowed]
    _required_kw = [NodeServiceDriverArgument('server_address', 'lircd server address'),
                    NodeServiceDriverArgument('server_port', 'lircd server port')]
    _properties = {'version' : DriverProperty(property_desc='Module Version',
                                              permissions=DriverPropertyPermissions.READ,
                                              getter=module_version,
                                              data_type=PPDataTypes.STRING),
                   'avail_remotes' : DriverProperty(property_desc='Available Remotes',
                                                    permissions=DriverPropertyPermissions.READ,
                                                    data_type=PPDataTypes.STRING_LIST)}
    _methods = {'get_remote_actions' : DriverMethod(method_desc='Retrieve available remote actions',
                                                    method_args={'remote_name' : DriverMethodArgument(argument_desc='Remote name',
                                                                                                      required=True,
                                                                                                      data_type=PPDataTypes.STRING)},
                                                    method_return=PPDataTypes.STRING_LIST)

    )}

    def __init__(self, **kwargs):
        super(LircdDriver, self).__init__(**kwargs)

        #create lirc client instance
        self.lirc_handler = LircClient(self._loaded_kwargs['server_address'],
                                       self._loaded_kwargs['server_port'])

        #build property list
        self._register_properties()
        #build method list
        self._register_methods()

    def _get_available_remotes(self):
        """Return available remotes at the location"""
        return self.lirc_handler.get_remote_list()

    def _get_remote_actions(self, remote_name):
        return self.lirc_handler.get_remote_key_list(remote_name)

    def _register_properties(self):
        self._properties['avail_remotes'].getter = self._get_available_remotes

    def _register_methods(self):
        self._methods['get_remote_actions'].method_call = self._get_remote_actions

def discover_module(*args):
    return LircdDriver
