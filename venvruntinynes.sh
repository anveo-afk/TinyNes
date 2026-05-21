#!/bin/bash

VDIR=venv

if [ ! -d "$VDIR" ] 
then
    python3 -m venv "$VDIR"
    . "$VDIR/bin/activate";
    pip install pn532pi
    pip install ndeflib
    pip install RPi.GPIO
else
    . "$VDIR/bin/activate";
fi 

python3 tinynes.py "$@"

deactivate
