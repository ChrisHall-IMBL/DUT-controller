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
import csv
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
    if 'serArduino' in globals(): serArduino.close()
    if 'serKeithley' in globals(): serKeithley.close()
    if 'scope' in globals(): sc.scopeClose()
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
        SRAMarray=Ar.Arduino_ReadSRAM(serArduino)
        width, height = 256, 256
        mode = "L"  # "L" for grayscale
        # Create an Image object from the raw pixel data
        img = Image.frombytes(mode, (width, height), SRAMarray)
        # Save the image to a file
        timeNow=time.localtime()
        timeStamp=(f'{timeNow[3]}_{timeNow[4]}_{timeNow[5]}_')
        img.save('Data\\' + timeStamp+'SRAM.png')

    #################################       
    elif Seq==5:
        # print('Saving oscilloscope data')
        [scaled_waveform,time_axis]=sc.scopeGrab(scope, scopeChannel)
        timeNow=time.localtime()
        timeStamp=(f'{timeNow[3]}_{timeNow[4]}_{timeNow[5]}_')
        scopeFile='Data\\' +timeStamp + '_scope_data.csv'
        with open(scopeFile, 'w', newline='') as csvfile:
            scopeWriter = csv.writer(csvfile, delimiter=',',
                                    quotechar='|', quoting=csv.QUOTE_MINIMAL)
            for row in range(len(time_axis)):
            #scopeWriter.writerows(f'{time_axis} , {scaled_waveform}')
                scopeWriter.writerow([time_axis[row], scaled_waveform[row]])
        csvfile.close()
   
#%% Main script starts here...
if __name__ == "__main__":

    # Open a log file. Append if already exists.
    timeNow=time.localtime()
    timeStamp=(f'{timeNow.tm_mday}_{timeNow.tm_mon}_{timeNow.tm_hour}_{timeNow.tm_min}_')
    outFile=open('Data\\' + timeStamp + 'out_file.txt','a')
    
    #%% Create a thread and a pipe for the StepNShoot communication link
    parent_conn, child_conn = Pipe(False) # Unidirectional
    # p = Process(target=f, args=(child_conn,))
    proc=Process(target=SNS.SNSmonitor, args=(child_conn,))
    proc.start()
    if proc.is_alive():
        SNSactive=True # We are using StepNShoot
    else:
        SNSactive=False

    #%% Serial link to microcontroller
    ArduinoCOM='COM5'
    # open and init the Arduino serial port, with a 2 second timeout
    try:
        serArduino = serial.Serial(ArduinoCOM,baudrate=115200, bytesize=8, parity='N', stopbits=1,
                        xonxoff=0, rtscts=0, timeout=5)
    except:
        print('Arduino connection faulted')
        shutDown()
    # serArduino.reset_input_buffer()
    try:
        Errs=Ar.Arduino_errReadBack(serArduino) # First readback after comms init.
    except:
        print('Arduino readback failed')
        shutDown()
    # If it gets here...all good
    timeNow=time.asctime(time.localtime())
    DUTstatus=f'Total errors: {Errs[0]}, Set: {Errs[1]}, Reset: {Errs[2]}'
    print(timeNow + ' ucontroller connected: ' +DUTstatus)

    #%% Serial link to Keithley
    KeithleyCOM='COM3'
    # Open the serial connection to the power supply
    try:
        serKeithley = serial.Serial(KeithleyCOM, baudrate=9600, bytesize=8, parity='N', stopbits=1,
                        xonxoff=0, rtscts=0, timeout=1, write_timeout=1)
    except:
        print('Keithley connection faulted')
        shutDown()
    # Check the Keithley PSU connection with a SCPI IDN request.
    try:
        serKeithley.write("*IDN?\n".encode())  # Send ID command to check OK
    except:
        print('Caught comms exception')
        raise
    response = serKeithley.readline().decode()  # read response (ID string)
    print('PSU is: ',response.strip())
    
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
    #   5 - Oscilloscope grab
    sequence=(1,1,1,1,1)
    print(f'sequence is {sequence} with {maxStep} steps')
    
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
                if WO == 'Command: scopeCap':
                    print('Capturing scope data')
                    RunThis(5)
                if WO == 'Command: readDUT':
                    print('saving DUT memory to disk')
                    RunThis(4)

    # A four state sequence of writing then fault checking patterns A and B.
        # seqF.RunThis(sequence)
        RunThis(sequence[step])
        step = (step + 1) % maxStep # Write, fault check only
    
    # Also exit program if carryOn gets set false.
    print('Stopping command loop program')
    proc.terminate()
    shutDown()

  
