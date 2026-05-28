import time

from TinyNesNfcHandlerBase import TinyNesNfcHandlerBase,NfcStatus
from pn532pi import Pn532Spi, Pn532
from pn532pi.nfc import pn532
from TinyNesLogger import TinyNesLogger




class TinyNesPn532PiNfcHandler(TinyNesNfcHandlerBase):
    @staticmethod
    def _dispose_nfc(nfc):
        pass  #sample doesn't have any cleanup code
    @staticmethod
    def _get_nfc():
        nfc=None
        try:
            PN532_SPI = Pn532Spi(Pn532Spi.SS1_GPIO7)
            nfc = Pn532(PN532_SPI)
            nfc.begin()
            version_data = nfc.getFirmwareVersion()  #dbg print
            if version_data is not None and version_data!=0:
                msg = "Found chip PN5 {:#x} Firmware ver. {:d}.{:d}".format((version_data >> 24) & 0xFF,
                                                                            (version_data >> 16) & 0xFF,
                                                                            (version_data >> 8) & 0xFF)
                TinyNesLogger.dbg_write(msg)
                nfc.SAMConfig()
                return nfc
            TinyNesLogger.dbg_write("No pn532 firmware version found")
        except Exception as inst:
            TinyNesLogger.log_exception(inst)
        TinyNesPn532PiNfcHandler._dispose_nfc(nfc)
        return None

    def read_data(self) -> tuple[NfcStatus, bytearray]:
        r_bytes = bytearray(b'')
        nfc = None
        try:
            nfc = TinyNesPn532PiNfcHandler._get_nfc()

            tag_present, uid = nfc.readPassiveTargetID(pn532.PN532_MIFARE_ISO14443A_106KBPS)
            if not tag_present:  #one more try
                time.sleep(.1)
                tag_present, uid = nfc.readPassiveTargetID(pn532.PN532_MIFARE_ISO14443A_106KBPS)
            if not tag_present:
                TinyNesPn532PiNfcHandler._dispose_nfc(nfc)
                return NfcStatus.VALID_NO_DATA, r_bytes
            TinyNesLogger.dbg_write(f"found tag {uid}")
            #try to read all bytes. if this causes problems, have to implement __iter__ and __next__ to only read what's needed
            #this code comes from what is labeled as the ntag21x example, but all these function names are mifare ultralight. suspicious
            status, buf = nfc.mifareultralight_ReadPage(3)
            capacity = int(buf[2]) * 8
            TinyNesLogger.dbg_write("Tag capacity {:d} bytes".format(capacity))
            for i in range(4, int(capacity / 4)):
                status, buf = nfc.mifareultralight_ReadPage(i)
                r_bytes.append(buf[:4])
            TinyNesPn532PiNfcHandler._dispose_nfc(nfc)
            return NfcStatus.VALID_DATA, r_bytes
        except Exception as inst:
            TinyNesLogger.log_exception(inst)
            TinyNesPn532PiNfcHandler._dispose_nfc(nfc)
            return NfcStatus.ERROR, r_bytes
