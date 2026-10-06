# House rules: the robot must not be annoying.
#   - Cooldown: don't do the same thing again too soon.
#   - Quiet hours: show messages at night, but don't speak them.
#   - Waiting line: one phone message every few seconds, and only a few may wait.
# Every rule takes a clock, so the tests can use a pretend clock and "skip ahead" in time.

import time
from collections import deque
from datetime import datetime


class Cooldown:
    """ready("kid-1") says True once, then False until the cooldown has passed."""

    def __init__(self, seconds, clock=time.monotonic):
        self.seconds = seconds
        self.clock = clock
        self.last_time = {}

    def ready(self, key="everyone"):
        now = self.clock()
        if key in self.last_time and now - self.last_time[key] < self.seconds:
            return False
        self.last_time[key] = now
        return True


def clock_time(text):
    """ "21:00" -> (21, 0) """
    hour, minute = text.strip().split(":")
    hour, minute = int(hour), int(minute)
    if not (0 <= hour <= 23 and 0 <= minute <= 59):
        raise ValueError(f"{text!r} is not a time. Use 24-hour times like 15:30.")
    return hour, minute


def in_quiet_hours(now, start="21:00", end="07:00"):
    """Is 'now' (a datetime) inside quiet hours? They may cross midnight, like 21:00 to 07:00."""
    start, end, current = clock_time(start), clock_time(end), (now.hour, now.minute)
    if start == end:
        return False                       # same time twice means "no quiet hours"
    if start < end:
        return start <= current < end      # for example 13:00 to 14:00
    return current >= start or current < end


class WaitingLine:
    """Phone messages wait here. At most 'size' can wait, and one comes out every 'gap' seconds."""

    def __init__(self, gap=3, size=5, clock=time.monotonic):
        self.gap = gap
        self.size = size
        self.clock = clock
        self.line = deque()
        self.last_out = None

    def add(self, message):
        """Join the line. Says False if the line is full (the message is dropped)."""
        if len(self.line) >= self.size:
            return False
        self.line.append(message)
        return True

    def next(self):
        """The next message, or None if it isn't time yet (or nobody is waiting)."""
        if not self.line:
            return None
        now = self.clock()
        if self.last_out is not None and now - self.last_out < self.gap:
            return None
        self.last_out = now
        return self.line.popleft()


def quiet_now(config, now=None):
    """Read the quiet hours from the config and check the Mac's clock."""
    hours = config.get("quiet_hours") or {}
    if not hours.get("start") or not hours.get("end"):
        return False
    return in_quiet_hours(now or datetime.now(), hours["start"], hours["end"])
