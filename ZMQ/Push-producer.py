# -*- coding: utf-8 -*-
"""
Created on Wed Aug 13 15:32:21 2025
Stub to test the ZMQ  communication to the DUT controller program
@author: hallc
"""

import time
import zmq

class producer():
    def __init__(self):
    # Function to send work orders over the ZMQ socket
        self.context = zmq.Context()
        self.zmq_socket = self.context.socket(zmq.PUSH)
        self.zmq_socket.bind("tcp://127.0.0.1:5557")
        
        self.poller = zmq.Poller()
        self.poller.register(self.zmq_socket, zmq.POLLOUT) # Register for send readiness
       
   
    def sendMsg(self, message):
        if self.poller.poll(1000):
            self.zmq_socket.send_json(message)
            return True
        else:
            return False
    def close(self):
        self.zmq_socket.close()
      
WOsender=producer() # Instantiate the producer and create a ZMQ PUSH connection   
# Send a shutter close command
print('Sending: shutter close request')
work_message = { 'shutter' : 0 }
if (WOsender.sendMsg(work_message)):
    print('Work order message sent OK')
else:
    print('Work order message failed or timed out')
time.sleep(0.5)
print()

# # Send a shutter open and continue command
print('Sending shutter open request, and Continue command')
work_message = { 'shutter' : 1 , 'command' : 'continue'}
if (WOsender.sendMsg(work_message)):
    print('Work order message sent OK')
else:
    print('Work order message failed or timed out')
time.sleep(0.5)
print()

# # Send a shutter close and continue
# print('Sending shutter close')
# work_message = { 'shutter' : 0, 'command' : 'continue' }
# zmq_socket.send_json(work_message)
# # Wait until sending command to stop
comm=input('Ready to send a stop')
work_message = { 'command' : 'stop' }
if (WOsender.sendMsg(work_message)):
    print('Work order message sent OK')
else:
    print('Work order message failed or timed out')

# zmq_socket.send_json(work_message)
WOsender.close() # Need to axplicitly close the socket for re-use
