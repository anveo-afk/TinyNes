import os
import re
import subprocess
import time
from datetime import datetime
from threading import Event

from RPi import GPIO as GPIO

from TinyNesGameRunner import TinyNesGameRunner
from TinyNesLogger import TinyNesLogger
from TinyNesWaveshareLibNfcHandler import TinyNesWaveshareLibNfcHandler
from typing import Any

CONTROLLER_MACS = ["71:C5:7A:62:82:1C"]

class TinyNesEventHandler:
    fceuxCmd: str
    runner: TinyNesGameRunner
    resetPin: int

    def __init__(self, resetPin: int = 11, romDir: str = "/var/roms", fceuxCmd: str = "/usr/games/fceux"):
        self.resetPin = resetPin
        self.romDir = romDir
        self.fceuxCmd = fceuxCmd
        self.firstPollIntervalSecs = 5
        self.runner = TinyNesGameRunner()
        self.nfcHandler = TinyNesWaveshareLibNfcHandler()
        self.btEnableTime = None

    @staticmethod
    def parse_rom_url(url: str | None) -> tuple[None, None] | tuple[str, str | Any]:  #->(system,name)
        #would have to rewrite to handle snes
        if url is None or url == '':
            return None, None
        url_extract_re = re.compile(r'([^/?=]+)(/iframe)?$')  # "([^/?=]+)(\/iframe)?$"
        m = url_extract_re.search(url)
        if m is None:
            TinyNesLogger.log_msg(f"unable to extract rom name from url {url}")
            return None, None
        return "nes", m.group(1)

    def find_rom(self, url: str | None) -> str | None:
        system, name = TinyNesEventHandler.parse_rom_url(url)
        if system is None:
            return None
        ret_val = f"{self.romDir}/{system}/{name}.nes"
        if os.path.exists(ret_val):
            return ret_val
        TinyNesLogger.log_msg(f"rom {ret_val} not found on disk")
        return None

    @staticmethod
    def do_fceux_replace(contents:str)->str:
        return re.sub(r"SDL\.Fullscreen\s*=\s*0","SDL.Fullscreen = 1",contents)
    @staticmethod
    def set_fceux_config_fullscreen()->None:
        #fceux sets fullscreen off in the config file at exit
        #so set it back on before starting
        try:
            with open("~/.fceux/fceux.cfg") as f:
                data=f.readlines()
                data=TinyNesEventHandler.do_fceux_replace(data)
                f.seek(0)
                f.write(data)
                f.truncate()
        except FileNotFoundError:
            TinyNesLogger.log_msg("fceux.cfg not found")
        except Exception as inst:
            TinyNesLogger.log_exception(inst)
    def set_running_game_from_url(self, url: str | None):
        self.connect_bt_controllers()
        rom_path = self.find_rom(url)
        if rom_path is None:
            self.runner.SetRunningGame(None)
        self.set_fceux_config_fullscreen()
        command_args = [self.fceuxCmd, rom_path]
        self.runner.SetRunningGame(command_args)

    def start_bluetooth(self):
        try:
            args = ["/bin/bash", "-c", "echo 'power on'|/usr/bin/bluetoothctl"]
            self.btEnableTime = datetime.now()
            subprocess.run(args, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        except Exception as inst:
            TinyNesLogger.log_exception(inst)

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
            TinyNesLogger.log_exception(inst)

    def poll_for_first_game(self):
        while not self.runner.startedOnce:
            url = self.nfcHandler.get_url_from_nfc()
            if url is None:
                time.sleep(self.firstPollIntervalSecs)
            else:
                self.set_running_game_from_url(url)

    def hookup_event(self, func):
        GPIO.setwarnings(False)
        GPIO.setmode(GPIO.BOARD)
        GPIO.setup(self.resetPin, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
        GPIO.add_event_detect(self.resetPin, GPIO.RISING, callback=func,bouncetime=300)
    def hookup_reset_button_event_handler(self):
        def hdlr(i:int):
            url = self.nfcHandler.get_url_from_nfc()
            self.set_running_game_from_url(url)  # if no url found, exit game
        self.hookup_event(hdlr)
    def hookup_dbg_button_event_handler(self):
        def hdlr(i:int):
            TinyNesLogger.dbg_write("button pressed")
        self.hookup_event(hdlr)
    def hookup_dbg_nfc_event_handler(self):
        def hdlr(i:int):
            url = self.nfcHandler.get_url_from_nfc()
            TinyNesLogger.dbg_write(f"NFC url: {url}")
            rom_path = self.find_rom(url)
            TinyNesLogger.dbg_write(f"rom: {rom_path}")
        self.hookup_event(hdlr)
    def wait_for_signal(self):
        try:
            Event().wait()
        except KeyboardInterrupt:
            pass
