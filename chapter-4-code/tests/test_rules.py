from datetime import datetime

import pytest

from bridge import rules


def at(hour, minute=0):
    return datetime(2026, 10, 5, hour, minute)


# ---------- quiet hours ----------

@pytest.mark.parametrize("hour, minute, quiet", [
    (21, 0, True), (23, 30, True), (0, 0, True), (6, 59, True),
    (7, 0, False), (12, 0, False), (20, 59, False),
])
def test_quiet_hours_across_midnight(hour, minute, quiet):
    assert rules.in_quiet_hours(at(hour, minute), "21:00", "07:00") is quiet


def test_quiet_hours_in_the_daytime():
    assert rules.in_quiet_hours(at(13, 30), "13:00", "14:00")
    assert not rules.in_quiet_hours(at(14, 0), "13:00", "14:00")
    assert not rules.in_quiet_hours(at(3, 0), "13:00", "14:00")


def test_same_start_and_end_means_no_quiet_hours():
    assert not rules.in_quiet_hours(at(3), "00:00", "00:00")


def test_quiet_now_reads_the_config():
    config = {"quiet_hours": {"start": "21:00", "end": "07:00"}}
    assert rules.quiet_now(config, at(22))
    assert not rules.quiet_now(config, at(12))
    assert not rules.quiet_now({}, at(22))


def test_bad_times_are_refused():
    for bad in ["25:00", "12:99", "noon", "12"]:
        with pytest.raises(ValueError):
            rules.clock_time(bad)


# ---------- cooldowns ----------

def test_cooldown_blocks_until_time_has_passed(clock):
    cooldown = rules.Cooldown(60, clock.seconds)
    assert cooldown.ready()
    clock.forward(seconds=59)
    assert not cooldown.ready()
    clock.forward(seconds=1)
    assert cooldown.ready()


def test_five_walk_pasts_in_a_minute_is_one_text(clock):
    cooldown = rules.Cooldown(60, clock.seconds)
    texts = 0
    for _ in range(5):
        texts += cooldown.ready()
        clock.forward(seconds=10)
    assert texts == 1


def test_each_person_has_their_own_cooldown(clock):
    cooldown = rules.Cooldown(120, clock.seconds)
    assert cooldown.ready("kid-1")
    assert cooldown.ready("kid-2")
    assert not cooldown.ready("kid-1")
    clock.forward(minutes=2)
    assert cooldown.ready("kid-1")


# ---------- the waiting line (rate limit) ----------

def test_one_message_every_3_seconds(clock):
    line = rules.WaitingLine(gap=3, size=5, clock=clock.seconds)
    line.add("a")
    line.add("b")
    assert line.next() == "a"
    assert line.next() is None            # too soon
    clock.forward(seconds=2.9)
    assert line.next() is None
    clock.forward(seconds=0.1)
    assert line.next() == "b"
    clock.forward(seconds=10)
    assert line.next() is None            # nobody waiting


def test_ten_messages_at_once_keeps_5_and_drops_5(clock):
    line = rules.WaitingLine(gap=3, size=5, clock=clock.seconds)
    kept = [line.add(f"message {n}") for n in range(10)]
    assert kept == [True] * 5 + [False] * 5
    spoken = []
    for _ in range(20):
        message = line.next()
        if message:
            spoken.append(message)
        clock.forward(seconds=3)
    assert spoken == [f"message {n}" for n in range(5)]


def test_line_has_room_again_after_one_leaves(clock):
    line = rules.WaitingLine(gap=3, size=2, clock=clock.seconds)
    assert line.add("a") and line.add("b") and not line.add("c")
    assert line.next() == "a"
    assert line.add("c")
