import subprocess
import threading
from unittest import mock

from bridge.speech import SpeechQueue, say_command


def test_say_command_is_a_list_of_separate_words():
    assert say_command("Hello there", "Samantha") == ["say", "-v", "Samantha", "Hello there"]
    assert say_command("Hello", "") == ["say", "Hello"]
    assert say_command("Fast", "Fred", 300) == ["say", "-v", "Fred", "-r", "300", "Fast"]


def test_speech_uses_subprocess_run_with_a_list_and_no_shell():
    with mock.patch.object(subprocess, "run") as run:
        run.return_value.returncode = 0
        speech = SpeechQueue("Samantha", run=subprocess.run)
        speech.say("Hello, I am a robot")
        speech.wait_until_quiet()
        speech.stop()
    args, kwargs = run.call_args
    assert args[0] == ["say", "-v", "Samantha", "Hello, I am a robot"]
    assert isinstance(args[0], list)
    assert not kwargs.get("shell")


def test_injection_text_is_spoken_never_run(tmp_path):
    """The Step 1 test: '"; echo HACKED' must reach `say` as ONE plain argument."""
    nasty = '"; echo HACKED'
    calls = []
    speech = SpeechQueue("Samantha", run=lambda command, **kw: calls.append((command, kw)))
    speech.say(nasty)
    speech.say("$(touch %s/hacked) `touch %s/hacked`; rm -rf ~" % (tmp_path, tmp_path))
    speech.wait_until_quiet()
    speech.stop()

    command, kwargs = calls[0]
    assert command == ["say", "-v", "Samantha", nasty]      # the whole text is the last word
    assert "shell" not in kwargs
    assert calls[1][0][:3] == ["say", "-v", "Samantha"] and len(calls[1][0]) == 4


def test_injection_text_with_a_real_program(tmp_path):
    """Run a real program the same way (a harmless one instead of `say`) and check nothing else ran."""
    marker = tmp_path / "hacked"
    nasty = f'"; touch {marker}; echo HACKED'

    def run_echo_instead(command, **kwargs):
        return subprocess.run(["/bin/echo"] + command[1:], capture_output=True, **kwargs)

    speech = SpeechQueue("", run=run_echo_instead)
    speech.say(nasty)
    speech.wait_until_quiet()
    speech.stop()
    assert not marker.exists()


def test_text_cannot_pretend_to_be_an_option():
    calls = []
    speech = SpeechQueue("Samantha", run=lambda command, **kw: calls.append(command))
    speech.say("-o /tmp/sneaky.aiff hello")
    speech.wait_until_quiet()
    speech.stop()
    assert not calls[0][-1].startswith("-")


def test_sentences_are_spoken_one_at_a_time_in_order():
    order, talking, overlaps = [], threading.Lock(), []

    def slow_voice(command, **kwargs):
        if not talking.acquire(blocking=False):
            overlaps.append(command)
            return
        order.append(command[-1])
        threading.Event().wait(0.02)
        talking.release()

    speech = SpeechQueue("", run=slow_voice)
    for number in range(5):
        speech.say(f"message {number}")
    speech.wait_until_quiet()
    speech.stop()
    assert order == [f"message {n}" for n in range(5)]
    assert overlaps == []


def test_screen_job_runs_just_before_the_voice():
    events = []
    speech = SpeechQueue("", run=lambda command, **kw: events.append("voice"))
    speech.say("hi", first=lambda: events.append("screen"))
    speech.wait_until_quiet()
    speech.stop()
    assert events == ["screen", "voice"]


def test_empty_text_updates_the_screen_but_stays_silent():
    events = []
    speech = SpeechQueue("", run=lambda command, **kw: events.append("voice"))
    speech.say("", first=lambda: events.append("screen"))
    speech.wait_until_quiet()
    speech.stop()
    assert events == ["screen"]


def test_a_broken_voice_never_crashes_the_worker(log):
    def broken(command, **kwargs):
        raise FileNotFoundError("no say here")

    speech = SpeechQueue("", run=broken, log=log.append)
    speech.say("one")
    speech.say("two")
    speech.wait_until_quiet()
    speech.stop()
    assert len(log) == 2 and "one" in log[0]


def test_missing_voice_falls_back_to_the_normal_voice(log):
    calls = []

    def run(command, **kwargs):
        calls.append(command)
        return mock.Mock(returncode=1 if "-v" in command else 0)

    speech = SpeechQueue("NoSuchVoice", run=run, log=log.append)
    speech.say("hello")
    speech.wait_until_quiet()
    speech.stop()
    assert calls == [["say", "-v", "NoSuchVoice", "hello"], ["say", "hello"]]


def test_too_many_sentences_are_skipped_not_piled_up(log):
    gate = threading.Event()
    speech = SpeechQueue("", run=lambda command, **kw: gate.wait(2), log=log.append, max_waiting=3)
    for number in range(10):
        speech.say(f"message {number}")
    gate.set()
    speech.wait_until_quiet()
    speech.stop()
    assert any("Skipped" in line for line in log)
