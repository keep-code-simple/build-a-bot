import pytest

from bridge import protocol
from bridge.arduino_link import FakeArduino


# ---------- cleaning and wrapping text for the 16x2 screen ----------

def test_emoji_become_one_question_mark():
    assert protocol.clean_for_lcd("Hi 🤖!") == "Hi ?!"
    assert protocol.clean_for_lcd("Family 👨‍👩‍👧‍👦 time") == "Family ? time"     # a 7-part emoji


def test_curly_quotes_from_phones_become_plain():
    assert protocol.clean_for_lcd("I’m “home” – yay…") == "I'm \"home\" - yay..."


def test_bar_and_newlines_cannot_break_show():
    assert protocol.clean_for_lcd("a|b\nc\td") == "a/b c d"
    assert "\n" not in protocol.show("one\ntwo", "three|four")
    assert protocol.show("one\ntwo", "three|four").count("|") == 1


def test_wrap_on_word_boundaries():
    assert protocol.wrap_for_lcd("Hello, I am a robot") == ("Hello, I am a", "robot")
    assert protocol.wrap_for_lcd("Hi") == ("Hi", "")
    assert protocol.wrap_for_lcd("") == ("", "")


def test_wrap_never_longer_than_16_and_drops_the_overflow():
    line1, line2 = protocol.wrap_for_lcd("The quick brown fox jumps over the lazy dog again and again")
    assert line1 == "The quick brown"
    assert line2 == "fox jumps over"
    assert len(line1) <= 16 and len(line2) <= 16


def test_wrap_cuts_a_giant_word():
    assert protocol.wrap_for_lcd("Supercalifragilisticexpialidocious!") == ("Supercalifragili", "")
    assert protocol.wrap_for_lcd("Wow Supercalifragilisticexpialidocious") == ("Wow", "Supercalifragili")


def test_speech_is_cut_to_100_letters_and_loses_control_letters():
    assert len(protocol.clean_for_speech("blah " * 100)) <= 100
    assert protocol.clean_for_speech("hi\x00\x07 there\n") == "hi there"
    assert protocol.clean_for_speech("--version") == "version"


# ---------- building notes for the Arduino ----------

def test_building_every_command():
    assert protocol.ping() == "PING"
    assert protocol.idle() == "IDLE"
    assert protocol.show("Hello", "I am a robot") == "SHOW Hello|I am a robot"
    assert protocol.show_wrapped("Hello, I am a robot") == "SHOW Hello, I am a|robot"
    assert protocol.beep(880, 200) == "BEEP 880 200"
    assert protocol.tune("win") == "TUNE WIN"
    assert protocol.notes([523, 659, 784]) == "NOTES 523 659 784"
    assert protocol.led("blink") == "LED BLINK"
    assert protocol.play(4) == "PLAY 4"


def test_show_cuts_each_line_to_16():
    assert protocol.show("x" * 40, "y" * 40) == "SHOW " + "x" * 16 + "|" + "y" * 16


def test_no_command_is_ever_longer_than_64():
    longest = [protocol.show("W" * 99, "W" * 99), protocol.notes([5000] * 8), protocol.beep(5000, 2000)]
    assert all(len(line) <= protocol.MAX_LINE for line in longest)


@pytest.mark.parametrize("bad", [
    lambda: protocol.beep(50, 200), lambda: protocol.beep(880, 5000), lambda: protocol.tune("DISCO"),
    lambda: protocol.notes([]), lambda: protocol.notes([523] * 9), lambda: protocol.notes([20]),
    lambda: protocol.led("purple"), lambda: protocol.play(0),
])
def test_bad_values_are_refused(bad):
    with pytest.raises(ValueError):
        bad()


def test_read_tune():
    assert protocol.read_tune("C E G C2") == [523, 659, 784, 1047]
    assert protocol.read_tune("523, 659,784") == [523, 659, 784]
    for bad in ["", "H", "C " * 9, "99999"]:
        with pytest.raises(ValueError):
            protocol.read_tune(bad)


# ---------- reading notes from the Arduino ----------

def test_parsing_good_lines():
    assert protocol.parse_line("READY\r\n") == {"kind": "READY"}
    assert protocol.parse_line("PONG") == {"kind": "PONG"}
    assert protocol.parse_line("EVENT VISITOR 23") == {"kind": "VISITOR", "count": 23}
    assert protocol.parse_line("EVENT LEFT") == {"kind": "LEFT"}
    assert protocol.parse_line("OK SHOW") == {"kind": "OK", "verb": "SHOW"}
    assert protocol.parse_line("ERR TOO_LONG") == {"kind": "ERR", "reason": "TOO_LONG"}


@pytest.mark.parametrize("bad", ["", "EVENT VISITOR", "EVENT VISITOR x", "EVENT VISITOR -1", "OK",
                                 "HELLO THERE", "ready", "\x00\xff garbage"])
def test_parsing_bad_lines_gives_junk_not_a_crash(bad):
    assert protocol.parse_line(bad)["kind"] == "JUNK"


def test_parsing_too_long_line():
    message = protocol.parse_line("X" * 500)
    assert message["kind"] == "JUNK" and len(message["text"]) == 64


# ---------- the pretend Arduino follows the same protocol table ----------

@pytest.mark.parametrize("note, answer", [
    ("PING", "PONG"), ("ping", "PONG"),
    ("SHOW Hello|I am a robot", "OK SHOW"),
    ("BEEP 880 200", "OK BEEP"), ("BEEP 50 200", "ERR RANGE"), ("BEEP 880 9999", "ERR RANGE"),
    ("BEEP 880", "ERR RANGE"), ("BEEP abc def", "ERR RANGE"),
    ("TUNE HELLO", "OK TUNE"), ("TUNE WIN", "OK TUNE"), ("TUNE SAD", "OK TUNE"), ("TUNE SIREN", "OK TUNE"),
    ("TUNE DISCO", "ERR UNKNOWN"),
    ("NOTES 523 659 784 1047", "OK NOTES"), ("NOTES " + "523 " * 9, "ERR RANGE"), ("NOTES", "ERR RANGE"),
    ("NOTES 523 20", "ERR RANGE"),
    ("LED ON", "OK LED"), ("LED OFF", "OK LED"), ("LED BLINK", "OK LED"), ("LED PURPLE", "ERR UNKNOWN"),
    ("PLAY 1", "ERR NO_PLAYER"), ("PLAY 0", "ERR RANGE"),
    ("IDLE", "OK IDLE"),
    ("DANCE", "ERR UNKNOWN"), ("PINGPONG", "ERR UNKNOWN"),
    ("SHOW " + "x" * 70, "ERR TOO_LONG"),
])
def test_fake_arduino_answers(note, answer):
    assert FakeArduino().answer(note) == answer


def test_fake_arduino_screen_and_visitors():
    robot = FakeArduino()
    assert robot.readline() == b"READY\n"
    robot.write(b"SHOW A very long first line|two\n")
    assert robot.readline() == b"OK SHOW\n"
    assert robot.screen == ("A very long firs", "two")
    robot.visitor()
    assert robot.readline() == b"EVENT VISITOR 1\n"
    robot.left()
    assert robot.readline() == b"EVENT LEFT\n"
    assert robot.readline() == b""
