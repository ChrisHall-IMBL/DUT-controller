# -*- coding: utf-8 -*-
"""
Created on Wed Aug 27 12:34:18 2025
Sequencer object exposes functions for reading DUT, EPICS, oscilloscope, FPGA, and Keithley
The comms objects are all instantiated in the main program and passed to the initialisation function.
@author: CH-imbl
"""

import time
from PIL import Image
import csv
    
class sequencer():
    def __init__(self,Inst,ep,ar,kt,sc, fpga,outFile):
        self.Inst=Inst
        self.ep=ep
        self.ar=ar
        self.kt=kt
        self.sc=sc
        self.fpga=fpga
        self.outFile=outFile
        self.scopeChannel=2
        self.keithleyChannel=3

    def reportDUTstatus(self, DUTstatus):
        # write a line to the log file with various status and monitor values
        # To keep the lines with the same elememnts. Dummy values may be used.
        timeNow=time.asctime(time.localtime()) # String version of the time.
        if self.Inst['use EPICS']:
            SHT=self.ep.readShutter()
            IC=self.ep.readIC()
        else:
            SHT=(False, 'Not connected')
            IC=(False, 999.999)
        #
        if self.Inst['use Keithley']:
            Pcurr=self.kt.readCurrent(self.keithleyChannel)
        else:
            Pcurr=(False, 999.999)
        #
        if self.Inst['use Scope']:
            reply=self.sc.scopeMeasV(self.scopeChannel)
            if reply[0]:
                #print(f'Scope read {reply[1]}')
                SVmax=reply[1]
            else:
                SVmax=0.0
        else:
            SVmax=0.0
            
        outRow=DUTstatus + ', ' ' shutter is:' + SHT[1] \
           + f', IC current is: {IC[1]:.4f}'  \
           + f',  PSU current is: {Pcurr[1]:.4f}, Scope Vmax is: {SVmax:.4f}'
        statusLine=timeNow + ': ' + outRow
        self.outFile.write(statusLine + '\n')
        print(statusLine)

    def runThis(self, Seq):
        # Chack against comms status in Inst before attempting comms
        # Each section will return a boolean to indicate a fault or failure...
        # A triplet of errors detected and a text description of the status.

        ###############################
        # Write a pattern A to the SRAM
        if Seq == 0:
            if self.Inst['use Arduino']:   
                try:
                    self.ar.Arduino_command(b'WA')
                except:
                    return (False, [99,99,99], '"Write A" command failed')
            else:
                return (False, [99,99,99], 'No Arduino')
            return (True, [0,0,0], 'DUT write OK')

        ################################
        # Fault check pattern A on the SRAM
        elif Seq == 1:
            if self.Inst['use Arduino']:   
                print('Requesting fault check pattern A')
                try:
                    self.ar.Arduino_command(b'FA')
                except:
                    return (False, [99,99,99], '"Fault A" command failed')
                Errs=self.ar.Arduino_errReadBack()
                if not Errs[0]:
                    print('Arduino - error readback failed')
                DUTstatus=f'SRAM errors: {Errs[1][0]}, Set: {Errs[1][1]}, Reset: {Errs[1][2]}'
                self.reportDUTstatus(DUTstatus)
                return(True, Errs[1], 'SRAM check OK')
            else:
                return (False, [99,99,99],'No Arduino')
        
        ###############################
        # Write a pattern B to the SRAM
        elif Seq == 2:
            if self.Inst['use Arduino']:   
                try:
                    self.ar.Arduino_command(b'WB')
                except:
                    return (False, [99,99,99], '"Write B" command failed')
            else:
                return (False, [99,99,99], 'No Arduino')
            return (True, [0,0,0], 'SRAM write OK')
        
        ################################
        # Fault check pattern B on the SRAM
        elif Seq == 3:
            if self.Inst['use Arduino']: 
                print('Requesting fault check pattern B')
                try:
                    self.ar.Arduino_command(b'FB')
                except:
                    return (False, [99,99,99], '"Fault B" command failed')
                Errs=self.ar.Arduino_errReadBack()
                if not Errs[0]:
                    print(f'Reply failed: {Errs}')
                DUTstatus=f'SRAM errors: {Errs[1][0]}, Set: {Errs[1][1]}, Reset: {Errs[1][2]}'
                self.reportDUTstatus(DUTstatus)
                return(True, Errs[1], 'SRAM check OK')
            else:
                return (False, [99,99,99], 'No Arduino')

        ################################
        # Readout the SRAM array to a file
        elif Seq == 4:
            if self.Inst['use Arduino']: 
                print('Requesting read')
                try:
                    reply=self.ar.Arduino_readSRAM()
                except:
                    return (False, [99,99,99], '"Read SRAM" command failed')
                SRAMarray=reply[1]
                width, height = 256, 256
                mode = "L"  # "L" for grayscale
                # Create an Image object from the raw pixel data
                img = Image.frombytes(mode, (width, height), SRAMarray)
                # Save the image to a file
                timeNow=time.localtime()
                timeStamp=(f'{timeNow[3]}_{timeNow[4]}_{timeNow[5]}_')
                img.save('Data\\' + timeStamp+'SRAM.png')
                return(True, [0,0,0], 'SRAM readout OK')
            else:
                return (False, [99,99,99], 'No Arduino')

        ################################
        # Check the FPGA
        elif Seq == 5:
            if self.Inst['use FPGA']: 
                print('Checking FPGA')
                try:
                    Errs=self.fpga.FPGA_errReadBack()
                except:
                    return (False, [99,99,99], 'FPGA read failed')
                if not Errs[0]:
                    print(f'Reply failed: {Errs}')             
                DUTstatus=f'FPGA errors: {Errs[1][0]}, Set: {Errs[1][1]}, Reset: {Errs[1][2]}'
                self.reportDUTstatus(DUTstatus)
                return(True, Errs[1], 'FPGA check OK')
            else:
                return (False, [99,99,99], 'No FPGA')
            
        ################################
        # Readout a scope measurement
        # elif Seq==6:
        #     if self.Inst['use Scope']: 
        #         try:
        #             reply=self.sc.scopeMeasV(self.scopeChannel)
        #             if reply[0]:
        #                 #print(f'Scope read {reply[1]}')
                        
        #                 return (True, [0,0,0], reply[1])
        #             else:
        #                 #print('Scope read error {reply}')
        #                 return (False, [99,99,99], f'Scope read error {reply}')
        #         except:
        #             return (False, [99,99,99], '"Scope measure" command failed')
            
        ################################
        # Grab the scope trace
        elif Seq==6:
            if self.Inst['use Scope']: 
                try:
                    reply=self.sc.scopeGrab(self.scopeChannel)
                except:
                    return (False, [99,99,99], '"Scope grab" command failed')
                [scaled_waveform,time_axis]=reply[1]
                timeNow=time.localtime()
                timeStamp=(f'{timeNow[3]}_{timeNow[4]}_{timeNow[5]}_')
                scopeFile='Data\\' + timeStamp + '_scope_data.csv'
                with open(scopeFile, 'w', newline='') as csvfile:
                    scopeWriter = csv.writer(csvfile, delimiter=',',
                                            quotechar='|', quoting=csv.QUOTE_MINIMAL)
                    for row in range(len(time_axis)):
                    #scopeWriter.writerows(f'{time_axis} , {scaled_waveform}')
                        scopeWriter.writerow([time_axis[row], scaled_waveform[row]])
                csvfile.close()
                return(True, [0,0,0], 'Scope grab OK')
            else:
                return (False, [99,99,99], 'No Scope')
            
        else:
            return (False, [99,99,99], 'Unknown sequence')

    def closeSequencer(self):
        self.outFile.close()
        return (True, [99,99,99], 'Closed OK')
        
 