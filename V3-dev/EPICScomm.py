# -*- coding: utf-8 -*-
"""
Created on Mon Sep  8 16:17:49 2025

@author: imbl
"""
from epics import caget, caput

class EPICScomm():
    def __init__(self):
        self.IC_PV='SR08ID01DAQ03:Measure'
        self.Shutter_PV='SR08ID01IS01:'
        IC=caget(self.IC_PV)
        if IC == None:
            raise ('Cannot contact IC PV')
    
    def readIC(self):
        IC=caget(self.IC_PV)
        return (True, IC)
    
    def readShutter(self):
        SHT='OPEN' if caget(self.Shutter_PV + 'SHUTTEROPEN_MONITOR') else 'CLOSED'
        return (True, SHT)