import time
from abc import ABCMeta, abstractmethod
from enum import Enum

import ndef
from TinyNesLogger import TinyNesLogger

class NfcStatus(Enum):
    VALID_NO_DATA = 0
    VALID_DATA = 1
    ERROR = 2


class TinyNesNfcHandlerBase(metaclass=ABCMeta):
    @staticmethod
    def get_url_from_ndef(buff: bytearray) -> tuple[NfcStatus, str]:
        if buff is None:
            return NfcStatus.ERROR, ''
        try:
            decoder = ndef.message_decoder(buff)
            for rec in decoder:
                if isinstance(rec, ndef.uri.UriRecord):
                    return NfcStatus.VALID_DATA, rec.uri
            TinyNesLogger.log_msg("valid nfc data but no URIs")
            return NfcStatus.VALID_NO_DATA, ''
        except ndef.record.DecodeError:
            TinyNesLogger.log_msg("invalid nfc data")
            return NfcStatus.ERROR, ''

    @abstractmethod
    def read_data(self)-> tuple[NfcStatus, bytearray]:
        pass

    def get_url_from_nfc(self) -> str | None:
        sleeptime = .1
        tries_left = 3
        while tries_left > 0:
            status, buf = self.read_data()
            if status == NfcStatus.VALID_NO_DATA:
                return None
            status2, uri = TinyNesNfcHandlerBase.get_url_from_ndef(buf)
            if status2 == NfcStatus.VALID_NO_DATA:
                #even if read_data threw an error, we got enough for a valid ndef, and it had no uri
                return None
            if status2 == NfcStatus.VALID_DATA:
                return uri
            tries_left = tries_left - 1
            time.sleep(sleeptime)
        return None
