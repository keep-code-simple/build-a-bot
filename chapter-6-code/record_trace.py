#!/usr/bin/env python3
"""Chapter 6: Dino Bot - record what the eyes really see.

Saves the live light readings from the light_check sketch as a CSV file,
so the robot's brain can be tested on YOUR screen again and again without
playing the game each time. Record once, test forever.

How to use it:
  1. Upload light_check to the UNO. Close the Serial Monitor and the
     Serial Plotter (only one program can listen to the UNO at a time).
  2. One-time setup, in the Terminal:
         python3 -m venv ~/dino-venv
         ~/dino-venv/bin/pip install pyserial
  3. Start the game, then record 30 seconds of it:
         ~/dino-venv/bin/python record_trace.py --seconds 30 > tests/traces/my_screen.csv
     (Leave out --seconds to record until you press Ctrl+C.)
  4. See what each brain level would have done with it:
         /tmp/replay_test --replay tests/traces/my_screen.csv

The file looks like this (one row every 5 ms):
    ms,a0,a1,a2
    0,812,799,805
"""
import argparse
import sys
import time

SAMPLE_MS = 5        # must match SAMPLE_MS in light_check.ino
BAUD = 115200        # must match Serial.begin() in light_check.ino


def find_port():
    """Guess which serial port the UNO is on."""
    from serial.tools import list_ports
    ports = list(list_ports.comports())
    for port in ports:
        text = (port.device + " " + (port.description or "")).lower()
        if "usbmodem" in text or "usbserial" in text or "arduino" in text or "ch340" in text:
            return port.device
    return ports[0].device if ports else None


def parse_line(line):
    """Turn 'A0:812,A1:799,A2:805' into [812, 799, 805]. Returns None for a broken line."""
    values = []
    for part in line.strip().split(","):
        name, colon, number = part.partition(":")
        if not colon or not number.strip().isdigit():
            return None
        values.append(int(number))
    return values if len(values) == 3 else None


def main():
    parser = argparse.ArgumentParser(description="Record light_check readings as CSV.")
    parser.add_argument("--port", help="serial port, for example /dev/cu.usbmodem1101 (default: guess)")
    parser.add_argument("--seconds", type=float, default=0, help="stop after this many seconds (default: until Ctrl+C)")
    args = parser.parse_args()

    try:
        import serial
    except ImportError:
        sys.exit("This needs the pyserial package. See step 2 at the top of this file.")

    port = args.port or find_port()
    if not port:
        sys.exit("No serial port found. Is the UNO plugged in?")
    print("Recording from", port, "- press Ctrl+C to stop.", file=sys.stderr)

    rows = 0
    with serial.Serial(port, BAUD, timeout=1) as uno:
        time.sleep(2)                 # opening the port restarts the UNO: give it a moment
        uno.reset_input_buffer()
        uno.readline()                # the first line may be cut in half: throw it away
        print("ms,a0,a1,a2")
        started = time.monotonic()
        try:
            while not args.seconds or time.monotonic() - started < args.seconds:
                values = parse_line(uno.readline().decode("ascii", "ignore"))
                if values is None:
                    continue
                # light_check sends one line every SAMPLE_MS, so the row number tells the time.
                print("%d,%d,%d,%d" % (rows * SAMPLE_MS, values[0], values[1], values[2]))
                rows += 1
        except KeyboardInterrupt:
            pass
    print("Saved %d rows (%.1f seconds)." % (rows, rows * SAMPLE_MS / 1000.0), file=sys.stderr)


if __name__ == "__main__":
    main()
