from collections import namedtuple

#driver property
DriverProperty = namedtuple('DriverProperty', ['property_desc',
                                               'permissions',
                                               'getter',
                                               'setter',
                                               'data_type'])

#data types for completeness
class PPDataTypes:
    INT = 0
    FLOAT = 1
    STRING = 2
    VOID = 3
    INT_LIST = 4
    FLOAT_LIST = 5
    STRING_LIST = 6
    VOID_LIST = 7

class DriverPropertyPermissions(object):
    READ = 0
    WRITE = 1
    RW = 2
