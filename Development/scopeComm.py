# -*- coding: utf-8 -*-
"""
Created on Tue Aug 19 16:06:44 2025

@author: imbl
"""

import pyvisa

class scopeComm():
#  
    def __init__(self):
        rm = pyvisa.ResourceManager('@py')
        reSources=rm.list_resources()
        lastResource=reSources[len(reSources)-1]
        if not (lastResource[0:3]) == 'USB' :
            print('Scope USB connection not found')
            rm.close()
            return -1
        # print(inst.query("*IDN?"))
        try:
            self.scope = rm.open_resource('USB0::6833::1201::DS4A162850305::0::INSTR') # Example USB address
            # Query instrument identification
            print('Oscilloscope is: ' + self.scope.query('*IDN?').strip())
            return self.scope
        except pyvisa.errors.VisaIOError as e:
            print(f"Error connecting or communicating with the oscilloscope: {e}")
            return -1

    def scopeGrab(scope, channel):
        sourceString=':WAV:SOUR CHAN' + str(channel)
        scope.write(sourceString)
        scope.write(':WAV:MODE NORM')
        # Acquire waveform data
        scope.write(':WAV:DATA?')
        waveform_data = scope.query_binary_values(':WAV:DATA?', datatype='f', is_big_endian=False)
        return waveform_data
    
    def scopeClose(scope):
        if 'scope' in locals() and scope:
            print ('Closing scope VISA connection')
            scope.close()