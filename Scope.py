# -*- coding: utf-8 -*-
"""
Created on Tue Aug 19 16:06:44 2025

@author: imbl
"""

import pyvisa
import numpy as np

#  
def scopeInit():
    rm = pyvisa.ResourceManager('@py')
    reSources=rm.list_resources()
    lastResource=reSources[len(reSources)-1]
    if not (lastResource[0:3]) == 'USB' :
        print('Scope USB connection not found')
        rm.close()
        return -1
    # print(inst.query("*IDN?"))
    try:
        scope = rm.open_resource('USB0::6833::1201::DS4A162850305::0::INSTR') # Example USB address
        # Query instrument identification
        print('Oscilloscope is: ' + scope.query('*IDN?').strip())
        return scope
    except pyvisa.errors.VisaIOError as e:
        print(f"Error connecting or communicating with the oscilloscope: {e}")
        return -1

def scopeGrab(scope, channel):
    sourceString=':WAV:SOUR CHAN' + str(channel)
    scope.write(sourceString)
    scope.write(':WAV:MODE NORM')
    # Get preamble for scaling
    preamble_str = scope.query(':WAV:PRE?')
    preamble = [float(x) for x in preamble_str.split(',')]
    x_increment = preamble[4]
    x_origin = preamble[5]
    y_increment = preamble[7]
    y_origin = preamble[8]
    # Acquire waveform data
    scope.write(':WAV:DATA?')
    # waveform_data = scope.query_binary_values(':WAV:DATA?', datatype='f', is_big_endian=False)
    waveform_bytes = scope.query_binary_values(':WAV:DATA?', datatype='B')
    waveform_data = np.array(waveform_bytes)
    # Scale the data
    scaled_waveform = (waveform_data - y_origin) * y_increment
    time_axis = (np.arange(len(scaled_waveform)) * x_increment) + x_origin
    return [scaled_waveform,time_axis]

def scopeClose():
    global rm, scope  
    if 'scope' in locals() and scope:
        print ('Closing scope VISA connection')
        scope.close()
        rm.close()