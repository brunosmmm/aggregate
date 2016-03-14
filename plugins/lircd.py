from node.service.driver import NodeServiceDriver, NodeServiceDriverArgument, DriverCapabilities
from node.service.prop import DriverProperty, DriverPropertyPermissions, PPDataTypes
from periodicpy.irtools.lirc import LircClient

class LircdDriver(NodeServiceDriver):
    _module_desc = NodeServiceDriverArgument('lircd', 'lircd client driver')
    _capabilities = [DriverCapabilities.MultiInstanceAllowed]
    _required_kw = [NodeServiceDriverArgument('server_address', 'lircd server address'),
                    NodeServiceDriverArgument('server_port', 'lircd server port')]

    def __init__(self, **kwargs):
        super(LircdDriver, self).__init__(**kwargs)

        #create lirc client instance
        self.lirc_handler = LircClient(self._loaded_kwargs['server_address'],
                                       self._loaded_kwargs['server_port'])

        #build property list
        self._register_properties()

    def _get_available_remotes(self):
        """Return available remotes at the location"""
        return self.lirc_handler.get_remote_list()

    def _register_properties(self):
        self._properties = {'avail_remotes' : DriverProperty(property_desc='Available Remotes',
                                                             permissions=DriverPropertyPermissions.READ,
                                                             getter=self._get_available_remotes,
                                                             setter=None,
                                                             data_type=PPDataTypes.STRING_LIST)}


def discover_module():
    return LircdDriver
