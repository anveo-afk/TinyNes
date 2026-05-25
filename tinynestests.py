#!/usr/bin/env python3
import sys
from unittest import TestCase
from unittest.mock import MagicMock, patch

class TinyNesTests(TestCase):
    def test_ParseRomUrl(self):
        with patch.dict('sys.modules',{
            "RPi":MagicMock(),
            "RPi.GPIO":MagicMock()
            }):
            from tinynes import TinyNesEventHandler
            url="https://retromania.gg/games/nes/battletoads"
            system,name=TinyNesEventHandler.parse_rom_url(url)
            self.assertEqual(system,"nes")
            self.assertEqual(name,"battletoads")
            url="https://retromania.gg/games/nes/battletoads/iframe"
            system,name=TinyNesEventHandler.parse_rom_url(url)
            self.assertEqual(system,"nes")
            self.assertEqual(name,"battletoads")
            url="https://somesite.com/nes/play?game=battletoads"
            system,name=TinyNesEventHandler.parse_rom_url(url)
            self.assertEqual(system,"nes")
            self.assertEqual(name,"battletoads")
    def test_GetUrlFromNdef(self):
        with patch.dict('sys.modules',{
            "RPi":MagicMock(),
            "RPi.GPIO":MagicMock()
            }):
            from tinynes import TinyNesNfcHandler, NfcStatus
            data=None
            status,uri=TinyNesNfcHandler.GetUrlFromNdef(data)
            self.assertEqual(NfcStatus.ERROR,status)
            data=bytearray.fromhex('9101085402656e48656c6c6f5101085402656e576f726c64');#nedeflib example text records
            status,uri=TinyNesNfcHandler.GetUrlFromNdef(data)
            self.assertEqual(NfcStatus.VALID_NO_DATA,status)
            data=b'\xd1\x01$U\x04retromania.gg/games/nes/battletoads'
            status,uri=TinyNesNfcHandler.GetUrlFromNdef(data)
            self.assertEqual(NfcStatus.VALID_DATA,status)
            self.assertEqual("https://retromania.gg/games/nes/battletoads",uri)
            data=b'garbage'
            status,uril=TinyNesNfcHandler.GetUrlFromNdef(data)
            self.assertEqual(NfcStatus.ERROR,status)
        

if __name__ == '__main__':
    unittest.main()
