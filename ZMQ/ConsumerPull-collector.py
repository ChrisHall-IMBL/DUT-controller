# -*- coding: utf-8 -*-
"""
Created on Wed Aug 13 15:35:20 2025

@author: hallc
"""

import time
import sys
import signal
import zmq
import random
# import pprint
from  multiprocessing import Process, Pipe

# Shut down gracefully on receiving ^c interupt
def signal_handler(sig, frame):
    print('Stopping consumer')
    # shutdown()
    sys.exit(0)
signal.signal(signal.SIGINT, signal_handler)

def consumer(conn):
    # 'conn' is this end of the pipe back to parent process
    consumer_id = random.randrange(1,10005)
    conn.send("I am consumer #%s" % (consumer_id))
    # Set up ZMQ socket to pull from the other application
    context = zmq.Context()
    # recieve work
    consumer_receiver = context.socket(zmq.PULL)
    consumer_receiver.connect("tcp://127.0.0.1:5557")
    # Python dictionaries can be sent as json messages:
    carryOn=True
    while carryOn:
        work = consumer_receiver.recv_json() # Get the work order
        conn.send('I got a WO')
        message = 'Here is the order: ' + str(work)
        conn.send(work)
        if 'shutter' in work:
            shutterState = work['shutter']
            if shutterState == 0:
                conn.send('Closing shutter')
            elif shutterState == 1:
                conn.send('Opening shutter')
        #
        if 'command' in work:
            comm=work['command']
            message='Asking to: ' + comm
            conn.send(message)
            if comm == 'stop':
                conn.send('Stop requested')
                carryOn=False
        else:
            message='Doing nothing'
            conn.send(message)

#consumer()
# Attempt to run this in a thread
if __name__ == "__main__":
    parent_conn, child_conn = Pipe() # Create a pipe for comms.
    # p = Process(target=f, args=(child_conn,))
    proc=Process(target=consumer, args=(child_conn,))
    proc.start()
    # proc.join() # Wait for the child process to finish before exiting.

    while True:
        if proc.is_alive():
            if parent_conn.poll():
                print('Consumer says: ' + str(parent_conn.recv()))
        else:
            print('Consumer is dead!')
            break