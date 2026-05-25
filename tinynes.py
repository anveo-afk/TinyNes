#!/usr/bin/env python3


import os
import sys
import time
from typing import Any

import RPi.GPIO as GPIO
import subprocess
import syslog
import re
from enum import Enum
from datetime import datetime

import ndef
from pn532pi import Pn532, pn532
from pn532pi import Pn532Spi

IS_DEBUG = True
CONTROLLER_MACS = []  #["AA:BB:CC:DD:EE:FF"]


def _dbg_write(msg: str) -> None:
    if IS_DEBUG:
        print(msg)


def _logMsg(msg: str) -> None:
    if IS_DEBUG:
        print(msg)
    syslog.syslog(syslog.LOG_WARNING, msg)
def _log_exception(inst:Exception)->None:
    _logMsg(str(inst))


class TinyNesGameRunner:
    def __init__(self):
        self.startedOnce = False
        self.runningChild = None

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

    def SetRunningGame(self, commandArgs) -> bool:
        #there is a race condition if the user manages to stick in a game and hit reset really fast before the first game launch
        #or just hits the reset button twice really, really fast
        #could be fixed with a lock, but really, if the user plays stupid games they can win stupid prizes
        self.startedOnce = True  #startedOnce indicates we tried, not necessarily succeeded
        rc = self.runningChild
        self.runningChild = None
        if rc != None:
            TinyNesGameRunner.KillGame(rc)
            rc = None
        if commandArgs != None:  #None means kill running game and just show background
            try:
                rc = subprocess.Popen(commandArgs)
            except Exception as inst:
                _log_exception(inst)
        if rc != None:
            self.runningChild = rc
            return True
        return False


class NfcStatus(Enum):
    VALID_NO_DATA = 0
    VALID_DATA = 1
    ERROR = 2


class TinyNesNfcHandler:
    @staticmethod
    def DisposeNfc(nfc):
        pass  #sample doesn't have any cleanup code

    @staticmethod
    def GetNfc():
        nfc=None
        try:
            PN532_SPI = Pn532Spi(Pn532Spi.SS0_GPIO8)
            nfc = Pn532(PN532_SPI)
            nfc.begin()
            versiondata = nfc.getFirmwareVersion()  #dbg print
            if versiondata is not None:
                msg = "Found chip PN5 {:#x} Firmware ver. {:d}.{:d}".format((versiondata >> 24) & 0xFF,
                                                                            (versiondata >> 16) & 0xFF,
                                                                            (versiondata >> 8) & 0xFF)
                _dbg_write(msg)
                nfc.SAMConfig()
                return nfc
            _dbg_write("No pn532 firmware version found")
        except Exception as inst:
            _log_exception(inst)
        TinyNesNfcHandler.DisposeNfc(nfc)
        return None

    @staticmethod
    def ReadData() -> tuple[NfcStatus, bytearray]:
        rBytes = bytearray(b'')
        nfc = None
        try:
            nfc = TinyNesNfcHandler.GetNfc()
            tagPresent, uid = nfc.readPassiveTargetID(pn532.PN532_MIFARE_ISO14443A_106KBPS)
            if not tagPresent:  #one more try
                time.sleep(.1)
                tagPresent, uid = nfc.readPassiveTargetID(pn532.PN532_MIFARE_ISO14443A_106KBPS)
            if tagPresent == False:
                TinyNesNfcHandler.DisposeNfc(nfc)
                return NfcStatus.VALID_NO_DATA, rBytes
            _dbg_write(f"found tag {uid}")
            #try to read all bytes. if this causes problems, have to implement __iter__ and __next__ to only read what's needed
            #this code comes from what is labled as the ntag21x example, but all these function names are mifare ultralight. suspicious
            status, buf = nfc.mifareultralight_ReadPage(3)
            capacity = int(buf[2]) * 8
            _dbg_write("Tag capacity {:d} bytes".format(capacity))
            for i in range(4, int(capacity / 4)):
                status, buf = nfc.mifareultralight_ReadPage(i)
                rBytes.append(buf[:4])
            TinyNesNfcHandler.DisposeNfc(nfc)
            return NfcStatus.VALID_DATA, rBytes
        except Exception as inst:
            _log_exception(inst)
            TinyNesNfcHandler.DisposeNfc(nfc)
            return NfcStatus.ERROR, rBytes

    @staticmethod
    def GetUrlFromNdef(buff: bytearray) -> tuple[NfcStatus, str]:
        if buff is None:
            return NfcStatus.ERROR, ''
        try:
            decoder = ndef.message_decoder(buff)
            for rec in decoder:
                if isinstance(rec, ndef.uri.UriRecord):
                    return NfcStatus.VALID_DATA, rec.uri
            _logMsg("valid nfc data but no URIs")
            return NfcStatus.VALID_NO_DATA, ''
        except ndef.record.DecodeError:
            _logMsg("invalid nfc data")
            return NfcStatus.ERROR, ''

    @staticmethod
    def GetUrlFromNfc() -> str | None:
        sleeptime = .1
        tries_left = 3
        while tries_left > 0:
            status, buf = TinyNesNfcHandler.ReadData()
            if status == NfcStatus.VALID_NO_DATA:
                return None
            status2, uri = TinyNesNfcHandler.GetUrlFromNdef(buf)
            if status2 == NfcStatus.VALID_NO_DATA:  #retry only if there was an error
                return None
            if status2 == NfcStatus.VALID_DATA:
                return uri
            tries_left = tries_left - 1
        return None


class TinyNesEventHandler:
    runner: TinyNesGameRunner
    resetPin: int

    def __init__(self, resetPin: int = 3, romDir: str = "/var/roms", fceuxCmd: str = "/usr/games/fceux"):
        self.resetPin = resetPin
        self.romDir = romDir
        self.fceuxCmd = fceuxCmd
        self.firstPollIntervalSecs = 5
        self.runner = TinyNesGameRunner()
        self.nfcHandler = TinyNesNfcHandler()
        self.btEnableTime = None

    @staticmethod
    def parse_rom_url(url: str | None) -> tuple[None, None] | tuple[str, str | Any]:  #->(system,name)
        #would have to rewrite to handle snes
        if url is None or url == '':
            return None, None
        url_extract_re = re.compile(r'([^/?=]+)(/iframe)?$')  # "([^/?=]+)(\/iframe)?$"
        m = url_extract_re.search(url)
        if m is None:
            _logMsg(f"unable to extract rom name from url {url}")
            return None, None
        return "nes", m.group(1)

    def find_rom(self, url: str | None) -> str | None:
        system, name = TinyNesEventHandler.parse_rom_url(url)
        if system is None:
            return None
        ret_val = f"{self.romDir}/{system}/{name}.nes"
        if os.path.exists(ret_val):
            return ret_val
        _logMsg(f"rom {ret_val} not found on disk")
        return None

    def set_running_game_from_url(self, url: str | None):
        rom_path = self.find_rom(url)
        command_args = None if rom_path is None else [self.fceuxCmd, rom_path]
        self.connect_bt_controllers()
        self.runner.SetRunningGame(command_args)

    def start_bluetooth(self):
        try:
            args = ["/bin/bash", "-c", "echo 'power on'|/usr/bin/bluetoothctl"]
            self.btEnableTime = datetime.now()
            subprocess.run(args, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        except Exception as inst:
            _log_exception(inst)

    def connect_bt_controllers(self):
        try:
            if self.btEnableTime is not None:
                diff = (datetime.now() - self.btEnableTime).total_seconds()
                min_secs = 2
                if diff < min_secs:
                    time.sleep(min_secs - diff)
            for m in CONTROLLER_MACS:
                msg = f"connect {m}\\nquit"
                args = ["/bin/bash", "-c", f"echo -e \"{msg}\"|/usr/bin/bluetoothctl"]
                subprocess.run(args, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        except Exception as inst:
            _log_exception(inst)

    def poll_for_first_game(self):
        while not self.runner.startedOnce:
            url = self.nfcHandler.GetUrlFromNfc()
            if url is None:
                time.sleep(self.firstPollIntervalSecs)
            else:
                self.set_running_game_from_url(url)

    def hookup_event(self, func):
        GPIO.setwarnings(False)
        GPIO.setmode(GPIO.BOARD)
        GPIO.setup(self.resetPin, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
        GPIO.add_event_detect(self.resetPin, GPIO.RISING, callback=func)

    def reset_button_event_handler(self):
        url = self.nfcHandler.GetUrlFromNfc()
        self.set_running_game_from_url(url)  #if no url found, exit game

    def hookup_reset_button_event(self):
        self.hookup_event(self.reset_button_event_handler)

    @staticmethod
    def dbg_write_event_handler():
        _dbg_write("button pressed")

    def dbg_nfc_event_handler(self):
        url = self.nfcHandler.GetUrlFromNfc()
        _dbg_write(f"NFC url: {url}")
        rom_path = self.find_rom(url)
        _dbg_write(f"rom: {rom_path}")


if __name__ == "__main__":
    testcard = False
    test_button = False
    for v in sys.argv[1:]:
        if v == '-?' or v == '-h':
            sys.exit("tinynes.py: -c test card reader, -b test button")
        elif v == '-c':
            testcard = True
        elif v == '-b':
            test_button = True

    handler = TinyNesEventHandler()
    handler.start_bluetooth()

    if test_button:
        handler.hookup_event(handler.dbg_write_event_handler)
        print("press button, ctrl-C to exit")
    elif testcard:
        handler.hookup_event(handler.dbg_nfc_event_handler)
        print("press button, ctrl-C to exit")

    else:
        handler.hookup_reset_button_event()
        handler.poll_for_first_game()
