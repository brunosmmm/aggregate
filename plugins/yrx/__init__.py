from periodicpy.plugmgr.plugin import Module, ModuleArgument, ModuleCapabilities
from periodicpy.plugmgr.plugin.prop import ModuleProperty, ModulePropertyPermissions
from periodicpy.plugmgr.plugin.dtype import ModuleDataTypes
from periodicpy.plugmgr.exception import HookNotAvailableError
from periodicpy.plugmgr import ModuleManagerHookActions
import re
import rxv

YAMAHARX_REGEX = re.compile(r'^RX-A1020 ([0-9]+)')

_ACTIVE_RECEIVER_LIST = []

class YRXNodeDriverLoadError(Exception):
    pass

class YRXNodeDriver(Module):
    _module_desc = ModuleArgument('yrx', 'Yamaha RX receiver driver')
    _capabilities = [ModuleCapabilities.MultiInstanceAllowed]
    _required_kw = [ModuleArgument('address', 'node address'),
                    ModuleArgument('port', 'node port'),
                    ModuleArgument('name', 'node advertised name')]


    def __init__(self, **kwargs):
        super(YRXNodeDriver, self).__init__(**kwargs)

        m = YAMAHARX_REGEX.match(kwargs['name'])
        self.identifier = m.group(1)

        if self.identifier in _ACTIVE_RECEIVER_LIST:
            raise YRXNodeDriverLoadError('receiver with id "{}" is already active, not loading'.format(self.identifier))

        self.interrupt_handler(log_info='new RX-A1020 receiver with id: {}'.format(self.identifier))

        #attach node_removed hook
        self.interrupt_handler(attach_custom_hook=['ppagg.node_removed',
                                                   [self._node_removed,
                                                    ModuleManagerHookActions.UNLOAD_MODULE,
                                                    self._registered_id]])

        self.rx = rxv.RXV('http://{}:{}/YamahaRemoteControl/ctrl'.format(kwargs['address'],
                                                                         kwargs['port']), 'RX-A1020')

        self._automap_properties()
        self._automap_methods()

        _ACTIVE_RECEIVER_LIST.append(self.identifier)

    def module_unload(self):
        pass

    def _node_removed(self, **kwargs):
        #see if we were removed!
        m = YAMAHARX_REGEX.match(kwargs['name'])

        if m == None:
            return False

        if self.identifier == m.group(1) and kwargs['address'] == self._loaded_kwargs['address']:
            _ACTIVE_RECEIVER_LIST.remove(m.group(1))
            return True

    @classmethod
    def new_node_detected(cls, **kwargs):

        m = YAMAHARX_REGEX.match(kwargs['name'])
        if m == None:
            return False

        return True

    def _get_volume(self):
        return self.rx.volume

    def _set_volume(self, value):
        try:
            self.rx.volume = value
        except Exception:
            self.interrupt_handler(log_warning='Invalid volume value received: "{}"'.format(value))

    def _get_volume2(self):
        return self.rx.volume2

    def _set_volume2(self, value):
        try:
            self.rx.volume2 = value
        except Exception:
            self.interrupt_handler(log_warning='Invalid volume value received: "{}"'.format(value))
            return False

    def _get_main_on(self):
        return self.rx.main_on

    def _get_zone_on(self):
        return self.rx.zone_on

    def _set_main_on(self, state):
        self.rx.main_on = state

    def _set_zone_on(self, state):
        self.rx.zone_on = state

    def _get_zone_input(self):
        return self.rx.zone_input

    def _get_main_input(self):
        return self.rx.main_input

def discover_module(**kwargs):
    class YRXNodeDriverProxy(YRXNodeDriver):
        _, _properties, _methods = Module.build_module_structure_from_file(kwargs['plugin_path']+'yrx.json')

    try:
        kwargs['modman'].attach_custom_hook('ppagg.node_discovered',
                                            YRXNodeDriver.new_node_detected,
                                            ModuleManagerHookActions.LOAD_MODULE,
                                            YRXNodeDriver)
    except HookNotAvailableError:
        raise

    return YRXNodeDriverProxy