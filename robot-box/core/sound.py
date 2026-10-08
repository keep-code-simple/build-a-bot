# The box's voice and beeps.
#   Beeps and tunes are made from math (a sine wave) and played by pygame.
#   Talking is slow, so sentences wait in a queue and ONE helper says them in order.
#   The game never freezes while the robot talks.
# Which voice? Piper (a natural voice) if it's installed, else espeak-ng (robotic but instant),
# and with --desktop on a Mac, the Mac's own "say".

import importlib.util
import queue
import shutil
import subprocess
import sys
import threading

import numpy as np
import pygame

from .settings import MODELS_FOLDER

SOUND_RATE = 22050      # sound samples per second

# Tunes are lists of (pitch in hertz, length in milliseconds). 0 hertz = a short silence.
TUNES = {
    "HELLO": [(523, 150), (659, 150), (784, 150), (1047, 200)],
    "WIN":   [(784, 120), (988, 120), (1175, 120), (1568, 250)],
    "LOSE":  [(392, 250), (370, 250), (349, 250), (330, 400)],
    "TIE":   [(659, 200), (0, 50), (659, 200)],
    "COUNT": [(523, 150)],
    "SHOOT": [(1047, 300)],
    "OOPS":  [(220, 300)],
}


def wave(hz, ms, loudness=0.4):
    """The numbers for one beep: a sine wave with soft edges so it doesn't click."""
    count = int(SOUND_RATE * ms / 1000)
    if hz <= 0:
        return np.zeros(count, dtype=np.int16)
    time = np.arange(count) / SOUND_RATE
    shape = np.sin(2 * np.pi * hz * time)
    fade = np.minimum(1, np.minimum(np.arange(count), count - np.arange(count)) / (SOUND_RATE * 0.01))
    return (shape * fade * loudness * 32767).astype(np.int16)


def speech_commands(text, desktop, voice_file=None, mac_voice="", which=shutil.which,
                    has_piper=None, wav_file="/tmp/robot-box-voice.wav"):
    """The commands that say the text out loud, as LISTS of separate words.

    A list means the text can never be run as a command, even if it looks like one.
    Returns [] if this computer has no voice at all.
    """
    if has_piper is None:
        has_piper = importlib.util.find_spec("piper") is not None
    if voice_file and has_piper and which("aplay"):
        return [[sys.executable, "-m", "piper", "-m", str(voice_file), "-f", wav_file, "--", text],
                ["aplay", "-q", wav_file]]
    if which("espeak-ng"):
        return [["espeak-ng", text]]
    if desktop and which("say"):
        return [["say"] + (["-v", mac_voice] if mac_voice else []) + [text]]
    return []


class Sound:
    def __init__(self, config=None, desktop=False, run=subprocess.run, log=print):
        config = (config or {}).get("voice", {})
        self.desktop = desktop
        self.run = run                    # tests swap this for a pretend one
        self.log = log
        self.mac_voice = config.get("mac_voice", "")
        voice_file = MODELS_FOLDER / "voice" / (config.get("piper_voice", "") + ".onnx")
        self.voice_file = voice_file if voice_file.exists() else None
        try:
            pygame.mixer.init(SOUND_RATE, -16, 1, 512)
            self.speaker_works = True
        except pygame.error:              # no speaker plugged in: carry on silently
            self.speaker_works = False
        self.waiting = queue.Queue(maxsize=5)
        self.talker = threading.Thread(target=self._talk, daemon=True)
        self.talker.start()

    def beep(self, hz=880, ms=200):
        self._play([(hz, ms)])

    def tune(self, name):
        self._play(TUNES.get(name, TUNES["OOPS"]))

    def _play(self, notes):
        if self.speaker_works:
            samples = np.concatenate([wave(hz, ms) for hz, ms in notes])
            pygame.mixer.Sound(buffer=samples.tobytes()).play()

    def say(self, text):
        """Queue a sentence for the robot's voice. Returns right away."""
        try:
            self.waiting.put_nowait(str(text))
        except queue.Full:
            self.log("Too much to say! Skipped: " + str(text))

    def wait_until_quiet(self):
        self.waiting.join()

    def _talk(self):
        while True:
            text = self.waiting.get()
            try:
                commands = speech_commands(text, self.desktop, self.voice_file, self.mac_voice)
                for command in commands:
                    self.run(command, check=False, timeout=30)
            except (OSError, subprocess.SubprocessError) as problem:
                self.log(f"The voice had a problem: {problem}")
            finally:
                self.waiting.task_done()
