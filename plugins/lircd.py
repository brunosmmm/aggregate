from node.service.driver import NodeServiceDriver, NodeServiceDriverArgument, DriverCapabilities
from periodicpy.irtools.lirc import LircClient

class LircdDriver(NodeServiceDriver):
    _module_desc = NodeServiceDriverArgument('lircd', 'lircd client driver')
    _capabilities = [DriverCapabilities.MultiInstanceAllowed]
    _required_kw = [NodeServiceDriverArgument('server_address', 'lircd server address'),
                    NodeServiceDriverArgument('server_port', 'lircd server port')]

    def __init__(self, **kwargs):
        super(LircdDriver, self).__init__(**kwargs)

        self.lirc_handler = LircClient(self._loaded_kwargs['server_address'],
                                       self._loaded_kwargs['server_port'])

def discover_module():
    return LircdDriver
