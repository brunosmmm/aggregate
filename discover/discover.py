import dbus, gobject, avahi
from dbus import DBusException
from dbus.mainloop.glib import DBusGMainLoop
from util.thread import StoppableThread

def get_service_text_list(byte_array):
    if byte_array.signature != 'ay':
        return []

    text_list=[]
    for element in byte_array:
        #really stupid redundant check, but whatever
        if element.signature != 'y':
            continue

        text_list.append(''.join([chr(x) for x in element]))

    return text_list


class AvahiDiscoverLoop(StoppableThread):
    def __init__(self, service_resolved_cb=None, service_removed_cb=None, type_filter=None):
        super(AvahiDiscoverLoop, self).__init__()
        self.resolve_cb = service_resolved_cb
        self.remove_cb = service_removed_cb
        self.type_filter = type_filter
        self.main_loop = None

    def stop(self):
        super(AvahiDiscoverLoop, self).stop()
        print 'STOPPING'
        self.main_loop.quit()

    def run(self):

        def _item_resolved_cb(*args):
            if self.resolve_cb != None:
                #call everything as named arguments, discard DBus types!
                self.resolve_cb(name=str(args[2]),
                                host=str(args[5]),
                                address=str(args[7]),
                                port=int(args[8]),
                                text=get_service_text_list(args[9]))

        def _error_cb(*args):
            pass

        def _item_new_event(interface, protocol, name, stype, domain, flags):
            if flags & avahi.LOOKUP_RESULT_LOCAL:
                # local service, skip
                pass

            server.ResolveService(interface, protocol, name, stype,
                                  domain, avahi.PROTO_UNSPEC, dbus.UInt32(0),
                                  reply_handler=_item_resolved_cb,
                                  error_handler=_error_cb)

        loop = DBusGMainLoop()
        bus = dbus.SystemBus(mainloop=loop)
        server = dbus.Interface(bus.get_object(avahi.DBUS_NAME, '/'),
                                     'org.freedesktop.Avahi.Server')
        sbrowser = dbus.Interface(bus.get_object(avahi.DBUS_NAME,
                                                 server.ServiceBrowserNew(avahi.IF_UNSPEC,
                                                                          avahi.PROTO_UNSPEC,
                                                                          '_http._tcp',
                                                                          'local',
                                                                          dbus.UInt32(0))),
                                  avahi.DBUS_INTERFACE_SERVICE_BROWSER)
        sbrowser.connect_to_signal("ItemNew", _item_new_event)

        self.main_loop = gobject.MainLoop()

        #run main loop
        self.main_loop.run()

        #finish thread execution
        if self.is_stopped():
            exit(0)
