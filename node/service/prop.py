from node.service.dtype import PPDataTypes

class DriverPropertyPermissions(object):
    READ = 0
    WRITE = 1
    RW = 2

#driver property
class DriverProperty(object):
    def __init__(self,
                 property_desc,
                 permissions=DriverPropertyPermissions.RW,
                 getter=None,
                 setter=None,
                 data_type=PPDataTypes.VOID,
                 **kwargs):

        self.property_desc = property_desc
        self.permissions = permissions
        self.getter = getter
        self.setter = setter
        self.data_type = data_type

        #hacky hack
        self.__dict__.update(kwargs)
