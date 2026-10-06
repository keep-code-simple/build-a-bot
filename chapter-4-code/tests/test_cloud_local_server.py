# The real `requests` add-on talking to a tiny pretend ntfy server on THIS computer (127.0.0.1).
# Nothing here touches the internet.
import json
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

import pytest

requests = pytest.importorskip("requests")

from bridge import cloud

TOPIC_IN, TOPIC_OUT = "bab-local-test-in", "bab-local-test-out"


class PretendNtfy(BaseHTTPRequestHandler):
    received = []

    def log_message(self, *args):
        pass

    def do_GET(self):
        if self.path != f"/{TOPIC_IN}/json":
            self.send_error(404)
            return
        self.send_response(200)
        self.send_header("Content-Type", "application/x-ndjson")
        self.end_headers()
        for event in [{"event": "open"}, {"event": "keepalive"},
                      {"event": "message", "id": "a1", "message": "Hello from the phone"},
                      {"event": "message", "id": "a1", "message": "Hello from the phone"},
                      {"event": "message", "id": "a2", "message": "!status"}]:
            self.wfile.write(json.dumps(event).encode() + b"\n")
            self.wfile.flush()
        if "slow" in self.headers.get("User-Agent", ""):
            threading.Event().wait(5)                 # keep the line open, like the real ntfy does

    def do_POST(self):
        body = self.rfile.read(int(self.headers.get("Content-Length", 0)))
        PretendNtfy.received.append((self.path, self.headers.get("Title"), body.decode("utf-8")))
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"{}")


@pytest.fixture
def server():
    PretendNtfy.received = []
    httpd = ThreadingHTTPServer(("127.0.0.1", 0), PretendNtfy)
    threading.Thread(target=httpd.serve_forever, daemon=True).start()
    yield f"http://127.0.0.1:{httpd.server_address[1]}"
    httpd.shutdown()


def test_real_requests_reads_the_stream(server, log):
    heard = []
    listener = cloud.PhoneListener(server, TOPIC_IN, heard.append, log=log.append)
    listener.listen_once()
    assert heard == ["Hello from the phone", "!status"]


def test_real_requests_publishes_with_title_and_emoji(server, log):
    assert cloud.publish(server, TOPIC_OUT, "Door Greeter", "🤖 Visitor #24 at the door", log=log.append)
    assert PretendNtfy.received == [(f"/{TOPIC_OUT}", "Door Greeter", "🤖 Visitor #24 at the door")]


def test_real_requests_survives_a_dead_server(log):
    assert cloud.publish("http://127.0.0.1:9", TOPIC_OUT, "Robot", "hello", log=log.append,
                         sleep=lambda s: None) is False
    assert "Couldn't send" in log[0]


def test_messages_arrive_while_the_stream_is_still_open(server, log):
    """ntfy keeps the connection open for hours. A message must not wait for it to close."""
    import time

    class SlowSession(requests.Session):
        def __init__(self):
            super().__init__()
            self.headers["User-Agent"] = "slow"

    heard = []
    listener = cloud.PhoneListener(server, TOPIC_IN, lambda text: heard.append(time.monotonic()),
                                   http=SlowSession(), log=log.append)
    started = time.monotonic()
    threading.Thread(target=listener.listen_once, daemon=True).start()
    while len(heard) < 2 and time.monotonic() - started < 4:
        time.sleep(0.05)
    assert len(heard) == 2 and heard[-1] - started < 2
