# -*- coding: utf-8 -*-
"""
Created on Wed Sep 17 16:54:28 2025

@author: imbl
"""

import serial

class FPGAcomm():
    def __init__(self):
# Create a serial link to microcontroller
        FPGA_COM='COM9'
        # open and init the Arduino serial port, with a 2 second timeout
        try:
            self.serFPGA = serial.Serial(FPGA_COM,baudrate=115200, bytesize=8, parity='N', stopbits=1,
                            xonxoff=0, rtscts=0, timeout=5)
        except Exception as e:
            raise e
        self.serFPGA.readline() # Clear the last line from the buffer
    
    def readFPGA(self):
        try:
            reply=self.serFPGA.readline().decode('utf-8')
        except:
            return (False, reply)
        return (True, reply)
    
    def FPGA_errReadBack(self):
        reply=self.readFPGA()
        if reply[0]:
            if reply[1].strip() != 'Hello World!':
            # print('Faulted?')
                return(False, [99,99,99], reply[1])
            else:
                return (True, [0,0,0], reply[1])
        else:
            return(False, [99,99,99], reply[1])
    
# Close the microcontroller serial connection    
    def closeFPGA(self):
        self.serFPGA.close()
        return (True, 'Closed OK')