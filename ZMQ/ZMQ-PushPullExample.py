# -*- coding: utf-8 -*-
"""
Created on Wed Aug 13 15:07:59 2025

@author: hallc
"""

#%% PUSH server that sends command to workers to continue working or exit.

import zmq
import time
import sys
import random
from  multiprocessing import Process

def server_push(port="5556"):
    context = zmq.Context()
    socket = context.socket(zmq.PUSH)
    socket.bind("tcp://*:%s" % port)
    print ("Running server on port: ", port)
    # serves only 5 request and dies
    for reqnum in range(10):
        if reqnum < 6:
            socket.send_string("Continue")
        else:
            socket.send_string("Exit")
            break
        time.sleep (1)
        
#%% Publisher that publishes for topics “8”,”9”,”10” in random order.
    
def server_pub(port="5558"):
    context = zmq.Context()
    socket = context.socket(zmq.PUB)
    socket.bind("tcp://*:%s" % port)
    publisher_id = random.randrange(0,9999)
    print ("Running server on port: ", port)
    # serves only 5 request and dies
    for reqnum in range(10):
        # Wait for next request from client
        topic = random.randrange(8,10)
        messagedata = "server#%s" % publisher_id
        print ("%s %s" % (topic, messagedata))
        socket.send_string("%d %s" % (topic, messagedata))
        time.sleep(1)    


#%% A worker that works on messages received for topic “9”. We setup zmq poller
# to poll for messages on the socket connection to both command server and publisher.

def client(port_push, port_sub):
    context = zmq.Context()
    socket_pull = context.socket(zmq.PULL)
    socket_pull.connect ("tcp://localhost:%s" % port_push)
    print ("Connected to server with port %s" % port_push)
    socket_sub = context.socket(zmq.SUB)
    socket_sub.connect ("tcp://localhost:%s" % port_sub)
    socket_sub.setsockopt_string(zmq.SUBSCRIBE, "9")
    print ("Connected to publisher with port %s" % port_sub)
    # Initialize poll set
    poller = zmq.Poller()
    poller.register(socket_pull, zmq.POLLIN)
    poller.register(socket_sub, zmq.POLLIN)

# We poll the sockets to check if we have messages to recv and work on it.
# Worker continues working until it receives exit condition.
    # Work on requests from both server and publisher
    should_continue = True
    while should_continue:
        socks = dict(poller.poll())
        if socket_pull in socks and socks[socket_pull] == zmq.POLLIN:
            message = socket_pull.recv()
            print ("Recieved control command: %s" % message)
            if message == "Exit": 
                print ("Recieved exit command, client will stop recieving messages")
                should_continue = False

        if socket_sub in socks and socks[socket_sub] == zmq.POLLIN:
            string = socket_sub.recv()
            topic, messagedata = string.split()
            print ("Processing ... ", topic, messagedata)
        
#%% Finally, we fire up all the processes.

if __name__ == "__main__":
    # Now we can run a few servers 
    server_push_port = "5556"
    server_pub_port = "5558"
    Process(target=server_push, args=(server_push_port,)).start()
    Process(target=server_pub, args=(server_pub_port,)).start()
    Process(target=client, args=(server_push_port,server_pub_port,)).start()