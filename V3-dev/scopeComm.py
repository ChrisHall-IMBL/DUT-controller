# -*- coding: utf-8 -*-
"""
Created on Tue Aug 19 16:06:44 2025

@author: imbl
"""

import pyvisa
import numpy as np

class scopeComm():
    def __init__(self):
        self.rm = pyvisa.ResourceManager('@py')
        reSources=self.rm.list_resources()
        lastResource=reSources[len(reSources)-1]
        if not (lastResource[0:3]) == 'USB' :
            self.rm.close()
            raise ValueError('Scope USB connection not found')
            # return (False,'Scope USB connection not found')
        # print(inst.query("*IDN?"))
        try:
            self.scope = self.rm.open_resource('USB0::6833::1201::DS4A162850305::0::INSTR') # 
        except Exception as e:
            raise e
            
    def scopeCheck(self):
        # Query instrument identification
        try:
            reply=f'Oscilloscope is: {self.scope.query('*IDN?').strip()}'
        except Exception as e:
            return (False, f'Unable to communicate with scope: {e}')
        return (True, reply)
        # except pyvisa.errors.VisaIOError as e:
        #     return (False, f"Error connecting or communicating with the oscilloscope: {e}")

    def scopeGrab(self, channel):
        sourceString=':WAV:SOUR CHAN' + str(channel)
        self.scope.write(sourceString)
        self.scope.write(':WAV:MODE NORM')
        # Get preamble for scaling
        preamble_str = self.scope.query(':WAV:PRE?')
        preamble = [float(x) for x in preamble_str.split(',')]
        x_increment = preamble[4]
        x_origin = preamble[5]
        y_increment = preamble[7]
        y_origin = preamble[8]
        # Acquire waveform data
        self.scope.write(':WAV:DATA?')
        # waveform_data = scope.query_binary_values(':WAV:DATA?', datatype='f', is_big_endian=False)
        waveform_bytes = self.scope.query_binary_values(':WAV:DATA?', datatype='B')
        waveform_data = np.array(waveform_bytes)
        # Scale the data
        scaled_waveform = (waveform_data - y_origin) * y_increment
        time_axis = (np.arange(len(scaled_waveform)) * x_increment) + x_origin
        return (True, [scaled_waveform,time_axis])
    
    def scopeMeasV(self, channel):
        if channel != 0:
            sourceString=':WAV:SOUR CHAN' + str(channel)
            self.scope.write(sourceString)
        voltS=self.scope.query(':MEASURE:VMAX?')
        try:
            voltF = float( voltS)
            return (True, voltF)
        except:
            return (False, voltS)
    
    def closeScope(self):
            self.scope.close()
            self.rm.close()
            return (True, 'Closed OK')