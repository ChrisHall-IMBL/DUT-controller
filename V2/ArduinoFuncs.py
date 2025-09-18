# -*- coding: utf-8 -*-
"""
Created on Fri Aug 15 12:57:34 2025

@author: imbl
"""


def Arduino_errReadBack(serArduino):
    readBack=serArduino.readline()
    if readBack != b'': # Something has come from the Arduino        
        arduinoString=readBack.decode('utf-8')
        # print(arduinoString)
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

def Arduino_command(serArduino,command):
    serArduino.write(command)
    readBack=serArduino.readline() # Expect an 'OK' if happy.        
    arduinoString=readBack.decode('utf-8')
    # print(arduinoString)
    if arduinoString.strip() == 'OK':
        return True
    else:
        return False

def Arduino_ReadSRAM(serArduino):
    SRAMarray=bytearray()
    for i in range (2048):
        readBack=serArduino.readline()
        if readBack != b'': 
            #arduinoString=readBack.decode('utf-8')
            SRAMarray.extend(readBack[:-2]) # Get rid of cr/lf
        else:
            break
    return SRAMarray