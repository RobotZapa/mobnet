#!/usr/bin/env python3
import sys
import argparse
import asyncio
import Network
import Nameservice

try:
    import signal
except ImportError:
    signal = None


class mobnet_server(asyncio.Protocol):

    length_header = 4
    encoding = 'JSON'
    clients = []
    topics = {}
    verbose = False
    name_list = []

    def __init__(self):
        self.transport = None

    def connection_made(self, transport):
        print('=====================')
        print('Client has connected.')
        self.transport = transport
        self.clients.append(self)

        #Define the send and unpack fuction
        self.unpacker = Network.Unpacker()
        self.send = lambda topic, data: self.transport.write(Network.pack(Network.encode(topic, data, self.encoding),
                                                                          self.length_header))

    def connection_lost(self, exc):
        print('---------------------')

        #remove self from clients
        self.clients.remove(self)

        #remove self from all topics
        for topic in self.topics:
            if self in self.topics[topic]:
                self.topics[topic].remove(self)
        print(f"client removed.")

    def data_received(self, data):
        # print('RAW DATA', data)
        socket_data = self.unpacker.unpack(data, self.length_header)
        # print('SOCKET DATA', socket_data)
        if socket_data:
            for data in socket_data:
                self.process_data(data)

    def process_data(self, msg):
        topic, data = Network.decode(msg, self.encoding)

        if topic == 'name_get':
            for obj in self.name_list:
                if obj['name'] == data:
                    self.send('name', obj)
        if topic == 'name_set':
            self.name_list.append(data)
            print(f"new server named {data['name']} has registered")

    def eof_received(self):
        pass


ARGS = argparse.ArgumentParser(description='mobnet name server.')

ARGS.add_argument(
    '-iocp', action='store_true', dest='iocp',
    default=False, help='Use IOCP event loop')

def start_server(loop, host, port, encoding, length):
    mobnet_server.encoding = encoding
    mobnet_server.length_header = length
    f = loop.create_server(mobnet_server, host, port)
    return loop.run_until_complete(f)

if __name__ == '__main__':
    args = ARGS.parse_args()

    if args.iocp:
        from asyncio import windows_events
        loop = windows_events.ProactorEventLoop()
        asyncio.set_event_loop(loop)
    else:
        loop = asyncio.get_event_loop()
    print(f'Using backend: {loop.__class__.__name__}')

    if signal is not None and sys.platform != 'win32':
        loop.add_signal_handler(signal.SIGINT, loop.stop)

    server = start_server(loop, '0.0.0.0', Nameservice.port, 'JSON', 4)

    print(f'Starting name server on port {Nameservice.port}')

    try:
        loop.run_forever()
    finally:
        server.close()
        loop.close()