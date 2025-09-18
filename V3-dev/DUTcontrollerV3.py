# -*- coding: utf-8 -*-
"""
Created on Fri Aug  8 16:53:13 2025
New version using OOP
@author: CH-imbl
"""

#%%
import EPICScomm
import arduinoComm
import FPGAcomm
import keithleyComm
import scopeComm
import seqFuncs
import SNSmonitor as SNS

import sys
import time
import ast
import signal
# import io
# import numpy as np
# import matplotlib.pyplot as plt
# from PIL import Image
from  multiprocessing import Process, Pipe

#%% #### Shut down gracefully on receiving ^c interupt #####
def signal_handler(sig, frame):
    global carryOn
    print('Stopping capture')
    carryOn=False
    proc.terminate()
    shutDown()
    sys.exit(0)

signal.signal(signal.SIGINT, signal_handler)

#%% Clean up and exit
def shutDown():
    # Check if these handles exist and shut them down.
    if 'ar' in globals(): 
        if Inst['use Arduino']: ar.closeArduino()
    if 'kt' in globals():
        if Inst['use Keithley']: kt.closeKeithley()
    if 'sc' in globals():
        if Inst['use Scope']: sc.closeScope()
    if 'fpga' in globals():
        if Inst['use FPGA']: fpga.closeFPGA()
    if 'outFile' in globals(): outFile.close()
    sys.exit(0)
    
#%% Main script starts here...
if __name__ == "__main__":
    # Sequences are:
    #   0 - Write pattern A
    #   1 - Fault check pattern A
    #   2 - Write pattern B
    #   3 - Fault check pattern B
    #   4 - Read out device
    #   5 - Readout FPGA
    #   6 - Save oscillogram
    if len(sys.argv) > 1:
        argStr=sys.argv[1]
        sequence = ast.literal_eval(argStr)
        print("Sequence list is:", sequence)
        maxStep=len(sequence)
    else:
        # sequence=[0,1,2,3,0,1] # Default list
        print('Please provide the test sequence as a command argument')
        print('List the test/readout functions as a comma separated numerical list enclosed in square brackets')
        print('The number-function mapping is:')
        print(' 0 - Write pattern A\n 1 - Fault check pattern\n 2 - Write pattern B\n 3 - Fault check pattern B\n'
              ' 4 - Read out device\n 5 - Readout FPGA\n 6 - Save oscillogram')
        sys.exit(0)
    # Open a log file. Append if already exists.
    timeNow=time.localtime()
    timeStamp=(f'{timeNow.tm_mday}_{timeNow.tm_mon}_{timeNow.tm_hour}_{timeNow.tm_min}_')
    outFile=open('Data\\' + timeStamp + 'out_file.txt','a')
    
    #%% Create a thread and a pipe for the StepNShoot communication link
    parent_conn, child_conn = Pipe()
    # p = Process(target=f, args=(child_conn,))
    proc=Process(target=SNS.SNSmonitor, args=(child_conn,))
    proc.start()
    if proc.is_alive():
        SNSactive=True # We are using StepNShoot
    else:
        SNSactive=False

# Instantiate the instrument objects
    Inst={} # Dictionary showing which instruments are in use...
    
#%% EPICS
    try:
        Inst['use EPICS']=True
        ep=EPICScomm.EPICScomm()
    except:
        print('Unable to connect to EPICS')
        Inst['use EPICS']=False
        ep=None
    if Inst['use EPICS']:
        print('EPICS OK')
    else:
        print('No EPICS')
    
    #%% Arduino
    try:
        Inst['use Arduino']=True
        ar=arduinoComm.arduinoComm()
    except Exception as e:
        print(f'Unable to commmunicate with the microcontroller: {e}')
        Inst['use Arduino']=False
        ar=None
    if Inst['use Arduino']:
        print('Arduino OK')
    else:
        print('No Arduino')
    
    #%% Keithley
    try:
        Inst['use Keithley']=True
        kt=keithleyComm.keithleyComm()
    except Exception as e:
        print(f'Unable to communicate with Keithley PSU: {e}')
        Inst['use Keithley']=False
        kt=None
    if Inst['use Keithley']:
        print('Keithley OK')
    else:
        print('No Keithley')
    
    #%% Oscilloscope
    try:
        Inst['use Scope']=True
        sc=scopeComm.scopeComm()
    except Exception as e:
        print (f'Unable to connect to oscilloscope: {e}')
        # sys.exit(0)
        Inst['use Scope']=False
        sc=None
    if Inst['use Scope']:
        print('Scope OK')
    else:
        print('No Scope')

    #%% FPGA
    try:
        Inst['use FPGA']=True
        fpga=FPGAcomm.FPGAcomm()
    except Exception as e:
        print (f'Unable to connect to FPGA: {e}')
        # sys.exit(0)
        Inst['use FPGA']=False
        fpga=None
    if Inst['use FPGA']:
        print('FPGA OK')
    else:
        print('No FPGA')

#%% Sequencer
    time.sleep(0.5)
    seq=seqFuncs.sequencer(Inst,ep,ar,kt,sc,fpga, outFile)

#%% #### Start the main controller loop, as a sequencer #####
    carryOn=True
    step=0
    
    # Start with a writing pattern A
    if Inst['use Arduino']:
        reply=ar.Arduino_command(b'WA')
        if not reply[0] :
            print ('Write A command failed')
            carryOn=False
            print('No Arduino!')
    else:
        carryOn=False
        print('No Arduino!')

    # Loop whilst carryOn. Check errors back from DUT against thresholds
    thresholds=[1,99]
    while carryOn:
        # First - check for requests from StepNShoot, if it's running
        if (SNSactive and proc.is_alive()): # Check if any commands issued from StepNShoot
            if parent_conn.poll():
                WO=parent_conn.recv()
                print('SNS: ' + WO)
                if WO == 'Stop':
                    print('Stopping command loop program')
                    proc.terminate()
                    shutDown()
                if WO == 'Close shutter':
                    # caput(Shutter_PV + 'SHUTTEROPEN_CMD 0')
                    reply=ep.readShutter()
                    SHT=reply[1]
                    print('IMBL imaging shutter: ', SHT)
                if WO == 'Command: readDUT':
                    print('saving DUT memory as image')
                    seq.runThis(4)
                if WO == 'Command: scopeCap':
                    print('Capturing scope data')
                    seq.runThis(6)

    # For instance: A sequence of writing then fault checking patterns A and B.
    # Plus reading the FPGA output.
        # print(sequence[step], ':', seq.runThis(sequence[step]))
        result=seq.runThis(sequence[step])
        worked=result[0]
        errors=result[1]
        reply=result[2]
        # print(errors, reply)
    # Actions to be taken on deteting problems / errors
        if not worked:
            print('Oops something went wrong in the process')
        if (errors[1] > thresholds[1]):
            print('Second error threshold passed')
        elif errors[1] > thresholds[0]:
            print('First threshold passed')
            
        step = (step + 1) % maxStep # Write, fault check only
    
    # Also exit program if carryOn gets set false.
    print('Stopping command loop program')
    proc.terminate()
    shutDown()

  
