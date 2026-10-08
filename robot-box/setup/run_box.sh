#!/bin/bash
# Starts the Robot Box, and starts it again if it ever crashes.
# The autostart uses this. Anything after the name is passed on to box.py, like:  --app rps
cd "$(dirname "$0")/.." || exit 1
mkdir -p data
while true; do
    # A clean quit (the Q key) stays quit. A crash waits 3 seconds and tries again.
    .venv/bin/python box.py "$@" > data/last-run.log 2>&1 && break
    sleep 3
done
