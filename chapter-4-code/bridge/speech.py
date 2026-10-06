# The robot's voice: the Mac's built-in "say" command.
# Talking is slow, so sentences wait in a queue and ONE worker says them in order.
# That way two messages never talk over each other.

import queue
import subprocess
import threading

from . import protocol


def say_command(text, voice="", rate=0):
    """Build the command as a LIST of separate words.

    A list means the text can never be run as a command, even if it looks like one.
    The text '"; echo HACKED' just gets spoken out loud.
    """
    command = ["say"]
    if voice:
        command += ["-v", voice]
    if rate:
        command += ["-r", str(int(rate))]
    return command + [text]


class SpeechQueue:
    def __init__(self, voice="", rate=0, run=subprocess.run, log=print, max_waiting=10):
        self.voice = voice
        self.rate = rate
        self.run = run                    # tests swap this for a pretend one
        self.log = log
        self.waiting = queue.Queue(maxsize=max_waiting)
        self.thread = threading.Thread(target=self._work, daemon=True)
        self.thread.start()

    def say(self, text, first=None):
        """Queue a sentence. 'first' is a job to do just before speaking, like updating the screen."""
        text = protocol.clean_for_speech(text)
        try:
            self.waiting.put_nowait((text, first))
        except queue.Full:
            self.log("🔇 Too much to say! Skipped: " + text)

    def wait_until_quiet(self):
        """Wait until everything in the queue has been said."""
        self.waiting.join()

    def stop(self):
        self.waiting.put((None, None))    # None means "worker, go home"
        self.thread.join(timeout=3)

    def _work(self):
        while True:
            text, first = self.waiting.get()
            try:
                if text is None:
                    return
                if first:
                    first()
                if text:
                    self._speak(text)
            except Exception as problem:  # a broken voice must never stop the robot
                self.log(f"🔇 Couldn't speak: {problem}")
            finally:
                self.waiting.task_done()

    def _speak(self, text):
        try:
            result = self.run(say_command(text, self.voice, self.rate), timeout=60)
            if getattr(result, "returncode", 0) != 0 and self.voice:
                # That voice isn't on this Mac. Use the Mac's normal voice instead.
                self.log(f"🔇 No voice called {self.voice}, using the Mac's normal voice.")
                self.voice = ""
                self.run(say_command(text, "", self.rate), timeout=60)
        except FileNotFoundError:
            self.log("🔇 (This computer has no 'say' command.) I would say: " + text)
