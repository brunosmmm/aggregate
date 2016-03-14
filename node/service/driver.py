from collections import namedtuple
from node.service.exception import ModuleLoadError, ModuleNotLoadedError

#simple description for arguments
NodeServiceDriverArgument = namedtuple('NodeServiceDriverArgument', ['arg_name', 'arg_help'])

class DriverCapabilities(object):
    MultiInstanceAllowed = 0

class NodeServiceDriver(object):
    _required_kw = []
    _optional_kw = []
    _module_desc = NodeServiceDriverArgument(None, None)
    _capabilities = []
    _registered_id = None
    _mod_handler = None

    def __init__(self, module_id, handler, **kwargs):
        self._check_kwargs(**kwargs)

        #save loaded kwargs
        self._loaded_kwargs = dict(kwargs)

        #register module
        self.module_register(module_id, handler)

    @classmethod
    def get_capabilities(cls):
        return cls._capabilities

    @classmethod
    def get_module_desc(cls):
        """get module description"""
        return cls._module_desc

    @classmethod
    def get_required_kwargs(cls):
        """return a list of required arguments to spawn module"""
        return cls._required_kw

    @classmethod
    def get_optional_kwargs(cls):
        """return a list of optional arguments"""
        return cls._optional_kw

    @classmethod
    def _check_kwargs(cls, **kwargs):
        """verify if required kwargs are met"""
        for kwg in cls._required_kw:
            if kwg.arg_name not in kwargs:
                raise ModuleLoadError('missing argument: {}'.format(kwg.arg_name), cls._module_desc.arg_name)

    def module_unload(self):
        """Unload module procedure (module-specific)"""
        pass

    def module_register(self, module_id, handler):
        """Register module procedure"""
        self._registered_id = module_id
        self._mod_handler = handler

    def handler_communicate(self, **kwargs):
        """Handle communication from manager (module-specific)"""
        pass

    def interrupt_handler(self, **kwargs):
        """Get attention of handler"""
        if self._mod_handler == None or self._registered_id == None:
            raise ModuleNotLoadedError('module is not registered')

        self._mod_handler(self._registered_id, **kwargs)

    def log_info(self, message):
        self.interrupt_handler(log_info=message)

    def log_warning(self, message):
        self.interrupt_handler(log_warning=message)

    def log_error(self, message):
        self.interrupt_handler(log_error=message)
