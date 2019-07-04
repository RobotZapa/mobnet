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
    ip = None

    def __init__(self):
        self.transport = None

    def connection_made(self, transport):
        print('=====================')
        print('Node has connected.')
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
        print(f"Node removed.")

    def data_received(self, data):
        # print('RAW DATA', data)
        socket_data = self.unpacker.unpack(data, self.length_header)
        # print('SOCKET DATA', socket_data)
        if socket_data:
            for data in socket_data:
                self.process_data(data)

    def process_data(self, msg):
        topic, data = Network.decode(msg, self.encoding)

        if data == 'SUBSCRIBE' or self.encoding == 'bytes' and data == b'SUBSCRIBE':
            if topic not in self.topics:
                self.topics[topic] = []
            self.topics[topic].append(self)
            if self.verbose:
                print(f"A node has subscribed to {topic}")

        else:
            if topic in self.topics:
                for sub in self.topics[topic]:
                    sub.send(topic, data)
                if self.verbose:
                    print(f"A message has been published to {topic}")
            else:
                if self.verbose:
                    print(f"A message has been published to {topic} but no one is subscribed")

    def eof_received(self):
        pass


def start_server(loop, host, port, encoding, length, server_name, name_server):
    mobnet_server.encoding = encoding
    mobnet_server.length_header = length
    f = loop.create_server(mobnet_server, host, port)
    if name_server and server_name:
        ns = Network.Node(name_server, Nameservice.port)
        ns.publish('name_set', {'name': server_name, 'ip': ns.socket_name, 'port': port})
    return loop.run_until_complete(f)

ARGS = argparse.ArgumentParser(description='mobnet server.')
ARGS.add_argument(
    '-host', action='store', dest='host',
    default = '0.0.0.0', help='Host name')
ARGS.add_argument(
    '-port', action='store', dest='port',
    default=20801, type=int, help='Port number')
ARGS.add_argument(
    '-iocp', action='store_true', dest='iocp',
    default=False, help='Use IOCP event loop')
ARGS.add_argument(
    '-length', action='store', dest='length',
    default=4, type=int, help='Size of the length field')
ARGS.add_argument(
    '-encode', action='store', dest='encode',
    default='JSON', help='The encoding to be used')
ARGS.add_argument(
    '-name', action='store', dest='servername',
    default=None, help='The name for name_server.py to tell others')
ARGS.add_argument(
    '-ns', action='store', dest='nameserver',
    default=None, help='The name_server.py address.')

if __name__ == '__main__':
    args = ARGS.parse_args()

    if ':' in args.host:
        args.host, port = args.host.split(':', 1)
        args.port = int(port)

    if args.iocp:
        from asyncio import windows_events
        loop = windows_events.ProactorEventLoop()
        asyncio.set_event_loop(loop)
    else:
        loop = asyncio.get_event_loop()
    print(f'Using backend: {loop.__class__.__name__}')

    if signal is not None and sys.platform != 'win32':
        loop.add_signal_handler(signal.SIGINT, loop.stop)

    server = start_server(loop, args.host, args.port, args.encode, args.length, args.servername, args.nameserver)

    print(f'Starting mobnet server on {args.host} port {args.port} with '
          f'{args.encode} and header length field {args.length}')

    try:
        loop.run_forever()
    finally:
        server.close()
        loop.close()
