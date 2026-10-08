# Optional: the Chapter 1 Arduino on a USB cable, running Chapter 3's robot_brain.ino.
# The box sends it the same one-letter messages the MacBook did:
#   F = I see a face    N = nobody there    r, p, s = rock, paper, scissors

import glob
import time

PORT_PATTERNS = ["/dev/cu.usbmodem*", "/dev/cu.usbserial*", "/dev/cu.wchusbserial*",   # Mac
                 "/dev/ttyACM*", "/dev/ttyUSB*"]                                        # Raspberry Pi


def find_port(look=glob.glob):
    for pattern in PORT_PATTERNS:
        ports = sorted(look(pattern))
        if ports:
            return ports[0]
    return None


class Arduino:
    def __init__(self, open_port=None, look=glob.glob, sleep=time.sleep, log=print):
        port = find_port(look)
        if port is None:
            raise SystemExit("No Arduino found. Is the USB cable plugged in?")
        if open_port is None:
            import serial                 # only needed when an Arduino is used
            open_port = lambda name: serial.Serial(name, 9600)
        try:
            self.link = open_port(port)
        except OSError:
            raise SystemExit("The Arduino is busy. Close the Serial Monitor, then try again.")
        log(f"Connected to the Arduino on {port}")
        sleep(2)                          # the Arduino restarts when we connect, so give it a moment

    def send(self, letter):
        """Sends one message, like "r" or "N"."""
        try:
            self.link.write(letter.encode())
        except OSError:
            pass                          # cable pulled out mid-game: keep playing

    def close(self):
        self.send("N")                    # leave the robot in its waiting screen
        self.link.close()
