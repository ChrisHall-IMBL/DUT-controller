# -*- coding: utf-8 -*-
"""
Created on Fri Aug 29 17:35:30 2025

@author: imbl
"""
import serial

class keithleyComm():
    def __init__(self):
    #%% Serial link to Keithley
        KeithleyCOM='COM3'
        # Open the serial connection to the power supply
        try:
            self.serKeithley = serial.Serial(KeithleyCOM, baudrate=9600, bytesize=8, parity='N', stopbits=1,
                            xonxoff=0, rtscts=0, timeout=1, write_timeout=1)
        except:
            print('Keithley connection faulted')
            #shutDown()
            return -1
        # Check the Keithley PSU connection with a SCPI IDN request.
        try:
            self.serKeithley.write("*IDN?\n".encode())  # Send ID command to check OK
        except:
            print('Caught comms exception')
            raise
        response = self.serKeithley.readline().decode()  # read response (ID string)
        print('PSU is: ',response.strip())
