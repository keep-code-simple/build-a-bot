import threading
from datetime import datetime

from bridge.scheduler import Scheduler

SNACK = {"time": "15:30", "days": ["mon", "tue", "wed", "thu", "fri"], "say": "Snack time!", "tune": "WIN"}
BED = {"time": "19:45", "days": ["sun", "mon", "tue", "wed", "thu"], "say": "Twenty minutes to bedtime", "tune": "HELLO"}


def says(items):
    return [item["say"] for item in items]


def test_fires_once_in_its_minute(clock):
    scheduler = Scheduler([SNACK], clock.now)
    clock.set(15, 29, 50)
    assert scheduler.due() == []
    clock.set(15, 30, 5)                       # the first check inside the minute
    assert says(scheduler.due()) == ["Snack time!"]
    clock.set(15, 30, 25)                      # the next checks, 20 seconds apart
    assert scheduler.due() == []
    clock.set(15, 30, 45)
    assert scheduler.due() == []
    clock.set(15, 31, 5)
    assert scheduler.due() == []


def test_fires_within_30_seconds_when_checked_every_20(clock):
    scheduler = Scheduler([SNACK], clock.now)
    clock.set(15, 29, 47)
    fired_at = None
    for _ in range(12):                        # four minutes of 20-second checks
        if scheduler.due():
            assert fired_at is None, "fired twice!"
            fired_at = clock.now()
        clock.forward(seconds=20)
    assert fired_at is not None
    assert 0 <= (fired_at - fired_at.replace(second=0)).seconds < 30
    assert (fired_at.hour, fired_at.minute) == (15, 30)


def test_only_on_the_listed_days(clock):
    scheduler = Scheduler([SNACK], clock.now)
    fired = []
    for _ in range(7):                         # Monday 5 Oct 2026 to Sunday
        clock.set(15, 30, 10)
        if scheduler.due():
            fired.append(clock.now().strftime("%a"))
        clock.forward(days=1)
    assert fired == ["Mon", "Tue", "Wed", "Thu", "Fri"]


def test_fires_again_the_next_day(clock):
    scheduler = Scheduler([SNACK], clock.now)
    clock.set(15, 30, 0)
    assert len(scheduler.due()) == 1
    clock.forward(days=1)
    assert len(scheduler.due()) == 1
    assert len(scheduler.already_fired) == 1   # yesterday was forgotten


def test_two_items_and_tidy_fields(clock):
    scheduler = Scheduler([SNACK, BED], clock.now)
    clock.set(19, 45, 0)
    due = scheduler.due()
    assert says(due) == ["Twenty minutes to bedtime"]
    assert due[0]["tune"] == "HELLO" and due[0]["hour"] == 19


def test_no_days_means_every_day(clock):
    scheduler = Scheduler([{"time": "08:00", "say": "Good morning"}], clock.now)
    clock.time = datetime(2026, 10, 10, 8, 0, 3)    # a Saturday
    assert says(scheduler.due()) == ["Good morning"]


def test_bad_lines_are_skipped_with_a_friendly_log(clock, log):
    scheduler = Scheduler([{"time": "25:99", "say": "x"}, {"time": "10:00"}, {"time": "10:00", "days": ["funday"], "say": "x"},
                           "nonsense", SNACK], clock.now, log.append)
    assert len(scheduler.items) == 1
    assert len(log) == 4


def test_empty_schedule_is_fine(clock):
    assert Scheduler(None, clock.now).due() == []


def test_run_loop_calls_on_fire_and_stops(clock):
    scheduler = Scheduler([SNACK], clock.now)
    clock.set(15, 30, 0)
    stopping, fired = threading.Event(), []

    def on_fire(item):
        fired.append(item["say"])
        stopping.set()

    scheduler.run(stopping, on_fire)
    assert fired == ["Snack time!"]
