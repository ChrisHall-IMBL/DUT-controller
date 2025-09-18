# -*- coding: utf-8 -*-
"""
Created on Wed Sep 17 17:13:14 2025

@author: imbl
"""

import FPGAcomm as FPGA

iCE=FPGA.FPGAcomm()
try:
    while True:
        readout=iCE.readFPGA()
        if readout[0]:
            reply=readout[1].strip()
            print(f'iCEstick says: {reply}')
        if reply != 'Hello World!':
            print('Faulted?')
    
except KeyboardInterrupt:
    try:
        iCE.closeFPGA()
        print('Stopping')
    except:
            pass
except:
    import traceback
    traceback.print_exc()
    print('error')
    try:
        iCE.closeFPGA()
    except:
        pass
