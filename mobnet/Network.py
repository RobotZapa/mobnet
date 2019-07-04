import sys
import threading
import socket
import json

name_field = 3

class Node:
    def __init__(self, hostname, port=20001, encoding='JSON', length_field=4):
        self.host = hostname
        self.port = port
        self.queue = {}
        self.buffer_size = 1024
        self.encoding = encoding
        self.lenfield = length_field
        self.socket_name = None
        self.running = True

        self._setup()
        #           start the receiver thread
        receiver = threading.Thread(target=self._listener_thread)
        receiver.start()

    def _setup(self):
        for res in socket.getaddrinfo(self.host, self.port, socket.AF_UNSPEC, socket.SOCK_STREAM):
            af, socktype, proto, canonname, sa = res
            try:
                self.conn = socket.socket(af, socktype, proto)
            except OSError as msg:
                self.conn = None
                continue
            try:
                self.conn.connect(sa)
            except OSError as msg:
                self.conn.close()
                self.conn = None
                continue
            break
        if self.conn is None:
            print('could not open socket')
            sys.exit(1)
        self.socket_name = self.conn.getsockname()[0]

    def _send(self, topic, data):
        try:
            self.conn.sendall(pack(encode(topic, data, self.encoding), self.lenfield))
        except ConnectionError:
            self._setup()
            self.conn.sendall(pack(encode(topic, data, self.encoding), self.lenfield))

    def _listener_thread(self):
        unpacker = Unpacker()
        with self.conn:
            while self.running:
                socket_data = None
                try:
                    socket_data = unpacker.unpack(self.conn.recv(self.buffer_size), self.lenfield)
                except ConnectionError:
                    self._setup()
                if socket_data:
                    for data in socket_data:
                        self._receiver_handle(data)

    def _receiver_handle(self, data):
        topic, data = decode(data, self.encoding)
        self.queue[topic].append(data)

    def terminate(self):
        self.conn.close()
        self.working = False

    def subscribe(self, topic):
        '''
        All messages of topic will be added to the inbound queue
        :param topic:
        :return:
        '''
        self._send(topic, 'SUBSCRIBE')
        self.queue[topic] = []

    def publish(self, topic, content):
        '''
        publishes the content to the topic
        :param topic:
        :param content:
        :return:
        '''
        self._send(topic, content)

    def status(self, topic=None):
        '''
        :return: Returns the number of elements in the inbound queue
        '''
        if topic:
            return len(self.queue[topic])
        total = 0
        for topic in self.queue:
            total += len(self.queue[topic])
        return total

    def read(self, read_topic=None, **kwargs):
        '''
        collect one message from the inbound queue
        :param topic: if a topic is given it will collect from that topic only
        :return: topic, data
        '''
        if kwargs:
            if kwargs['newest']:
                if read_topic:
                    item = self.queue[read_topic][-1]
                    del self.queue[read_topic][-1]
                    return read_topic, item
                else:
                    for topic in self.queue:
                        if len(self.queue[topic]):
                            item = self.queue[topic][-1]
                            del self.queue[topic][-1]
                            return topic, item
            if kwargs['forget']:
                if read_topic:
                    self.queue[read_topic] = []
                else:
                    for topic in self.queue:
                        self.queue[topic] = []
        if read_topic:
            item = self.queue[read_topic][0]
            del self.queue[read_topic][0]
            return read_topic, item
        else:
            for topic in self.queue:
                if len(self.queue[topic]):
                    item = self.queue[topic][0]
                    del self.queue[topic][0]
                    return topic, item


def encode(topic, data, encoding='JSON'):
    if encoding == 'JSON':
        data = json.dumps(data)
        data = [topic, data]
        return str.encode(json.dumps(data))
    elif 'byte' in encoding.lower():
        if data == "SUBSCRIBE":
            data = data.encode()
        header = str(format(len(topic), "0"+str(name_field)+"d"))+topic
        return header.encode()+data


def decode(raw_data, encoding='JSON'):
    if encoding == 'JSON':
        topic, data = json.loads(raw_data.decode())
        data = json.loads(data)
    elif 'byte' in encoding.lower():
        data = raw_data
        try:
            size = int(data[0:name_field].decode())
        except ValueError:
            #print("Decode Error:", data)
            size = 6
        topic = data[name_field:size+name_field].decode()
        data = data[size+name_field:]
        #print("Error: packet was not readable by mobnet")
    return topic, data


def pack(raw_data, lenfield=4):
    '''
    Adds a lenfield digit length of the stream size.
    :param raw_data: the data to be encoded
    :param lenfield: the length of the size field
    :return:
    '''
    size = len(raw_data)
    encoded = format(size, '0'+str(lenfield)+'d').encode() + raw_data
    #print("pack data:", encoded)
    return encoded

class Unpacker:
    def __init__(self):
        self.incomplete = None
        self.size = 0

    def unpack(self, data, lenfield=4):
        '''
        Waits for the content of one entire message
        :param data: the data from recv
        :param lenfield: the length of the size field
        :return: message list, or [] is it's not a whole message yet
        try unpacking extra data if any
        '''
        if self.incomplete:
            data = self.incomplete+data
            self.incomplete = None
        else:
            self.size = 0
        chunk_list = []
        while data:
            if self.size == 0:
                self.size = int(data[0:lenfield].decode())
            if self.size > len(data) - lenfield:
                self.incomplete = data
                self.size = 0
                return chunk_list
            chunk_list.append(data[lenfield:lenfield+self.size])
            data = data[self.size+lenfield:]
            self.size = 0
        return chunk_list