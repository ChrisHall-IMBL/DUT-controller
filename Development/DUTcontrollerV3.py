# -*- coding: utf-8 -*-
"""
Created on Fri Aug  8 16:53:13 2025

@author: imbl
"""

#%%
import serial
import signal
import sys
import time
# import io
# import numpy as np
# import matplotlib.pyplot as plt
from PIL import Image
from  multiprocessing import Process, Pipe
import ArduinoFuncs as Ar
from epics import caget, caput
import SNSmonitor as SNS
import Scope as sc
# import seqFuncs as seqF

#%%
##### Shut down gracefully on receiving ^c interupt #####
def signal_handler(sig, frame):
    print('Stopping capture')
    proc.terminate()
    shutDown()
    sys.exit(0)
signal.signal(signal.SIGINT, signal_handler)

#%%
def shutDown():
    # Check if these handles exist and shut them down.
    if 'Arduino' in globals(): Arduino.close()
    if 'Keithley' in globals(): Keithley.close()
    if 'Scope' in globals():
        if (scope != -1): Scope.close()
    if 'outFile' in globals(): outFile.close()
    sys.exit(0)

def RunThis(Seq):
    # Functions used in the sequencer
    def ReadKeithley(channel, ser):
            command=f'INST:NSEL {channel+1}\n'
            ser.write(command.encode())  # Send command
            # command='MEAS:VOLT?\n'
            # ser.write(command.encode())  # Send command
            # voltsS = ser.readline().decode()  # read response
            # voltsF=float(voltsS)
            command='MEAS:CURR?\n'
            ser.write(command.encode())  # Send command
            currS = ser.readline().decode()  # read response
            currF=float(currS)
            # print(voltsF,' V ',currF,' A')
            return currF
    # DUT status utility function
    def reportDUTstatus(DUTstatus): 
        timeNow=time.asctime(time.localtime()) # String version of the time.
        try:
            IC=float(caget(IC_PV))
            SHT='OPEN' if caget(Shutter_PV + 'SHUTTEROPEN_MONITOR') else 'CLOSED'
        except:
            SHT='Failed'
        try:
            voltS=scope.query(':MEASURE:VMAX?')
            voltF = float( voltS)
        except:
            voltF=999.999
        try:
            Pcurr=ReadKeithley(3,serKeithley)
        except:
            Pcurr=999.999
        
        outRow=DUTstatus + ', ' ' shutter is:' + SHT \
           + f', DUT current is: {voltF:.2f}' \
           + f', IC current is: {IC:.2f}'  \
           + f',  PSU current is: {Pcurr:.4f} A'    
        print(outRow)
        outFile.write(timeNow + ': ' + outRow + '\n')
        
    ##### These are the sequence operations #######
    ################################
    # Write a pattern A
    if Seq == 0:
        # print('Starting sequence')
        if not Ar.Arduino_command(serArduino,b'WA'):
            print ('Write A command failed')

    ################################
    # Fault check pattern A
    elif Seq == 1:
        print('Requesting fault check pattern A')
        if not Ar.Arduino_command(serArduino,b'FA'):
            print ('Fault A command failed')
        Errs=Ar.Arduino_errReadBack(serArduino)
        if not len(Errs) == 3:
            print(f'Reply failed: {Errs}')
        DUTstatus=f'Total errors: {Errs[0]}, Set: {Errs[1]}, Reset: {Errs[2]}'
        reportDUTstatus(DUTstatus)
    
    ###############################
    # Write a pattern B
    elif Seq == 2: 
        print('Requesting write pattern B')
        if not Ar.Arduino_command(serArduino,b'WB'):
            print ('Write command failed')
    
    ################################
    # Fault check pattern B
    elif Seq == 3:
        print('Requesting fault check pattern B')
        if not Ar.Arduino_command(serArduino,b'FB'):
            print ('Fault B command failed')
        Errs=Ar.Arduino_errReadBack(serArduino)
        if not len(Errs) == 3:
            print(f'Reply failed: {Errs}')
        DUTstatus=f'Total errors: {Errs[0]}, Set: {Errs[1]}, Reset: {Errs[2]}'
        reportDUTstatus(DUTstatus)
        
    ################################
    elif Seq == 4:
        print('Requesting read')
        if not Ar.Arduino_command(serArduino,b'R'):
              print ('Command failed')
        SRAMarray=Ar.Arduino_ReadSRAM()
        width, height = 256, 256
        mode = "L"  # "L" for grayscale
        # Create an Image object from the raw pixel data
        img = Image.frombytes(mode, (width, height), SRAMarray)
        # Save the image to a file
        timeNow=time.localtime()
        timeStamp=(f'{timeNow[3]}_{timeNow[4]}_{timeNow[5]}_')
        img.save(timeStamp+'SRAM.png')
        
    elif Seq==5:
        wave=sc.scopeGrab(scope, scopeChannel)
        # plt.plot(wave)
   
#%% Main script starts here...
if __name__ == "__main__":
    # Open a log file. Append if already exists.
    timeNow=time.localtime()
    timeStamp=(f'{timeNow.tm_mday}_{timeNow.tm_mon}_{timeNow.tm_hour}_{timeNow.tm_min}_')
    outFile=open(timeStamp + 'out_file.txt','a')
    
    #%% Create a thread and a pipe for the StepNShoot communication link
    parent_conn, child_conn = Pipe()
    # p = Process(target=f, args=(child_conn,))
    proc=Process(target=SNS.SNSmonitor, args=(child_conn,))
    proc.start()
    if proc.is_alive():
        SNSactive=True # We are using StepNShoot
    else:
        SNSactive=False
    
    #%% Test EPICS CA for connectivity, using the ionisation chamber
    IC_PV='SR08ID01DAQ03:Measure'
    Shutter_PV='SR08ID01IS01:'
    try:
        IC=caget(IC_PV)
        SHT='OPEN' if caget(Shutter_PV + 'SHUTTEROPEN_MONITOR') else 'CLOSED'
    except:
        shutDown()
    print('IMBL ionisation chamber reading: ', IC)
    print('IMBL imaging shutter: ', SHT)
    # If it clears this then CA is established
    
    #%% Visa link to the oscilloscope
    scope=sc.scopeInit()
    if scope == -1:
        print('Connection to scope failed')
        shutDown()
    scopeChannel=2
    print(f'Monitoring scope channel {scopeChannel}')

    #%%
    ##### Start the main controller loop, as a sequencer #####
    carryOn=True
    step=0
    maxStep=5
    # Sequences are:
    #   0 - Write pattern A
    #   1 - Fault check pattern A
    #   2 - Write pattern B
    #   3 - Fault check pattern B
    #   4 - Read out device
    sequence=(1,1,2,3,0)
    
    # Start with a writing pattern A
    #  print('Requesting write pattern A')
    if not Ar.Arduino_command(serArduino,b'WA'):
        print ('Write A command failed')
        carryOn=False
    
    while carryOn:
        # Check for requests from StepNShoot, if it's running
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
                    # SHT=caget(Shutter_PV + 'SHUTTEROPEN_MONITOR')
                    print('IMBL imaging shutter: ', SHT)
                if WO == '':
                    pass

    # A four state sequence of writing then fault checking patterns A and B.
        # seqF.RunThis(sequence)
        RunThis(sequence[step])
        step = (step + 1) % maxStep # Write, fault check only
    
    # Also exit program if carryOn gets set false.
    print('Stopping command loop program')
    proc.terminate()
    shutDown()

  
