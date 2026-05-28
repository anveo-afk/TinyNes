import asyncio
import time
from asyncio import Lock

from TinyNesNfcHandlerBase import TinyNesNfcHandlerBase,NfcStatus
from TinyNesLogger import TinyNesLogger
import RPi.GPIO as GPIO

import pn532.pn532 as nfc
from pn532 import *
from pn532 import PN532_SPI
from typing import Any


class TinyNesWaveshareLibNfcHandler(TinyNesNfcHandlerBase):
    saved_pn: PN532_SPI | None
    saved_pn_lock: Lock
    @staticmethod
    def _create_pn() -> PN532_SPI | None:
        pn=None
        try:
            pn = PN532_SPI(cs=4, reset=20, debug=False)
            ic, ver, rev, support = pn.get_firmware_version()
            TinyNesLogger.dbg_write(f'Found PN532 with firmware version: {ver}.{rev}')
            #detect 0.0 and bail?
            pn.SAM_configuration()
        except Exception as e:
            TinyNesLogger.log_exception(e)
            TinyNesWaveshareLibNfcHandler._dispose_pn(pn)
            pn=None
        return pn
    def _dispose_pn(self)->None:
        #we'll create a new object next time, but if we call GPIO.cleanup() we have
        #to re-register the button handler, so just hope for the best
        self.saved_pn=None
    def __init__(self):
        self.saved_pn=None
        self.saved_pn_lock=asyncio.Lock()
    async def _get_pn(self) -> PN532_SPI | None:
        pn = self.saved_pn
        if pn is None:
            async with self.saved_pn_lock:
                self.saved_pn=self._create_pn()
        return pn

    def read_data(self)-> tuple[NfcStatus, bytearray]:#try catch, getnfc method, retry loops
        r_bytes = bytearray(b'')
        pn = asyncio.run(self._get_pn())
        if pn is None:
            return NfcStatus.ERROR,r_bytes
        try:
            uid = pn.read_passive_target(timeout=0.1)  # none means no card present
            if uid is None:
                uid = pn.read_passive_target(timeout=0.1)  #try 1 more time
            if uid is None:
                return NfcStatus.VALID_NO_DATA,r_bytes
            # try to read all bytes. if this causes problems, have to implement __iter__ and __next__ to only read what's needed
            for i in range(135):
                x = pn.ntag2xx_read_block(i)
                r_bytes.append(x)
            return NfcStatus.VALID_DATA,r_bytes
        except Exception as e:
            TinyNesLogger.log_exception(e)
            self._dispose_pn()
            return NfcStatus.ERROR, r_bytes




