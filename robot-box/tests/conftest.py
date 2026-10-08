# Shared helpers for the tests. Run them from the robot-box folder with:  pytest
import os
import sys
from pathlib import Path

os.environ["SDL_VIDEODRIVER"] = "dummy"       # pygame draws on a pretend screen
os.environ["SDL_AUDIODRIVER"] = "dummy"       # and plays to a pretend speaker

import pygame
import pytest

BOX_FOLDER = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BOX_FOLDER))

import box as box_file
from core.scores import Scores
from core.settings import EXAMPLE_FILE, load_config


class FakeSound:
    """Remembers everything the box "said" and "played", without making a sound."""

    def __init__(self):
        self.said, self.played = [], []

    def say(self, text):
        self.said.append(text)

    def beep(self, hz=880, ms=200):
        self.played.append(("beep", hz, ms))

    def tune(self, name):
        self.played.append(name)


class FakeArduino:
    def __init__(self):
        self.sent = []

    def send(self, letter):
        self.sent.append(letter)


class FakeButtons:
    """The test "presses" buttons by adding to .next"""

    def __init__(self):
        self.next = []

    def read(self):
        happened, self.next = self.next, []
        return happened


@pytest.fixture
def log():
    """A list that collects log lines: use log.append as the log function."""
    return []


@pytest.fixture
def screen():
    pygame.init()
    return pygame.display.set_mode((1280, 720))


@pytest.fixture
def box(tmp_path, log):
    config = load_config(config_file=tmp_path / "none.json", example_file=EXAMPLE_FILE)
    return box_file.Box(config, FakeSound(), Scores(tmp_path / "scores.json"), None, log.append)
