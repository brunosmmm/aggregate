import pyjsonrpc
from util.thread import StoppableThread
import BaseHTTPServer

def make_json_server(drv_manager, node_list):
    class PeriodicPiAggJsonServer(pyjsonrpc.HttpRequestHandler):

        #set references
        drvman = drv_manager
        nodelist = node_list

        @pyjsonrpc.rpcmethod
        def list_nodes(self, simple=True):
            #build serializable node dictionary and return
            ret = {}
            for node_name, node in self.nodelist.iteritems():
                ret[node_name] = node.get_serializable_dict(simple)

            return ret

        @pyjsonrpc.rpcmethod
        def list_drivers(self):
            return self.drvman.list_loaded_modules()

        @pyjsonrpc.rpcmethod
        def module_info(self, module_name):
            return self.drvman.get_module_info(module_name)

        @pyjsonrpc.rpcmethod
        def module_get_property(self, module_name, property_name):
            return self.drvman.get_module_property(module_name, property_name)

        @pyjsonrpc.rpcmethod
        def module_get_property_list(self, module_name):
            return self.drvman.get_module_property_list(module_name)

    return PeriodicPiAggJsonServer

class PeriodicPiAggController(StoppableThread):
    def __init__(self, drv_manager, node_list):
        super(PeriodicPiAggController, self).__init__()
        self.drv_manager = drv_manager
        self.node_list = node_list
        self.http_server = None

    def stop(self):
        super(PeriodicPiAggController, self).stop()
        self.http_server.shutdown()

    def run(self):

        #generate class with references
        json_server_class = make_json_server(self.drv_manager, self.node_list)
        self.http_server = pyjsonrpc.ThreadingHttpServer(server_address=('localhost', 8080),
                                                         RequestHandlerClass=json_server_class)

        self.http_server.serve_forever()
