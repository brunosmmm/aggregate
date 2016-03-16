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
                                                    method_return=PPDataTypes.STRING_LIST),
                'send_remote_key' : DriverMethod(method_desc='Send a single remote control keypress',
                                                 method_args={'remote_name' : DriverMethodArgument(argument_desc='Remote name',
                                                                                                   required=True,
                                                                                                   data_type=PPDataTypes.STRING),
                                                              'key_name' : DriverMethodArgument(argument_desc='Key name',
                                                                                                required=True,
                                                                                                data_type=PPDataTypes.STRING)}),
                'start_key_press' : DriverMethod(method_desc='Start sending repeated keypresses',
                                                 method_args={'remote_name' : DriverMethodArgument(argument_desc='Remote name',
                                                                                                   required=True,
                                                                                                   data_type=PPDataTypes.STRING),
                                                              'key_name' : DriverMethodArgument(argument_desc='Key name',
                                                                                                required=True,
                                                                                                data_type=PPDataTypes.STRING),
                                                              'repeat_count' : DriverMethodArgument(argument_desc='Repeat count',
                                                                                                    required=False,
                                                                                                    data_type=PPDataTypes.INT)}),
                'stop_key_press' : DriverMethod(method_desc='Stop sending repeated keypresses',
                                                 method_args={'remote_name' : DriverMethodArgument(argument_desc='Remote name',
                                                                                                   required=True,
                                                                                                   data_type=PPDataTypes.STRING),
                                                              'key_name' : DriverMethodArgument(argument_desc='Key name',
                                                                                                required=True,
                                                                                                data_type=PPDataTypes.STRING)})}

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
