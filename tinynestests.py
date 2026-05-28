#!/usr/bin/env python3
import sys
from unittest import TestCase
from unittest.mock import MagicMock, patch

class TinyNesTests(TestCase):
    def test_do_fceux_replace(self):
        with patch.dict('sys.modules',{
            "RPi":MagicMock(),
            "RPi.GPIO":MagicMock(),
            "lgpio":MagicMock(),
            }):
            from TinyNesEventHandler import TinyNesEventHandler
            str="""
            SDL.Fullscreen = 1
            SDL.Fullscreen = 0
            SDL.Fullscreen =0
            SDL.Fullscreen=0
            SDL.XXXXxxx=1
            ladfjadfa***....3adfaet            
            """
            expected="""
            SDL.Fullscreen = 1
            SDL.Fullscreen = 1
            SDL.Fullscreen = 1
            SDL.Fullscreen = 1
            SDL.XXXXxxx=1
            ladfjadfa***....3adfaet            
            """
            actual=TinyNesEventHandler.do_fceux_replace(str)
            self.assertEqual(expected,actual)
    def test_ParseRomUrl(self):
        with patch.dict('sys.modules',{
            "RPi":MagicMock(),
            "RPi.GPIO":MagicMock(),
            "lgpio":MagicMock(),
            }):
            from TinyNesEventHandler import TinyNesEventHandler
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
            from TinyNesNfcHandlerBase import NfcStatus, TinyNesNfcHandlerBase
            data=None
            status,uri=TinyNesNfcHandlerBase.get_url_from_ndef(data)
            self.assertEqual(NfcStatus.ERROR,status)
            data=bytearray.fromhex('9101085402656e48656c6c6f5101085402656e576f726c64');#nedeflib example text records
            status,uri=TinyNesNfcHandlerBase.get_url_from_ndef(data)
            self.assertEqual(NfcStatus.VALID_NO_DATA,status)
            data=b'\xd1\x01$U\x04retromania.gg/games/nes/battletoads'
            status,uri=TinyNesNfcHandlerBase.get_url_from_ndef(data)
            self.assertEqual(NfcStatus.VALID_DATA,status)
            self.assertEqual("https://retromania.gg/games/nes/battletoads",uri)
            data=b'garbage'
            status,uri=TinyNesNfcHandlerBase.get_url_from_ndef(data)
            self.assertEqual(NfcStatus.ERROR,status)
        

if __name__ == '__main__':
    unittest.main()
