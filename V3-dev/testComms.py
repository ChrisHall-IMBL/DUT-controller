# -*- coding: utf-8 -*-
"""
Created on Mon Sep  8 16:49:11 2025

@author: imbl
"""

import EPICScomm
import arduinoComm
import keithleyComm
import scopeComm
import seqFuncs
# import sys
import time

Inst={} # Dictionary showing which instruments to use
#%% EPICS
try:
    Inst['use EPICS']=True
    ep=EPICScomm.EPICScomm()
    # print(ep)
except:
    print('Unable to connect to EPICS')
    # sys.exit(0)
    Inst['use EPICS']=False
if Inst['use EPICS']:
    print('EPICS OK')
    print(f'EPICS shutter state... {ep.readShutter()}')
    print(f'EPICS I/C current... {ep.readIC()}\n')

#%% Arduino
try:
    Inst['use Arduino']=True
    ar=arduinoComm.arduinoComm()
    # print(ar)
except Exception as e:
    print(f'Unable to commmunicate with the microcontroller: {e}')
    # sys.exit(0)
    Inst['useArduino']=False
if not Inst['use Arduino']:
    print(f'Arduino error readback... {ar.readErr()}')
print('Arduino OK\n')

#%% Keithley
try:
    Inst['use Keithley']=True
    kt=keithleyComm.keithleyComm()
    # print(kt)
except Exception as e:
    print(f'Unable to communicate with Keithley PSU: {e}')
    # sys.exit(0)
    Inst['use Keithley']=False
if Inst['use Keithley']:
    print ('Keithley OK')
    print (f'Keithley instrument... {kt.checkKeithley()}')
    print (f'Keithley current... {kt.readCurrent(3)}\n')

#%% Oscilloscope
try:
    Inst['use Scope']=True
    sc=scopeComm.scopeComm()
    # print(sc)
except Exception as e:
    print (f'Unable to connect to oscilloscope: {e}')
    # sys.exit(0)
    Inst['use Scope']=False
if Inst['use Scope']:
    print('Oscilloscope OK')
    print(f'Oscilloscope is... {sc.scopeCheck()}\n')


#%% The log file
    timeNow=time.localtime()
    timeStamp=(f'{timeNow.tm_mday}_{timeNow.tm_mon}_{timeNow.tm_hour}_{timeNow.tm_min}_')
    outFile=open(timeStamp + 'out_file.txt','a')

#%% The sequencer
seq=seqFuncs.sequencer(Inst,ep,ar,kt,sc,outFile)
print(f'\nUsing - EPICS:{Inst["use EPICS"]}, Arduino:{Inst["use Arduino"]}, Keithley:\
{Inst["use Keithley"]}, Oscilloscope:{Inst["use Scope"]}\n')

# %% Tidy up
print('Tidy up...')
print(f'Closing Arduino comms... {ar.closeArduino()}')
print (f'Closeing Keithley comms... {kt.closeKeithley()}')
print(f'Closing O\'scope comms... {sc.closeScope()}')
print(f'Closing sequencer... {seq.closeSequencer()}')
outFile.close()


