# Shared helpers for the tests. Run them from the chapter-4-code folder with:  pytest
import sys
from datetime import datetime, timedelta
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))


class FakeClock:
    """A pretend clock the tests can wind forward. No real waiting needed."""

    def __init__(self, start=datetime(2026, 10, 5, 12, 0, 0)):     # a Monday, at noon
        self.time = start

    def now(self):
        return self.time

    def seconds(self):
        return self.time.timestamp()

    def forward(self, seconds=0, minutes=0, hours=0, days=0):
        self.time += timedelta(seconds=seconds, minutes=minutes, hours=hours, days=days)

    def set(self, hour, minute, second=0):
        self.time = self.time.replace(hour=hour, minute=minute, second=second)


@pytest.fixture
def clock():
    return FakeClock()


@pytest.fixture
def log():
    """A list that collects log lines: use log.append as the log function."""
    return []
