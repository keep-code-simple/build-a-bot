# The USB link to the Arduino.
# Only ONE program at a time can use the USB cable, so every script talks through this file.
# One thread owns the cable: it sends the notes waiting in the outbox and reads the answers.
# If the cable is pulled out, it keeps trying until it is plugged back in.

import glob
import queue
import threading
import time

from . import protocol

BAUD = 9600


def find_port():
    """Look for the Arduino's USB port, the same way Chapter 3 does."""
    ports = (glob.glob("/dev/cu.usbmodem*") + glob.glob("/dev/cu.usbserial*")
             + glob.glob("/dev/cu.wchusbserial*"))
    return ports[0] if ports else None


class FakeArduino:
    """A pretend Arduino that lives inside the Mac, for trying things with no robot plugged in.

    It answers every note the way robot_bridge.ino does.
    """

    def __init__(self, visitor_every=0):
        self.replies = queue.Queue()
        self.visitors = 0
        self.screen = ("Talking Robot ON", "Visitors: 0")
        self.visitor_every = visitor_every      # seconds between pretend visitors (0 = never)
        self.next_visitor = time.monotonic() + visitor_every
        self.leave_at = None
        self.replies.put("READY")

    def write(self, data):
        for line in data.decode("ascii", "replace").splitlines():
            if line.strip():
                self.replies.put(self.answer(line.strip()))

    def readline(self):
        self._pretend_visitors()
        try:
            return (self.replies.get(timeout=0.05) + "\n").encode("ascii")
        except queue.Empty:
            return b""

    def close(self):
        pass

    def visitor(self):
        """Pretend somebody walked up."""
        self.visitors += 1
        self.replies.put(f"EVENT VISITOR {self.visitors}")

    def left(self):
        self.replies.put("EVENT LEFT")

    def _pretend_visitors(self):
        now = time.monotonic()
        if self.leave_at and now >= self.leave_at:
            self.leave_at = None
            self.left()
        if self.visitor_every and now >= self.next_visitor:
            self.next_visitor = now + self.visitor_every
            self.leave_at = now + 3
            self.visitor()

    def answer(self, line):
        if len(line) > protocol.MAX_LINE:
            return "ERR TOO_LONG"
        verb, _, rest = line.partition(" ")
        verb = verb.upper()
        rest = rest.strip()
        numbers = [int(word) if word.isdigit() else -1 for word in rest.split()]

        if verb == "PING":
            return "PONG"
        if verb == "SHOW":
            line1, _, line2 = rest.partition("|")
            self.screen = (line1[:16], line2[:16])
            return "OK SHOW"
        if verb == "BEEP":
            good = len(numbers) == 2 and 100 <= numbers[0] <= 5000 and 10 <= numbers[1] <= 2000
            return "OK BEEP" if good else "ERR RANGE"
        if verb == "TUNE":
            return "OK TUNE" if rest.upper() in protocol.TUNES else "ERR UNKNOWN"
        if verb == "NOTES":
            good = 1 <= len(numbers) <= 8 and all(100 <= hz <= 5000 for hz in numbers)
            return "OK NOTES" if good else "ERR RANGE"
        if verb == "LED":
            return "OK LED" if rest.upper() in protocol.LED_MODES else "ERR UNKNOWN"
        if verb == "PLAY":
            good = len(numbers) == 1 and 1 <= numbers[0] <= 9999
            return "ERR NO_PLAYER" if good else "ERR RANGE"
        if verb == "IDLE":
            self.screen = ("Talking Robot ON", f"Visitors: {self.visitors}")
            return "OK IDLE"
        return "ERR UNKNOWN"


class ArduinoLink:
    """Sends notes to the Arduino and hands every answer to on_message."""

    def __init__(self, on_message=None, fake=None, port=None, log=print):
        self.on_message = on_message or (lambda message: None)
        self.fake = fake                  # a FakeArduino, or None for the real one
        self.port = port
        self.log = log
        self.outbox = queue.Queue()
        self.ready = threading.Event()    # set when the Arduino says READY
        self.stopping = threading.Event()
        self.connected = False
        self.thread = threading.Thread(target=self._run, daemon=True)

    def start(self):
        self.thread.start()
        return self

    def send(self, line):
        """Put a note in the outbox. The link thread posts it."""
        if self.connected:                # no cable, no note (old notes would be confusing later)
            self.outbox.put(line)

    def wait_until_ready(self, seconds=6):
        return self.ready.wait(seconds)

    def stop(self):
        self.stopping.set()
        if self.thread.is_alive():
            self.thread.join(timeout=2)

    # ---- everything below runs on the link thread ----

    def _open(self):
        if self.fake:
            return self.fake
        import serial                     # pyserial, the USB messenger
        port = self.port or find_port()
        if not port:
            raise OSError("no Arduino found. Is the USB cable plugged in?")
        try:
            return serial.Serial(port, BAUD, timeout=0.1)
        except serial.SerialException:
            raise OSError("the Arduino is busy. Close the Serial Monitor in the Arduino IDE.")

    def _run(self):
        complained = ""
        while not self.stopping.is_set():
            try:
                arduino = self._open()
            except OSError as problem:
                if str(problem) != complained:      # say it once, not every 2 seconds
                    complained = str(problem)
                    self.log(f"🔌 Can't reach the robot: {problem} I'll keep trying.")
                self.stopping.wait(2)
                continue

            complained = ""
            self.connected = True
            self.log("🔌 Connected to the robot" + (" (a pretend one)" if self.fake else ""))
            try:
                self._talk(arduino)
            except OSError:                         # pyserial's errors are OSErrors too
                self.log("🔌 The USB cable came out! I'll keep trying.")
            self.connected = False
            self.ready.clear()
            try:
                arduino.close()
            except OSError:
                pass
            self.stopping.wait(1)

    def _talk(self, arduino):
        opened = time.monotonic()
        while not self.stopping.is_set():
            raw = arduino.readline()                # waits a moment for an answer
            if raw:
                text = raw.decode("ascii", "replace").strip()
                if text:
                    message = protocol.parse_line(text)
                    if message["kind"] == "READY":
                        self.ready.set()
                    self.on_message(message)
            # The Arduino restarts when the Mac connects. Don't talk until it says READY
            # (or until 4 seconds have gone by, in case we missed it).
            if time.monotonic() - opened > 4:
                self.ready.set()
            while self.ready.is_set() and not self.outbox.empty():
                line = self.outbox.get()
                arduino.write((line + "\n").encode("ascii", "replace"))
                time.sleep(0.05)                    # don't shout notes faster than it can read
