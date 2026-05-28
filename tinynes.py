#!/usr/bin/env python3


import sys

from TinyNesEventHandler import TinyNesEventHandler


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
        handler.hookup_dbg_button_event_handler()
        print("press button to test it. Ctrl-C to exit")
    elif testcard:
        handler.hookup_dbg_button_event_handler()
        print("press button to test reader. Ctrl-C to exit")
    else:
        handler.poll_for_first_game()
        handler.hookup_reset_button_event_handler()
    handler.wait_for_signal()
