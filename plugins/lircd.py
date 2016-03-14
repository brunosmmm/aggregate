from node.service.driver import NodeServiceDriver, NodeServiceDriverArgument, DriverCapabilities

class LircdDriver(NodeServiceDriver):
    _module_desc = NodeServiceDriverArgument('lircd', 'lircd client driver')
    _capabilities = [DriverCapabilities.MultiInstanceAllowed]

    def __init__(self, **kwargs):
        super(LircdDriver, self).__init__()

def discover_module():
    return LircdDriver
