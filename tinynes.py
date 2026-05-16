#!/usr/bin/env python3


import os
import shutil
import time
import RPi.GPIO as GPIO
import subprocess
import syslog

#import pn532.pn532 as nfc
#from pn532 import *


IS_DEBUG=True
def _dbgWrite(msg:str):
    if IS_DEBUG==True:
        print(msg)
def _logMsg(msg:str):
        if IS_DEBUG==True:
            print(msg)
        syslog.syslog(syslog.LOG_WARNING,msg)
    
class TinyNesGameRunner:
    def __init__(self):
        self.startedOnce=False
        self.runningChild=None
    @staticmethod
    def KillGame(popenObj):
        if popenObj == None or popenObj.poll() != None:
            return
        popenObj.terminate()
        try:
            popenObj.wait(5)
            # 5 seconds is definitely long enough for the user to notice the hang
            # but we can't very well start another emulator with the first one running
        except subprocess.TimeoutExpired:
            popenObj.kill()
    def SetRunningGame(self,commandArgs)->bool:
        #there is a race condition if the user manages to stick in a game and hit reset really fast before the first game launch
        #or just hits the reset button twice really, really fast
        #could be fixed with a lock, but really, if the user plays stupid games they can win stupid prizes
        self.startedOnce=True #startedOnce indicates we tried, not necessarily succeeded
        rc=self.runningChild
        self.runningChild=None
        if rc!=None:
            TinyNesRunner.KillGame(rc)
            rc=None
        if commandArgs != None: #None means kill running game and just show background
            try:
                rc=subprocess.Popen(commandArgs)
            except Exception as inst:
                _logMsg(inst)
        if rc!=None:
            self.runningChild=rc
            return True
        return False
        
class TinyNesNfcHandler:
    def GetNdefFromNfc(self)->bytearray|None:
        #TODO: all of it
        #static?
        #catch exceptions, cleanup and return None
        #TODO: create and cleanup every time we need it to prevent power failures
        #pn532 = PN532_SPI(cs=4, reset=20, debug=False) 
        #uid = pn532.read_passive_target(timeout=0.5)
        #if uid is None:
        #    return None
        
        #return '9101085402656e48656c6c6f5101085402656e576f726c64' ndeflib example, text records
        return bytearray.fromhex('d1010000021555016578616d706c652e636f6d2f70617468') #uri
    @staticmethod
    def GetUrlFromNdef(ndef:bytearray)->str|None:
        if ndef is None:
            return None
        #trim
        #nfc but no url element log message
        return None
    def GetUrlFromNfc()->str|None:
        #static?        
        ndef=self.GetNdefFromNfc()
        return TinyNesNfcHandler.GetUrlFromNdef(ndef)
            
    

class TinyNesEventHandler:
    def __init__(self,resetPin: str=3,romDir: str="/var/roms",fceuxCmd: str="/usr/games/fceux"):
        self.resetPin=resetPin
        self.romDir=romDir
        self.fceuxCmd=fceuxCmd
        self.isDebug=True
        self.firstPollIntervalSecs=5
        self.runner=TinyNesGameRunner()        
        self.nfcHandler=TinyNesNfcHandler()
    @staticmethod
    def ParseRomUrl(url:str):#->(system,name)
        #would have to rewrite to handle snes
        if url == None or url == '':
            return (None,None)
        urlExtractRe=re.compile("([^/?=]+)(/iframe)?$") 
        m=urlExtractRe.match(url)
        if m==None:
            _logMsg(f"unable to extract rom name from url {url}")
            return (None,None)
        return ("nes",m.group(1))        
    def FindRom(self,url:str)->str:
        system,name=TinyNesEventHandler.ParseRomUrl(url)
        if system is None:
            return None
        retVal=f"{self.romDir}/{system}/{name}.nes"
        if os.path.exists(retVal):
            return retVal
        _logMsg(f"rom {retVal} not found on disk")
        return None
    def SetRunningGameFromUrl(self,url: str):
        romPath=self.FindRom(url)
        commandArgs= None if romPath is None else [self.fceuxCmd,romPath]
        runner.SetRunningGame(commandArgs)
    def PollForFirstGame(self):
        while runner.startedOnce==False:
            url=self.nfcHandler.GetUrlFromNfc()
            if url is None:
                time.sleep(self.firstPollIntervalSecs)
            else:
                self.SetRunningGameFromUrl(url)
    def HookupEvent(self,func):
        GPIO.setwarnings(False) 
        GPIO.setmode(GPIO.BOARD) 
        GPIO.setup(self.resetPin, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
        GPIO.add_event_detect(pin,GPIO.RISING,callback=func)
    def ResetButtonEventHandler(self):    
        url=self.nfcHandler.GetUrlFromNfc()
        SetRunningGameFromUrl(url)#if no url found, exit game
    def HookupResetButtonEvent(self):
        self.HookupEvent(self.ResetButtonEventHandler)
    def DbgWriteEventHandler(self):
        _dbgWrite("button pressed")
    def DbgNfcEventHandler(self):
        url=self.GetUrlFromNfc()
        _dbgWrite(f"NFC url: {url}")
        romPath=FindRom(url)
        _dbgWrite(f"rom: {romPath}")



if __name__ == "__main__":
    handler=TinyNesEventHandler()

    #testing order:
    handler.HookupEvent(handler.DbgWriteEventHandler)
    #handler.HookupEvent(handler.DbgNfcEventHandler)

    #real code:
    #handler.HookupResetButtonEvent()
    #handler.PollForFirstGame()


 
    
