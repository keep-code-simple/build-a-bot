# The voice picking the right program, the speech queue, and the Arduino link.
import pytest

from core import arduino, sound


def test_voice_prefers_piper_then_espeak_then_the_mac():
    everything = lambda name: "/usr/bin/" + name
    commands = sound.speech_commands("Hi", False, "voice.onnx", which=everything, has_piper=True)
    assert commands[0][1:4] == ["-m", "piper", "-m"] and commands[0][-1] == "Hi"
    assert commands[1][0] == "aplay"

    only_espeak = lambda name: "/usr/bin/espeak-ng" if name == "espeak-ng" else None
    assert sound.speech_commands("Hi", False, None, which=only_espeak, has_piper=False) == [["espeak-ng", "Hi"]]
    assert sound.speech_commands("Hi", False, "voice.onnx", which=only_espeak, has_piper=False) == [["espeak-ng", "Hi"]]

    only_say = lambda name: "/usr/bin/say" if name == "say" else None
    assert sound.speech_commands("Hi", True, None, which=only_say, has_piper=False) == [["say", "Hi"]]
    assert sound.speech_commands("Hi", True, None, "Samantha", only_say, False) == [["say", "-v", "Samantha", "Hi"]]
    assert sound.speech_commands("Hi", False, None, which=lambda name: None, has_piper=False) == []


def test_text_can_never_become_a_command():
    nasty = '"; rm -rf ~ #'
    only_say = lambda name: "/usr/bin/say" if name == "say" else None
    assert sound.speech_commands(nasty, True, None, which=only_say, has_piper=False) == [["say", nasty]]


def test_speech_queue_says_things_in_order_without_blocking(log):
    ran = []
    voice = sound.Sound(desktop=True, run=lambda command, **options: ran.append(command[-1]), log=log.append)
    for words in ["one", "two", "three"]:
        voice.say(words)
    voice.wait_until_quiet()
    if ran:                                     # (a computer with no voice program says nothing)
        assert ran == ["one", "two", "three"]
    voice.beep()
    voice.tune("WIN")
    voice.tune("NOT A TUNE")                    # unknown tunes don't crash


def test_beep_wave():
    samples = sound.wave(440, 100)
    assert len(samples) == sound.SOUND_RATE // 10
    assert samples[0] == 0 and abs(int(samples.max())) > 1000
    assert not sound.wave(0, 50).any()          # 0 hertz is silence


class PretendPort:
    def __init__(self):
        self.written, self.closed = [], False

    def write(self, data):
        self.written.append(data)

    def close(self):
        self.closed = True


def test_arduino_finds_the_port_on_mac_and_pi(log):
    assert arduino.find_port(lambda pattern: ["/dev/ttyACM0"] if "ttyACM" in pattern else []) == "/dev/ttyACM0"
    assert arduino.find_port(lambda pattern: ["/dev/cu.usbmodem1"] if "usbmodem" in pattern else []) == "/dev/cu.usbmodem1"
    assert arduino.find_port(lambda pattern: []) is None
    with pytest.raises(SystemExit, match="No Arduino found"):
        arduino.Arduino(look=lambda pattern: [])


def test_arduino_sends_letters_and_says_goodbye(log):
    port = PretendPort()
    link = arduino.Arduino(open_port=lambda name: port, look=lambda pattern: ["/dev/ttyACM0"],
                           sleep=lambda seconds: None, log=log.append)
    link.send("r")
    link.close()
    assert port.written == [b"r", b"N"] and port.closed
