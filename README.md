# Mini Observer Network

####Painfully Simple Subscriber Publisher network.
Default encoding is JSON, optional encoding for raw bytes

###1. Start the server
use the -port #### -length # -encode (option) as arguments

1.-length # is the size of the header for length of the message

2.-encode (type) JSON or bytes

###2. Create Nodes in your code.
tnode = mobnet.Node(server_ip_str, port_number)
###3. Subscribe to topics
tnode.subscribe("generic topic name")
###4. Use the Nodes to read from topics and publish to them

##### publish to a topic
tnode.publish("generic topic name", "hello world")

##### check out many items are waiting to be read
tnode.status()

#### read the items
topic, info = tnode.read()

### set a callback function for a topic
tnode.callback("generic topic name", func_ptr, arg1, arg2... kwarg1, kwarg2...)

### At the moment

Only supported encoding are JSON and bytes.
The message length header is variable. 
These numbers and encodings must be consistent throughout the network.

### Q&A
The topics do not record history (Once a message is read it pops off the queue 
AND nodes don't get messages from before connection.)

The Nodes are anonymous (they don't have verified names)

Nodes will receive things they publish if they are subscribed to them.

There is no encryption (yet), It hurts being able to port mobnet to other languages. (but will be added as an option)

####the packets are easy to decode for other languages, mostly.

Every packet starts with N(4) digits that represent it's length. so a message cannot be over 10kb (by default)
The Packets are JSON or bytes after that.
The word SUBSCRIBE as a string is used for subscribing to topics by a node.

That's it folks

## Name server (optional utility)
I had a need for mobile and network config independent servers on a lan. To this end I decided on this extension.

1. Start up the name_server.py on a known reliable address
2. Start up your servers using the -name (server_name) and -ns (ip_for_name_server)
3. use host, port = mobnet.Nameservice.lookup(name)
4. connect your node to the host and port received
