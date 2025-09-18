# -*- coding: utf-8 -*-
"""
Created on Fri Aug 29 16:39:58 2025
Communication object for the Arduiono microcontroller.
Uses a 115,200 baud serial link with a custom command protocol.
@author: imbl
"""
import serial, time

class arduinoComm():
    def __init__(self):
# Create a serial link to microcontroller
        ArduinoCOM='COM5'
        # open and init the Arduino serial port, with a 2 second timeout
        try:
            self.serArduino = serial.Serial(ArduinoCOM,baudrate=115200, bytesize=8, parity='N', stopbits=1,
                            xonxoff=0, rtscts=0, timeout=5)
        except Exception as e:
            raise e
        self.serArduino.readline()

# Format the chip error readback
    def readErr(self):
        try:
            Errs=self.Arduino_errReadBack()
        except:
            return(False, 'Arduino readback failed')
        # If it gets here...all good
        timeNow=time.asctime(time.localtime())
        DUTstatus=f'Total errors: {Errs[0]}, Set: {Errs[1]}, Reset: {Errs[2]}'
        # print(timeNow + ' ucontroller connected: ' +DUTstatus)
        reply=f'{timeNow} ucontroller connected: {DUTstatus}'
        return (True, reply)

# Parse the error readback from the DUT        
    def Arduino_errReadBack(self):
        readBack=self.serArduino.readline()
        if readBack[1] != b'': # Something has come from the Arduino        
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
                return (True, [errs,sets,resets])
            else:
                return (False,'Data fault')
        else:
            return (False,'Comms fault') # Timeout

# Issue a command to the microcontroller
    def Arduino_command(self,command):
        self.serArduino.write(command)
        readBack=self.serArduino.readline() # Expect an 'OK' if happy.        
        arduinoString=readBack.decode('utf-8')
        # print(arduinoString)
        if arduinoString.strip() == 'OK':
            return (True, 'OK')
        else:
            return (False, 'Command fault')

# Readout the SRAM array
    def Arduino_readSRAM(self):
        reply=self.Arduino_command(b'R')
        if not reply[0] :
              print ('Command failed')
        SRAMarray=bytearray()
        for i in range (2048):
            readBack=self.serArduino.readline()
            if readBack != b'': 
                #arduinoString=readBack.decode('utf-8')
                SRAMarray.extend(readBack[:-2]) # Get rid of cr/lf
            else:
                return (False, 'Read RAM fault')
        return (True, SRAMarray)

# Close the microcontroller serial connection    
    def closeArduino(self):
        self.serArduino.close()
        return (True, 'Closed OK')