# The box watches itself: is it too hot? Is the charger too weak? How fast is it running?
# A Raspberry Pi answers those with the command "vcgencmd". On the Mac there's nothing to ask.

import subprocess
import time

# vcgencmd get_throttled answers with a number like 0x50005. Each "bit" in it is one warning light.
UNDER_VOLTAGE_NOW = 0x1         # the charger can't keep up right now
HOT_NOW = 0x2 | 0x4 | 0x8       # the Pi is slowing itself down, or is near its temperature limit

TOO_HOT_CELSIUS = 80


def read_throttled(text):
    """ "throttled=0x50005" -> the number 0x50005. Anything unreadable -> 0 (no warnings)."""
    try:
        return int(text.strip().split("=")[1], 16)
    except (IndexError, ValueError):
        return 0


def read_temperature(text):
    """ "temp=48.3'C" -> 48.3. Anything unreadable -> None."""
    try:
        return float(text.strip().split("=")[1].split("'")[0])
    except (IndexError, ValueError):
        return None


def warnings_for(throttled, temperature=None):
    """Turns the Pi's numbers into kid-friendly warnings: a list of (name, message)."""
    warnings = []
    too_hot = temperature is not None and temperature >= TOO_HOT_CELSIUS
    if throttled & UNDER_VOLTAGE_NOW:
        warnings.append(("power", "I need a better charger!"))
    if throttled & HOT_NOW or too_hot:
        warnings.append(("hot", "I'm too hot!"))
    return warnings


def ask_the_pi(question):
    """Runs vcgencmd and returns its answer, or "" if this isn't a Pi."""
    try:
        return subprocess.run(["vcgencmd", question], capture_output=True, text=True, timeout=2).stdout
    except (OSError, subprocess.SubprocessError):
        return ""


class Health:
    def __init__(self, ask=ask_the_pi, every_seconds=5, clock=time.monotonic, log=print):
        self.ask = ask
        self.every_seconds = every_seconds
        self.clock = clock
        self.log = log
        self.last_check = None
        self.temperature = None
        self.warnings = []

    def check(self):
        """Call this every frame. It only really asks the Pi every few seconds."""
        now = self.clock()
        if self.last_check is not None and now - self.last_check < self.every_seconds:
            return self.warnings
        self.last_check = now
        self.temperature = read_temperature(self.ask("measure_temp"))
        warnings = warnings_for(read_throttled(self.ask("get_throttled")), self.temperature)
        if warnings != self.warnings:
            for name, message in warnings:
                self.log(f"Health warning: {message} ({self.temperature} C)")
        self.warnings = warnings
        return self.warnings


class Speedometer:
    """Counts how many times something happens per second (camera frames, AI looks)."""

    def __init__(self, clock=time.monotonic):
        self.clock = clock
        self.started = clock()
        self.count = 0
        self.per_second = 0.0

    def tick(self):
        self.count += 1
        passed = self.clock() - self.started
        if passed >= 1:
            self.per_second = self.count / passed
            self.started = self.clock()
            self.count = 0
