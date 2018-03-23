import dbus
from gi.repository import GObject as gobject
import avahi
from dbus.mainloop.glib import DBusGMainLoop
from util.thread import StoppableThread
import logging
import socket
import time
import re


def get_service_text_list(byte_array):
    """Convert DBUS text list to a python list
    """
    if byte_array.signature != 'ay':
        return []

    text_list = []
    for element in byte_array:
        # really stupid redundant check, but whatever
        if element.signature != 'y':
            continue

        text_list.append(''.join([chr(x) for x in element]))

    return text_list


class AvahiDiscoverLoop(StoppableThread):
    """Discovery loop with Avahi
    """
    def __init__(self, root_logger, service_resolved_cb=None,
                 service_removed_cb=None, type_filter=None):
        super(AvahiDiscoverLoop, self).__init__()
        self.resolve_cb = service_resolved_cb
        self.remove_cb = service_removed_cb
        self.main_loop = None

        self.type_filter = type_filter
        self.logger = logging.getLogger('{}.discoverLoop'.format(root_logger))

        # make sure that gobject is OK with threads
        gobject.threads_init()

    def stop(self):
        super(AvahiDiscoverLoop, self).stop()
        self.main_loop.quit()

    def run(self):
        def _item_resolved_cb(*args):
            if self.resolve_cb is not None:
                # call everything as named arguments,
                # discard DBus types!
                self.resolve_cb(iface=int(args[0]),
                                proto=int(args[1]),
                                kind=str(args[3]),
                                name=str(args[2]),
                                host=str(args[5]),
                                address=str(args[7]),
                                port=int(args[8]),
                                text=get_service_text_list(args[9]))

        def _error_cb(*args):
            self.logger.error('error resolving service: {}'.format(args))

        def _item_remove_event(interface, protocol,
                               name, stype, domain, flags):
            if flags & avahi.LOOKUP_RESULT_LOCAL:
                # local service, skip
                return

            if self.remove_cb is not None:
                self.remove_cb(iface=int(interface),
                               proto=int(protocol),
                               kind=str(stype),
                               name=str(name))

        def _item_new_event(interface, protocol, name, stype, domain, flags):
            server.ResolveService(interface, protocol, name, stype,
                                  domain, avahi.PROTO_UNSPEC, dbus.UInt32(0),
                                  reply_handler=_item_resolved_cb,
                                  error_handler=_error_cb)

        loop = DBusGMainLoop()
        bus = dbus.SystemBus(mainloop=loop)
        server = dbus.Interface(bus.get_object(avahi.DBUS_NAME, '/'),
                                'org.freedesktop.Avahi.Server')

        # register several kinds of service
        for service_type in self.type_filter:
            self.logger.debug('registering callbacks for service type "{}"'
                              .format(service_type))
            sbrowser = dbus.Interface(bus.get_object(avahi.DBUS_NAME,
                                                     server.ServiceBrowserNew(avahi.IF_UNSPEC,
                                                                              avahi.PROTO_UNSPEC,
                                                                              service_type,
                                                                              'local',
                                                                              dbus.UInt32(0))),
                                      avahi.DBUS_INTERFACE_SERVICE_BROWSER)

            # connect new item signal
            sbrowser.connect_to_signal("ItemNew", _item_new_event)
            # connect item remove signal
            sbrowser.connect_to_signal("ItemRemove", _item_remove_event)

        self.main_loop = gobject.MainLoop()

        # run main loop
        self.main_loop.run()

        # finish thread execution
        if self.is_stopped():
            exit(0)


class SimpleSSDPDiscovery(StoppableThread):
    """Discovery using SSDP
    """
    def __init__(self, root_logger, interval, removal_interval,
                 service_discovered_cb=None, service_removed_cb=None):
        super(SimpleSSDPDiscovery, self).__init__()
        self.logger = logging.getLogger('{}.ssdp'.format(root_logger))
        self.intval = interval
        self.rem_intval_units = removal_interval
        self.queries = {}

        # callbacks
        self.discover_cb = service_discovered_cb
        self.remove_cb = service_removed_cb

        # keep a dictionary of known services and generate events from that
        self.known_services = {}

    def add_discovery_type(self, host_addr, host_port, service_type):
        self.queries[service_type] = [host_addr, host_port]

    def remove_discovery_type(self, service_type):
        if service_type in self.queries:
            del self.queries[service_type]

    def _parse_ssdp_return(self, data, search_all=False):
        # remove blank line at the end!
        lines = data.split('\n')[:-2]

        # check response
        m = re.match(r'^HTTP/([0-9\.]+) ([0-9]+) (.*)', lines[0])
        if m is None:
            # garbage
            return None

        # build a dictionary with the data retrieved
        ret_val = {}
        for line in lines[1::]:
            m = re.match(r'([a-zA-Z_\-]+):\s*(.*)$', line)
            ret_val[m.group(1).upper()] = m.group(2).strip()

        return ret_val

    def run(self):

        while True:

            if self.is_stopped():
                exit(0)

            for st, addr in self.queries.iteritems():
                ssdpRequest = "M-SEARCH * HTTP/1.1\r\n" + \
                              "HOST: {}:{}\r\n".format(*addr) + \
                              "MAN: \"ssdp:discover\"\r\n" + \
                              "MX: 3\r\n" + \
                              "ST: {}\r\n".format(st) + "\r\n"

                sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                sock.settimeout(3)
                sock.sendto(ssdpRequest, tuple(addr))
                try:
                    status = sock.recv(1000)
                    service = self._parse_ssdp_return(status,
                                                      (st == 'ssdp:all'))
                    if service['USN'] in self.known_services:
                        # already accounted for, but update last seen
                        a_service = self.known_services[service['USN']]
                        a_service['last_seen'] = time.time()
                        continue

                    # else
                    if self.discover_cb:
                        # put last seen in
                        service['last_seen'] = time.time()
                        self.known_services[service['USN']] = service
                        self.discover_cb(**service)

                except socket.timeout:
                    # not found!
                    #print 'NOT FOUND: {}'.format(st)
                    pass

            # remove services not seen in a while
            services_to_remove = []
            for usn, service in self.known_services.iteritems():
                if time.time() - service['last_seen'] > self.intval*self.rem_intval_units:
                    # remove
                    if self.remove_cb:
                        self.remove_cb(**service)
                        services_to_remove.append(usn)

            for usn in services_to_remove:
                del self.known_services[usn]

            time.sleep(self.intval)
