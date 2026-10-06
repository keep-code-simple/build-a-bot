# The robot's alarm clock.
# Every 20 seconds it looks at the clock and asks: "is anything on my list due this minute?"
# The clock is passed in, so the tests can use a pretend clock.

from datetime import datetime

from . import rules

DAYS = ["mon", "tue", "wed", "thu", "fri", "sat", "sun"]
CHECK_EVERY = 20        # seconds


def check_item(item):
    """Make sure one schedule line makes sense. Returns a tidy copy, or raises ValueError."""
    hour, minute = rules.clock_time(str(item.get("time", "")))
    days = [str(day).lower()[:3] for day in item.get("days", DAYS)]
    for day in days:
        if day not in DAYS:
            raise ValueError(f"{day!r} is not a day. Use: {', '.join(DAYS)}")
    if not str(item.get("say", "")).strip():
        raise ValueError("there is nothing to say")
    return {"hour": hour, "minute": minute, "days": days,
            "say": str(item["say"]), "tune": str(item.get("tune", "")).upper()}


class Scheduler:
    def __init__(self, items, clock=datetime.now, log=print):
        self.clock = clock
        self.items = []
        self.already_fired = set()         # (which item, which day, which minute)
        for item in items or []:
            try:
                self.items.append(check_item(item))
            except (ValueError, AttributeError, KeyError) as problem:
                log(f"⏰ Skipping a schedule line: {problem}")

    def due(self):
        """The items that should fire right now. Each one fires only once in its minute."""
        now = self.clock()
        today = DAYS[now.weekday()]
        firing = []
        for number, item in enumerate(self.items):
            right_minute = (now.hour, now.minute) == (item["hour"], item["minute"])
            stamp = (number, now.date(), now.hour, now.minute)
            if right_minute and today in item["days"] and stamp not in self.already_fired:
                self.already_fired.add(stamp)
                firing.append(item)
        # forget old days so the memory never grows
        self.already_fired = {stamp for stamp in self.already_fired if stamp[1] == now.date()}
        return firing

    def run(self, stopping, on_fire):
        """The scheduler thread: check, then nap, until told to stop."""
        while not stopping.is_set():
            for item in self.due():
                on_fire(item)
            stopping.wait(CHECK_EVERY)
