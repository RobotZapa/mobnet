import time

try:
    from mobnet import Network as Network, Network
except ImportError:
    pass

# The port that name service uses.
port = 20803


def lookup(server_address, name):
    '''
    Finds the server host_address and port for a given name
    :param server_address: the address of the name_server.py
    :param name: the name of the server
    :return: host_addr, port
    '''
    net = Network.Node(server_address, port)
    net.subscribe('name')
    net.publish('name_get', name)
    while not net.status():
        time.sleep(.00001)
    _, obj = net.read()
    if obj['name'] == name:
        return obj['ip'], obj['port']
    net.terminate()
    return None, None

def locate_server():
    '''
    Scans all ip's on all network interfaces to locate the name_server.py
    :return: host_addr
    '''
    pass