# The cloud: how the robot hears from a phone, and how it texts back.
# We use ntfy, a free message service. A "topic" is like a mailbox with a secret name.
#
# The Mac always reaches OUT to ntfy and asks "any messages for me?".
# Nothing on the internet can reach IN to the house.
#
# The secret topic names are never printed in the log.

import json
import queue
import threading
from collections import deque

PLACEHOLDER = "CHANGE-ME"       # what config.example.json has instead of real topics
MAX_WAIT = 30                   # the longest we wait before trying to reconnect


def is_real_topic(topic):
    return bool(topic) and PLACEHOLDER not in topic


def backoff_waits():
    """How long to wait before each reconnect try: 1, 2, 4, 8, 16, 30, 30, 30... seconds."""
    wait = 1
    while True:
        yield wait
        wait = min(wait * 2, MAX_WAIT)


def default_http():
    import requests             # the add-on that talks to websites
    return requests


class PhoneListener:
    """Keeps one long connection open to the "to robot" topic and reads messages as they arrive."""

    def __init__(self, server, topic, on_message, http=None, log=print):
        self.url = f"{server.rstrip('/')}/{topic}/json"
        self.on_message = on_message
        self.http = http or default_http()
        self.log = log
        self.seen_ids = deque(maxlen=200)       # so the same message is never handled twice
        self.connected = False
        self.stopping = threading.Event()

    def handle_line(self, line):
        """One line from ntfy is one JSON object. Only "message" events matter."""
        if isinstance(line, bytes):
            line = line.decode("utf-8", "replace")
        if not line.strip():
            return
        try:
            event = json.loads(line)
        except ValueError:
            return                              # not JSON: ignore it
        if not isinstance(event, dict) or event.get("event") != "message":
            return                              # "open" and "keepalive" are just ntfy saying hi
        if event.get("id") in self.seen_ids:
            return                              # a repeat
        self.seen_ids.append(event.get("id"))
        self.on_message(str(event.get("message", "")))

    def listen_once(self):
        """Open the stream and read until it ends or breaks."""
        # timeout: 10 seconds to connect, and give up if ntfy is silent for 2 minutes
        with self.http.get(self.url, stream=True, timeout=(10, 120)) as stream:
            stream.raise_for_status()
            self.connected = True
            self.log("☁️  Listening for phone messages")
            for line in stream.iter_lines(chunk_size=1):    # 1 = hand over each line the moment it arrives
                if self.stopping.is_set():
                    return
                self.handle_line(line)

    def run(self):
        """The ntfy thread: listen forever, and reconnect with longer and longer waits."""
        waits = backoff_waits()
        while not self.stopping.is_set():
            self.connected = False
            try:
                self.listen_once()
                problem = "the connection closed"
            except Exception as error:          # no Wi-Fi, ntfy is down, anything at all
                problem = type(error).__name__
            if self.stopping.is_set():
                break
            if self.connected:
                waits = backoff_waits()         # it was working, so start the waits again from 1
            wait = next(waits)
            self.log(f"☁️  Lost the cloud ({problem}). Trying again in {wait} s.")
            self.stopping.wait(wait)

    def stop(self):
        self.stopping.set()


def publish(server, topic, title, message, http=None, log=print, tries=3, wait=2,
            sleep=None):
    """Send one notification to the "from robot" topic. Returns True if it worked."""
    http = http or default_http()
    sleep = sleep or threading.Event().wait
    url = f"{server.rstrip('/')}/{topic}"
    # Titles travel in a header, and headers can only carry plain letters.
    title = title.encode("ascii", "ignore").decode("ascii").strip() or "Robot"
    for attempt in range(1, tries + 1):
        try:
            answer = http.post(url, data=message.encode("utf-8"),
                               headers={"Title": title}, timeout=10)
            answer.raise_for_status()
            return True
        except Exception as error:
            if attempt < tries:
                sleep(wait)
            else:
                log(f"☁️  Couldn't send \"{message}\" ({type(error).__name__}). Moving on.")
    return False


class PhoneNotifier:
    """Sends notifications from its own thread, so a slow internet never freezes the robot."""

    def __init__(self, server, topic, http=None, log=print, wait=2):
        self.server, self.topic = server, topic
        self.http = http or default_http()
        self.log = log
        self.wait = wait
        self.outbox = queue.Queue(maxsize=10)
        self.thread = threading.Thread(target=self._work, daemon=True)
        self.thread.start()

    def send(self, title, message):
        try:
            self.outbox.put_nowait((title, message))
        except queue.Full:
            self.log("☁️  Too many notifications waiting. Skipped: " + message)

    def wait_until_sent(self):
        self.outbox.join()

    def _work(self):
        while True:
            title, message = self.outbox.get()
            try:
                if publish(self.server, self.topic, title, message, self.http, self.log,
                           wait=self.wait):
                    self.log("🔔 Texted the phone: " + message)
            finally:
                self.outbox.task_done()
