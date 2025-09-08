# -*- coding: utf-8 -*-
"""
Created on Tue Aug 19 15:03:05 2025

Designed to be run in a thread.

It gets json messages from the zmq.PUSH application decodes them and sends
internal commands to the master application via a pipe .

The master app. will close the thread, and terminate the loop when required.

@author: CH/imbl
"""
import zmq

def SNSmonitor(conn):
    # 'conn' is this end of the pipe back to parent process
    #
    # Set up ZMQ socket to pull from this application
    context = zmq.Context()
    # recieve work
    consumer_receiver = context.socket(zmq.PULL)
    # consumer_receiver.bind("tcp://*:5557")
    consumer_receiver.connect("tcp://127.0.0.1:5557")
    conn.send('SNS connection is running')
    # Python dictionaries are sent as json messages:
    carryOn=True
    while carryOn:
        # Get the work order. Block on receive...
        work = consumer_receiver.recv_json()
        # conn.send('I got a WO')
        # message = 'Here is the order: ' + str(work)
        # conn.send(message)
        if 'shutter' in work: # This is a shutter command
            shutterState = work['shutter']
            if shutterState == 0:
                conn.send('Close shutter')
            elif shutterState == 1:
                conn.send('Open shutter')
        #
        if 'command' in work: # This is a process command
            comm=work['command']
            if comm == 'stop':
                conn.send('Stop')
            else:
                message='Command: ' + comm
                conn.send(message)

        else: # Unrecognised command
            message='SNS says: '+ str(work)
            conn.send(message)