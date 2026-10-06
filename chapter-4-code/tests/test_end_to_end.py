# The whole bridge, with a pretend Arduino, a pretend internet and a pretend voice.
# A phone message must become SHOW + speech, and EVENT VISITOR must become a text to the phone.
import json
import time
from datetime import datetime

import pytest

import robot_bridge
from bridge import cloud
from bridge.arduino_link import ArduinoLink, FakeArduino
from bridge.settings import load_config
from bridge.speech import SpeechQueue
from test_cloud import FakeHttp, FakeStream, line

SERVER, TO_ROBOT, FROM_ROBOT = "https://ntfy.example", "bab-test-to-robot", "bab-test-from-robot"


class RecordingArduino(FakeArduino):
    """A pretend Arduino that also remembers every note it was sent."""

    def __init__(self):
        super().__init__()
        self.notes = []

    def answer(self, note):
        self.notes.append(note)
        return super().answer(note)


class World:
    """Everything the bridge needs, all pretend, with a clock the test controls."""

    def __init__(self, hour=12, faces_on=False, **settings):
        self.config = load_config(config_file="/no/such/file")       # the example settings
        self.config.update(to_robot_topic=TO_ROBOT, from_robot_topic=FROM_ROBOT, ntfy_server=SERVER)
        self.config.update(settings)
        self.seconds = 1000.0
        self.wall = datetime(2026, 10, 5, hour, 0)
        self.log, self.spoken = [], []
        self.http = FakeHttp()
        self.arduino = RecordingArduino()
        self.speech = SpeechQueue("Samantha", run=lambda command, **kw: self.spoken.append(command[-1]),
                                  log=self.log.append)
        self.notifier = cloud.PhoneNotifier(SERVER, FROM_ROBOT, self.http, self.log.append, wait=0)
        self.link = ArduinoLink(fake=self.arduino, log=self.log.append)
        self.brain = robot_bridge.Brain(self.config, self.link, self.speech, self.notifier, faces_on,
                                        clock=lambda: self.seconds, now=lambda: self.wall,
                                        log=self.log.append)
        self.link.on_message = self.brain.from_arduino
        self.link.start()
        assert self.link.wait_until_ready(2)

    def settle(self):
        """Let the helper threads finish, then let the brain think."""
        for _ in range(3):
            time.sleep(0.15)
            self.brain.step()
            self.speech.wait_until_quiet()
            self.notifier.wait_until_sent()
        time.sleep(0.15)

    def phone_sends(self, *messages):
        """Messages arrive from the pretend ntfy stream, through the real listener code."""
        stream = [line("open")] + [line("message", f"id-{time.monotonic_ns()}-{n}", text)
                                   for n, text in enumerate(messages)]
        listener = cloud.PhoneListener(SERVER, TO_ROBOT, self.brain.from_phone,
                                       FakeHttp([FakeStream(stream)]), self.log.append)
        listener.listen_once()

    def shows(self):
        return [note for note in self.arduino.notes if note.startswith("SHOW")]

    def texts(self):
        return [post[1]["data"].decode() for post in self.http.posts]

    def close(self):
        self.link.stop()
        self.speech.stop()


@pytest.fixture
def world():
    worlds = []

    def make(**kwargs):
        worlds.append(World(**kwargs))
        return worlds[-1]

    yield make
    for made in worlds:
        made.close()


# ---------- Step 2: text the robot ----------

def test_phone_message_becomes_show_plus_speech(world):
    w = world()
    w.phone_sends("Dinner is ready, come downstairs")
    w.settle()
    assert w.shows() == ["SHOW Dinner is ready,|come downstairs"]
    assert w.spoken == ["Dinner is ready, come downstairs"]
    assert w.arduino.screen == ("Dinner is ready,", "come downstairs")
    assert any("📱 Phone said: Dinner is ready" in text for text in w.log)


def test_emoji_and_curly_quotes_from_a_phone_do_not_break_the_screen(world):
    w = world()
    w.phone_sends("I’m home 🎉")
    w.settle()
    assert w.shows() == ["SHOW I'm home ?|"]
    assert w.spoken == ["I’m home 🎉"]


def test_long_message_is_cut_to_100_letters(world):
    w = world()
    w.phone_sends("word " * 60)
    w.settle()
    assert len(w.spoken[0]) <= 100
    assert all(len(note) <= 64 for note in w.arduino.notes)


def test_quiet_hours_show_but_do_not_speak(world):
    w = world(hour=22)
    w.phone_sends("Goodnight robot")
    w.settle()
    assert w.shows() == ["SHOW Goodnight robot|"]
    assert w.spoken == []
    assert any("Quiet hours" in text for text in w.log)


def test_ten_messages_in_a_row_5_wait_5_are_dropped_one_every_3_seconds(world):
    w = world()
    w.phone_sends(*[f"message {n}" for n in range(10)])
    w.settle()
    assert w.spoken == ["message 0"]                       # the first goes straight away
    assert len([text for text in w.log if "Dropped" in text]) == 5
    for _ in range(6):
        w.seconds += 3
        w.settle()
    assert w.spoken == [f"message {n}" for n in range(5)]


def test_phone_commands(world):
    w = world()
    for command in ["!beep", "!tune win", "!led on", "!led off", "!TUNE SIREN", "!dance", "!tune disco"]:
        w.phone_sends(command)
        w.seconds += 3
        w.settle()
    wanted = ["BEEP 880 200", "TUNE WIN", "LED ON", "LED OFF", "TUNE SIREN"]
    assert [note for note in w.arduino.notes if note != "PING"] == wanted
    assert w.spoken == [] and w.shows() == []
    assert len([text for text in w.log if text.startswith("❓")]) == 2


def test_nasty_phone_text_is_only_ever_spoken(world):
    w = world()
    w.phone_sends('"; echo HACKED')
    w.settle()
    assert w.spoken == ['"; echo HACKED']


# ---------- Step 3: the robot texts back ----------

def test_event_visitor_becomes_a_publish(world):
    w = world()
    w.arduino.visitor()
    w.settle()
    assert w.texts() == ["🤖 Visitor #1 at the door"]
    url, kwargs = w.http.posts[0]
    assert url == f"{SERVER}/{FROM_ROBOT}"
    assert kwargs["headers"] == {"Title": "Door Greeter"}
    assert w.shows() == ["SHOW Hello, human!|Visitor #1"]
    assert w.spoken == ["Hello, human! You are visitor number 1."]
    assert any("🤖 Robot: visitor #1" in text for text in w.log)


def test_five_visits_in_a_minute_send_one_text(world):
    w = world()
    for _ in range(5):
        w.arduino.visitor()
        w.arduino.left()
        w.seconds += 10
        w.settle()
    assert w.texts() == ["🤖 Visitor #1 at the door"]
    w.seconds += 60
    w.arduino.visitor()
    w.settle()
    assert w.texts() == ["🤖 Visitor #1 at the door", "🤖 Visitor #6 at the door"]


def test_status_command_texts_back_uptime_and_visitors(world):
    w = world()
    w.arduino.visitor()
    w.arduino.visitor()
    w.settle()
    w.seconds += 3725
    w.phone_sends("!status")
    w.settle()
    assert w.texts()[-1] == "📊 Awake for 1 h 2 min. Visitors: 2."


def test_internet_off_visits_still_work_and_the_log_says_so(world):
    w = world()
    w.http.post_failures = 99
    w.arduino.visitor()
    w.settle()
    assert len(w.http.posts) == 3                               # three tries
    assert any("Couldn't send" in text for text in w.log)
    assert w.spoken == ["Hello, human! You are visitor number 1."]    # the greeting still happened
    assert not any(FROM_ROBOT in text or TO_ROBOT in text for text in w.log)


def test_without_secret_topics_the_bridge_still_runs(world):
    w = world()
    w.brain.notifier = None
    w.arduino.visitor()
    w.settle()
    assert w.texts() == [] and len(w.spoken) == 1


# ---------- Step 4: the alarm clock ----------

def test_alarm_shows_plays_and_speaks_even_in_quiet_hours(world):
    w = world(hour=22)
    w.brain.from_clock({"hour": 22, "minute": 0, "days": ["mon"], "say": "Snack time!", "tune": "WIN"})
    w.settle()
    notes = [note for note in w.arduino.notes if note != "PING"]
    assert notes == ["SHOW Snack time!|", "TUNE WIN"]
    assert w.spoken == ["Snack time!"]


# ---------- Step 5: faces ----------

KID_1 = {"name": "Kid 1", "say_as": "Kid One", "catchphrase": "Legend is here!", "tune": [523, 659, 784, 1047]}


def test_face_greeting_is_show_then_notes_then_speech(world):
    w = world(faces_on=True)
    w.brain.from_camera(KID_1)
    w.settle()
    notes = [note for note in w.arduino.notes if note != "PING"]
    assert notes == ["SHOW Hi Kid 1!|Legend is here!", "NOTES 523 659 784 1047"]
    assert w.spoken == ["Hi Kid One! Legend is here!"]


def test_names_never_go_to_the_internet_by_default(world):
    w = world(faces_on=True)
    w.brain.from_camera(KID_1)
    w.settle()
    assert w.texts() == ["🏠 Someone is home"]
    assert not any("Kid" in text for text in w.texts())


def test_names_go_out_only_if_notify_names_is_true(world):
    w = world(faces_on=True)
    w.config["faces"]["notify_names"] = True
    w.brain.from_camera(KID_1)
    w.settle()
    assert w.texts() == ["🏠 Kid 1 is home"]


def test_face_cooldowns_2_minutes_per_person_1_minute_for_friend(world):
    w = world(faces_on=True)
    for _ in range(3):
        w.brain.from_camera(KID_1)
        w.brain.from_camera(None)
        w.seconds += 30
        w.settle()
    assert w.spoken == ["Hi Kid One! Legend is here!", "Hello, friend!", "Hello, friend!"]
    w.seconds += 60
    w.brain.from_camera(KID_1)
    w.settle()
    assert w.spoken.count("Hi Kid One! Legend is here!") == 2


def test_with_faces_on_the_sensor_does_not_double_greet(world):
    w = world(faces_on=True)
    w.arduino.visitor()
    w.brain.from_camera(KID_1)
    w.settle()
    assert w.spoken == ["Hi Kid One! Legend is here!"]


# ---------- staying alive ----------

def test_heartbeat_ping_every_20_seconds(world):
    w = world()
    w.settle()
    assert w.arduino.notes.count("PING") == 1
    w.seconds += 20
    w.settle()
    assert w.arduino.notes.count("PING") == 2


def test_errors_from_the_arduino_are_logged_not_fatal(world):
    w = world()
    w.link.send("DANCE")
    w.settle()
    assert any("UNKNOWN" in text for text in w.log)


def test_how_long():
    assert robot_bridge.how_long(59) == "0 min"
    assert robot_bridge.how_long(3725) == "1 h 2 min"


def test_usb_cable_pulled_out_then_plugged_back_in():
    """The link keeps trying, says so in the log, and reconnects by itself."""
    log, heard = [], []

    class Cable:
        plugged_in = False
        yanked = False

    class FlakyArduino(FakeArduino):
        def readline(self):
            if Cable.yanked:
                Cable.yanked = False
                Cable.plugged_in = False
                raise OSError("device disconnected")
            return super().readline()

    class Link(ArduinoLink):
        def _open(self):
            if not Cable.plugged_in:
                raise OSError("no Arduino found. Is the USB cable plugged in?")
            return FlakyArduino()

    link = Link(on_message=heard.append, log=log.append)
    link.stopping.wait = lambda seconds: time.sleep(0.02)      # retry quickly in the test
    link.start()
    time.sleep(0.2)
    assert not link.connected and len([text for text in log if "Can't reach" in text]) == 1

    Cable.plugged_in = True
    assert link.wait_until_ready(2)
    link.send("PING")
    time.sleep(0.3)
    assert {"kind": "PONG"} in heard

    Cable.yanked = True                                         # pull the cable out
    time.sleep(0.3)
    assert any("cable came out" in text for text in log)
    assert not link.connected
    link.send("PING")                                           # dropped: nobody to send it to

    heard.clear()
    Cable.plugged_in = True                                     # plug it back in
    time.sleep(0.3)
    assert link.wait_until_ready(2)
    assert heard == [{"kind": "READY"}]
    link.stopping.wait = lambda seconds: None
    link.stop()
