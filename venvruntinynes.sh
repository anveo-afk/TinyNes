#!/bin/bash

VDIR=venv

if [ ! -d "$VDIR" ] 
then
    python3 -m venv --system-site-packages "$VDIR"
    . "$VDIR/bin/activate";
    pip install pn532pi
    pip install ndeflib
else
    . "$VDIR/bin/activate";
fi 

python3 tinynes.py "$@"

deactivate
