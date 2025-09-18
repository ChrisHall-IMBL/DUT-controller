# -*- coding: utf-8 -*-
"""
Created on Fri Aug 29 17:35:30 2025
Communication object for the Keithley power supply.
Uses SCPI over a 9600 baud serial interface.
@author: CH@imbl
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
        except Exception as e:
            raise e
    
    def checkKeithley(self):
        # Check the Keithley comms with a SCPI IDN request.
        try:
            self.serKeithley.write("*IDN?\n".encode())  # Send ID command to check OK
        except Exception as e:
            raise e
        response = self.serKeithley.readline().decode()  # read response (ID string)
        reply=f'PSU is: {response.strip()}'
        return (True, reply)

    def readCurrent(self, channel):
        command=f'INST:NSEL {channel+1}\n'
        self.serKeithley.write(command.encode())  # Send command
        command='MEAS:CURR?\n'
        self.serKeithley.write(command.encode())  # Send command
        currS = self.serKeithley.readline().decode()  # read response
        try:
            currF=float(currS)
            return (True, currF)
        except:
            return(False, 999.999)
    
    def readVoltage(self, channel):
        command=f'INST:NSEL {channel+1}\n'
        self.serKeithley.write(command.encode())  # Send command
        command='MEAS:VOLTS?\n'
        self.serKeithley.write(command.encode())  # Send command
        voltS = self.serKeithley.readline().decode()  # read response
        try:
            voltF=float(voltS)
            return (True, voltF)
        except:
            return(False, 999.999)
    
    def closeKeithley(self):
        self.serKeithley.close()
        return (True, 'Closed OK')