from node.service.driver import NodeServiceDriver, NodeServiceDriverArgument, DriverCapabilities

class SnapClientDriver(NodeServiceDriver):
    """SnapCast client dummy driver only for display purposes"""
    _module_desc = NodeServiceDriverArgument('snapclient',
                                             'SnapCast client dummy driver')
    _capabilities = [DriverCapabilities.MultiInstanceAllowed]

    def __init__(self, **kwargs):
        super(SnapClientDriver, self).__init__(**kwargs)

        #don't do anything!

def discover_module():
    return SnapClientDriver
