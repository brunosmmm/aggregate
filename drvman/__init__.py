""" Driver manager (inherited from Jux)
  @file drvman/__init__.py
  @author Bruno Morais <brunosmmm@gmail.com>
"""

import importlib
import logging
from node.service.driver import NodeServiceDriver, NodeServiceDriverArgument, DriverCapabilities
from node.service.exception import ModuleLoadError, ModuleAlreadyLoadedError, ModuleNotLoadedError
#from jux.module.mixin.control import JMControlMixin
#from jux.module.mixin.library import JMLibraryMixin
#from jux.module.mixin.asource import JMAudioSourceMixin
#from jux.mmanager.exception import NoLibraryError
import re

MODULE_HANDLER_LOGGING_KWARGS = ['log_info', 'log_warning', 'log_error']

#helper functions
def handle_multiple_instance(module_name, loaded_module_list):

    instance_list = []
    for module in loaded_module_list:
        m = re.match(r"{}-([0-9]+)".format(module_name), module)
        if m != None:
            instance_list.append(int(m.group(1)))

    if len(instance_list) == 0:
        return 1

    return sorted(instance_list)[-1] + 1

class DriverManager(object):
    """Module manager class"""
    def __init__(self, central_log):

        self.found_modules = {}
        self.loaded_modules = {}
        self.logger = logging.getLogger('{}.drvman'.format(central_log))

        #discover modules
        self.discover_modules()

    def discover_modules(self):

        module_root = importlib.import_module('plugins')
        module_list = module_root.MODULES

        for module in module_list:

            #ignore root
            if module == '__init__':
                continue

            try:
                the_mod = importlib.import_module('plugins.{}'.format(module))
                module_class = the_mod.discover_module()
                self.found_modules[module_class.get_module_desc().arg_name] = module_class
                self.logger.info('Discovered module "{}"'.format(module_class.get_module_desc().arg_name))
            except ImportError as error:
                self.logger.warning('could not register python module: {}'.format(error.message))
            except Exception as error:
                #catch anything else because this cannot break the application
                self.logger.warning('could not register module {}: {}'.format(module,error.message))

    def load_module(self, module_name, **kwargs):
        """Load a module that has been previously discovered"""
        if module_name not in self.found_modules:
            raise ModuleLoadError('invalid module name')

        if module_name in self.loaded_modules:
            if DriverCapabilities.MultiInstanceAllowed not in self.found_modules[module_name].get_capabilities():
                raise ModuleAlreadyLoadedError('module is already loaded')

            #handle multiple instances
            multi_inst_name = module_name + '-{}'.format(handle_multiple_instance(module_name,
                                                                                  self.loaded_modules.keys()))
            self.loaded_modules[multi_inst_name] = self.found_modules[module_name](module_id=multi_inst_name,
                                                                                   handler=self.module_handler,
                                                                                   **kwargs)
            self.logger.info('Loaded module "{}" as "{}"'.format(module_name, multi_inst_name))
            return

        #load (create object)
        self.loaded_modules[module_name] = self.found_modules[module_name](module_id=module_name,
                                                                           handler=self.module_handler,
                                                                           **kwargs)

        self.logger.info('Loaded module "{}"'.format(module_name))

    def unload_module(self, module_name):

        if module_name not in self.loaded_modules:
            raise ModuleNotLoadedError('cant unload {}: module not loaded'.format(module_name))

        #do unloading procedure
        self.loaded_modules[module_name].unload_module()

        #remove
        del self.loaded_modules[module_name]

    def list_discovered_modules(self):
        return [x.get_module_desc() for x in self.found_modules.values()]

    def module_handler(self, which_module, **kwargs):

        for kwg, value in kwargs.iteritems():
            if kwg in MODULE_HANDLER_LOGGING_KWARGS:
                #dispatch logger
                self._log_module_message(which_module, kwg, value)

    def _log_module_message(self, module, level, message):

        if level == 'log_info':
            self.logger.info("{}: {}".format(module, message))
        elif level == 'log_warning':
            self.logger.warning("{}: {}".format(module, message))
        elif level == 'log_error':
            self.logger.error("{}: {}".format(module, message))

    #def analyze_module(self, module_name):
    #
    #    if module_name not in self.loaded_modules:
    #        raise ModuleNotLoadedError('module {} is not loaded'.format(module_name))
    #
    #    if isinstance(self.loaded_modules[module_name], JMLibraryMixin):
    #        print 'has library -> counts:'
    #        print self.loaded_modules[module_name].get_element_count()
    #    if isinstance(self.loaded_modules[module_name], JMControlMixin):
    #        print 'has control'
    #    if isinstance(self.loaded_modules[module_name], JMAudioSourceMixin):
    #        print 'has audio source'

    def search_module_library(self, module_name, **kwargs):
        pass

        # if module_name not in self.loaded_modules:
        #     raise ModuleNotLoadedError('module {} is not loaded'.format(module_name))

        # if not isinstance(self.loaded_modules[module_name], JMLibraryMixin):
        #     raise NoLibraryError('module {} doesnt have library attributes'.format(module_name))

        # return self.loaded_modules[module_name].search_element(**kwargs)
