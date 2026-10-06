import itertools
import json

from bridge import cloud

TOPIC = "bab-test-topic-not-real"


def line(event, id=None, message=None):
    data = {"event": event, "time": 1, "topic": TOPIC}
    if id:
        data["id"] = id
    if message is not None:
        data["message"] = message
    return json.dumps(data).encode()


class FakeStream:
    """Pretends to be a long-running web answer that sends one line at a time."""

    def __init__(self, lines, break_after=False, status=200):
        self.lines, self.break_after, self.status = lines, break_after, status

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False

    def raise_for_status(self):
        if self.status != 200:
            raise IOError(f"status {self.status}")

    def iter_lines(self, chunk_size=None):
        self.chunk_size = chunk_size
        yield from self.lines
        if self.break_after:
            raise ConnectionError("Wi-Fi went away")


class FakeHttp:
    """Pretends to be the internet. get() hands out the next stream; post() records what was sent."""

    def __init__(self, streams=(), post_failures=0):
        self.streams = list(streams)
        self.gets, self.posts = [], []
        self.post_failures = post_failures
        self.on_empty = None

    def get(self, url, **kwargs):
        self.gets.append((url, kwargs))
        if not self.streams:
            if self.on_empty:
                self.on_empty()
            raise ConnectionError("no internet")
        stream = self.streams.pop(0)
        if isinstance(stream, Exception):
            raise stream
        return stream

    def post(self, url, **kwargs):
        self.posts.append((url, kwargs))
        if self.post_failures > 0:
            self.post_failures -= 1
            raise ConnectionError("no internet")
        return FakeStream([])


def make_listener(http, log):
    heard = []
    listener = cloud.PhoneListener("https://ntfy.example", TOPIC, heard.append, http, log.append)
    listener.stopping.wait = lambda seconds: listener.waits.append(seconds)   # don't really wait
    listener.waits = []
    return listener, heard


# ---------- listening ----------

def test_subscribes_to_the_json_stream_of_the_topic(log):
    http = FakeHttp([FakeStream([])])
    listener, _ = make_listener(http, log)
    listener.listen_once()
    url, kwargs = http.gets[0]
    assert url == f"https://ntfy.example/{TOPIC}/json"
    assert kwargs["stream"] is True and kwargs["timeout"]


def test_lines_are_handed_over_one_at_a_time_not_in_big_chunks(log):
    stream = FakeStream([line("message", "id1", "hi")])
    listener, heard = make_listener(FakeHttp([stream]), log)
    listener.listen_once()
    assert stream.chunk_size == 1 and heard == ["hi"]


def test_only_message_events_are_handled(log):
    http = FakeHttp([FakeStream([
        line("open"), line("keepalive"), b"", b"not json at all", b"[1, 2]",
        line("message", "id1", "Hello robot"), line("keepalive"),
        line("message", "id2", "Second"),
    ])])
    listener, heard = make_listener(http, log)
    listener.listen_once()
    assert heard == ["Hello robot", "Second"]


def test_duplicate_ids_are_skipped(log):
    http = FakeHttp([FakeStream([
        line("message", "id1", "one"), line("message", "id1", "one"),
        line("message", "id2", "two"), line("message", "id1", "one"),
    ])])
    listener, heard = make_listener(http, log)
    listener.listen_once()
    assert heard == ["one", "two"]


def test_reconnects_after_an_error_and_skips_repeats(log):
    http = FakeHttp([
        FakeStream([line("open"), line("message", "id1", "before")], break_after=True),
        ConnectionError("still no Wi-Fi"),
        FakeStream([line("open"), line("message", "id1", "before"), line("message", "id2", "after")]),
    ])
    listener, heard = make_listener(http, log)
    http.on_empty = listener.stop           # when the fake internet runs out of streams, stop
    listener.run()
    assert heard == ["before", "after"]
    assert len(http.gets) == 4
    assert any("Lost the cloud" in text for text in log)


def test_backoff_is_1_2_4_up_to_30():
    assert list(itertools.islice(cloud.backoff_waits(), 8)) == [1, 2, 4, 8, 16, 30, 30, 30]


def test_backoff_grows_while_down_and_resets_after_a_good_connection(log):
    down = [ConnectionError("down")] * 7
    http = FakeHttp(down + [FakeStream([line("open")], break_after=True), ConnectionError("down")])
    listener, _ = make_listener(http, log)
    http.on_empty = listener.stop
    listener.run()
    assert listener.waits[:7] == [1, 2, 4, 8, 16, 30, 30]
    assert listener.waits[7] == 1           # it connected, then dropped: start again from 1
    assert listener.waits[8] == 2
    assert max(listener.waits) <= 30


def test_the_secret_topic_never_appears_in_the_log(log):
    http = FakeHttp([FakeStream([line("message", "id1", "hi")], break_after=True),
                     FakeStream([], status=500)])
    listener, _ = make_listener(http, log)
    http.on_empty = listener.stop
    listener.run()
    cloud.publish("https://ntfy.example", TOPIC, "Robot", "hello", FakeHttp(post_failures=9),
                  log.append, sleep=lambda s: None)
    assert log and not any(TOPIC in text for text in log)


# ---------- publishing ----------

def test_publish_posts_to_the_topic_with_a_title(log):
    http = FakeHttp()
    assert cloud.publish("https://ntfy.example/", TOPIC, "Door Greeter", "🤖 Visitor #24 at the door", http, log.append)
    url, kwargs = http.posts[0]
    assert url == f"https://ntfy.example/{TOPIC}"
    assert kwargs["headers"] == {"Title": "Door Greeter"}
    assert kwargs["data"] == "🤖 Visitor #24 at the door".encode("utf-8")


def test_title_header_is_plain_ascii(log):
    http = FakeHttp()
    cloud.publish("https://ntfy.example", TOPIC, "🤖 Door Greeter", "hi", http, log.append)
    assert http.posts[0][1]["headers"]["Title"] == "Door Greeter"


def test_publish_retries_3_times_then_gives_up_without_crashing(log):
    naps = []
    http = FakeHttp(post_failures=99)
    assert cloud.publish("https://ntfy.example", TOPIC, "Robot", "hello", http, log.append,
                         sleep=naps.append) is False
    assert len(http.posts) == 3
    assert naps == [2, 2]
    assert len(log) == 1 and "Couldn't send" in log[0]


def test_publish_works_on_the_second_try(log):
    http = FakeHttp(post_failures=1)
    assert cloud.publish("https://ntfy.example", TOPIC, "Robot", "hello", http, log.append,
                         sleep=lambda s: None)
    assert len(http.posts) == 2 and log == []


def test_notifier_sends_in_the_background(log):
    http = FakeHttp()
    notifier = cloud.PhoneNotifier("https://ntfy.example", TOPIC, http, log.append)
    notifier.send("Door Greeter", "one")
    notifier.send("Door Greeter", "two")
    notifier.wait_until_sent()
    assert [post[1]["data"] for post in http.posts] == [b"one", b"two"]


def test_placeholder_topics_are_not_real():
    assert not cloud.is_real_topic("bab-CHANGE-ME-run-setup_cloud-py")
    assert not cloud.is_real_topic("")
    assert not cloud.is_real_topic(None)
    assert cloud.is_real_topic("bab-Zk3vQ9x1LmN8pT4rYw2sAb")
