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
from PIL import Image

# Shut down gracefully on receiving ^c interupt
def signal_handler(sig, frame):
    print('Stopping capture')
    serArduino.close()
    sys.exit(0)
signal.signal(signal.SIGINT, signal_handler)


def Arduino_errReadBack():
    readBack=serArduino.readline()
    if readBack != b'': # Something has come from the Arduino        
        arduinoString=readBack.decode('utf-8')
        print(arduinoString)
        ''' Depending on the DUT this section might get modified
        The standard digital test output is colon separated i.e.
        :<Error bits>:<error set bits>:<error reset bits>
        No errors would return ':0:0:0'
        '''
        arduinoStringClean=arduinoString.strip()
        # Check if it's error returns...
        data=arduinoStringClean.split(':')
        if len(data) == 4 :
            errs=int(data[1]) # Total bits in error
            sets=int(data[2]) # Bits set which should be reset
            resets=int(data[3]) # Bits reset which should be set
            return errs,sets,resets
        else:
            return 'Data fault'
    else:
        return 'Comms fault' # Timeout

def Arduino_command(command):
    serArduino.write(command)
    time.sleep(0.5)
    readBack=serArduino.readline() # Expect an 'OK' if happy.        
    arduinoString=readBack.decode('utf-8')
    # print(arduinoString)
    if arduinoString.strip() == 'OK':
        return True
    else:
        return False

def Arduino_ReadSRAM():
    SRAMarray=bytearray()
    for i in range (2048):
        readBack=serArduino.readline()
        if readBack != b'': 
            #arduinoString=readBack.decode('utf-8')
            SRAMarray.extend(readBack[:-2]) # Get rid of cr/lf
        else:
            break
    return SRAMarray

#%% Main script
ArduinoCOM='COM5'
SRAMimage=[32,2049]
# open and init the Arduino serial port, with a 2 second timeout
serArduino = serial.Serial(ArduinoCOM,baudrate=115200, bytesize=8, parity='N', stopbits=1,
                    xonxoff=0, rtscts=0, timeout=5)
time.sleep(5) # Wait for 5 seconds for first test

#%% First check...
# serArduino.reset_input_buffer()
Errs=Arduino_errReadBack() # First readback after comms init.
timeNow=time.asctime(time.localtime())
DUTstatus=f'Total errors: {Errs[0]}, Set: {Errs[1]}, Reset: {Errs[2]}'
# print(DUTstatus)
if Errs[0] != 0 : # Take an action if errors are detected.
    print('Errors detected.')
    # caput(Shutter_PV + 'SHUTTEROPEN_CMD 0')
    # SHT=caget(Shutter_PV + 'SHUTTEROPEN_MONITOR')
    # print(SHT)
    # carryOn=False

#%% Start the controller loop
carryOn=True
sequence=0
while carryOn:
# Set up a three state sequence of writing, fault checking, and reading.
    if sequence == 0:
        print('Requesting write')
        if not Arduino_command(b'W'):
            print ('Command failed')
            break
    elif sequence == 1:
        print('Requesting fault check')
        if not Arduino_command(b'F'):
            print ('Command failed')
            break
        Errs=Arduino_errReadBack()
        if not len(Errs) == 3:
            print(f'Command failed: {Errs}')
            break
        timeNow=time.asctime(time.localtime())
        DUTstatus=f'Total errors: {Errs[0]}, Set: {Errs[1]}, Reset: {Errs[2]}'
        print(DUTstatus)
    elif sequence == 2:
        print('Requesting read')
        if not Arduino_command(b'R'):
              print ('Command failed')
              break
        SRAMarray=Arduino_ReadSRAM()
        width, height = 256, 256
        mode = "L"  # "L" for grayscale
        # Create an Image object from the raw pixel data
        img = Image.frombytes(mode, (width, height), SRAMarray)
        # Save the image to a file
        img.save('output_raw_pixel_data.png') 
        break
    else:
        print('Continuing sequence')

    #sequence = (sequence + 1) % 3
    sequence = (sequence + 1) % 2

# Exit program if carryOn gets set false.
print('Stopping command loop program')
serArduino.close()
sys.exit(0)