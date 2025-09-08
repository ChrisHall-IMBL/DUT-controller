# -*- coding: utf-8 -*-
"""
Created on Wed Aug 27 12:34:18 2025

@author: imbl
"""
from epics import caget
import time
from PIL import Image
import ArduinoFuncs as Ar
import Scope as sc

##### Sequence functions ######
    
def RunThis(Seq):
    global IC_PV
    global Shutter_PV
    global serKeithley
    global serArduino
    global outFile
    global scopeChannel
    
    def ReadKeithley(channel, ser):
            command=f'INST:NSEL {channel+1}\n'
            ser.write(command.encode())  # Send command
            # command='MEAS:VOLT?\n'
            # ser.write(command.encode())  # Send command
            # voltsS = ser.readline().decode()  # read response
            # voltsF=float(voltsS)
            command='MEAS:CURR?\n'
            ser.write(command.encode())  # Send command
            currS = ser.readline().decode()  # read response
            currF=float(currS)
            # print(voltsF,' V ',currF,' A')
            return currF
  
    def reportDUTstatus(DUTstatus): 
        timeNow=time.asctime(time.localtime()) # String version of the time.
        try:
            IC=float(caget(IC_PV))
            SHT='OPEN' if caget(Shutter_PV + 'SHUTTEROPEN_MONITOR') else 'CLOSED'
        except:
            SHT='Failed'
        try:
            voltS=scope.query(':MEASURE:VMAX?')
            voltF = float( voltS)
        except:
            voltF=999.999
        try:
            Pcurr=ReadKeithley(3,serKeithley)
        except:
            Pcurr=999.999
        
        outRow=DUTstatus + ', ' ' shutter is:' + SHT \
           + f', DUT current is: {voltF:.2f}' \
           + f', IC current is {IC:.2f}'  \
           + f',  PSU current is {Pcurr:.4f} A'    
        print(outRow)
        outFile.write(timeNow + ': ' + outRow + '\n')

    # Write a pattern A
    if Seq == 0:
        # print('Starting sequence')
        if not Ar.Arduino_command(serArduino,b'WA'):
            print ('Write A command failed')

    ################################
    # Fault check pattern A
    elif Seq == 1:
        print('Requesting fault check pattern A')
        if not Ar.Arduino_command(serArduino,b'FA'):
            print ('Fault A command failed')
        Errs=Ar.Arduino_errReadBack(serArduino)
        if not len(Errs) == 3:
            print(f'Reply failed: {Errs}')
        DUTstatus=f'Total errors: {Errs[0]}, Set: {Errs[1]}, Reset: {Errs[2]}'
        reportDUTstatus(DUTstatus)
    
    ###############################
    # Write a pattern B
    elif Seq == 2: 
    #     print('Requesting write pattern B')
        if not Ar.Arduino_command(serArduino,b'WB'):
            print ('Write command failed')
    
    ################################
    # Fault check pattern B
    elif Seq == 3:
        print('Requesting fault check pattern B')
        if not Ar.Arduino_command(serArduino,b'FB'):
            print ('Fault B command failed')
        Errs=Ar.Arduino_errReadBack(serArduino)
        if not len(Errs) == 3:
            print(f'Reply failed: {Errs}')
        DUTstatus=f'Total errors: {Errs[0]}, Set: {Errs[1]}, Reset: {Errs[2]}'
        reportDUTstatus(DUTstatus)
        
    ################################
    elif Seq == 4:
        print('Requesting read')
        if not Ar.Arduino_command(serArduino,b'R'):
              print ('Command failed')
        SRAMarray=Ar.Arduino_ReadSRAM()
        width, height = 256, 256
        mode = "L"  # "L" for grayscale
        # Create an Image object from the raw pixel data
        img = Image.frombytes(mode, (width, height), SRAMarray)
        # Save the image to a file
        timeNow=time.localtime()
        timeStamp=(f'{timeNow[3]}_{timeNow[4]}_{timeNow[5]}_')
        img.save(timeStamp+'SRAM.png')
        
    elif Seq==5:
        wave=sc.scopeGrab(scope, scopeChannel)
        # plt.plot(wave)
        
 