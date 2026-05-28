#!/usr/bin/env python3


import os
import sys
import time
from typing import Any

import RPi.GPIO as GPIO

def callback(channel:int)->None:
    print(f"pushed {channel}")

GPIO.setwarnings(True)
GPIO.setmode(GPIO.BOARD)
for p in range(0,26):
    try:
        GPIO.setup(p, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
        GPIO.add_event_detect(self.resetPin, GPIO.RISING, callback=callback)
    except Exception as e:
        print(e)