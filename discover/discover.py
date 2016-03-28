import dbus, gobject, avahi
from dbus import DBusException
from dbus.mainloop.glib import DBusGMainLoop
from util.thread import StoppableThread
import signal

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
        self.main_loop = None

        if type_filter == None:
            self.type_filter = ['_http._tcp']
        else:
            self.type_filter = type_filter

        #make sure that gobject is OK with threads
        gobject.threads_init()

    def stop(self):
        super(AvahiDiscoverLoop, self).stop()
        self.main_loop.quit()

    def run(self):

        def _item_resolved_cb(*args):
            if self.resolve_cb != None:
                #call everything as named arguments, discard DBus types!
                self.resolve_cb(iface=int(args[0]),
                                proto=int(args[1]),
                                kind=str(args[3]),
                                name=str(args[2]),
                                host=str(args[5]),
                                address=str(args[7]),
                                port=int(args[8]),
                                text=get_service_text_list(args[9]))

        def _error_cb(*args):
            print 'ERROR: {}'.format(args)

        def _item_remove_event(interface, protocol, name, stype, domain, flags):
            if flags & avahi.LOOKUP_RESULT_LOCAL:
                # local service, skip
                return

            if self.remove_cb != None:
                self.remove_cb(iface=int(interface),
                               proto=int(protocol),
                               kind=str(stype),
                               name=str(name))

        def _item_new_event(interface, protocol, name, stype, domain, flags):
            if flags & avahi.LOOKUP_RESULT_LOCAL:
                # local service, skip
                return

            server.ResolveService(interface, protocol, name, stype,
                                  domain, avahi.PROTO_UNSPEC, dbus.UInt32(0),
                                  reply_handler=_item_resolved_cb,
                                  error_handler=_error_cb)

        loop = DBusGMainLoop()
        bus = dbus.SystemBus(mainloop=loop)
        server = dbus.Interface(bus.get_object(avahi.DBUS_NAME, '/'),
                                     'org.freedesktop.Avahi.Server')

        #register several kinds of service
        for service_type in self.type_filter:
            sbrowser = dbus.Interface(bus.get_object(avahi.DBUS_NAME,
                                                     server.ServiceBrowserNew(avahi.IF_UNSPEC,
                                                                              avahi.PROTO_UNSPEC,
                                                                              service_type,
                                                                              'local',
                                                                              dbus.UInt32(0))),
                                      avahi.DBUS_INTERFACE_SERVICE_BROWSER)

            #connect new item signal
            sbrowser.connect_to_signal("ItemNew", _item_new_event)
            #connect item remove signal
            sbrowser.connect_to_signal("ItemRemove", _item_remove_event)

        self.main_loop = gobject.MainLoop()

        #run main loop
        self.main_loop.run()

        #finish thread execution
        if self.is_stopped():
            exit(0)
