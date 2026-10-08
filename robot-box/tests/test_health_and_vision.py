# The box watching itself, and the vision router deciding who does the seeing.
import numpy as np
import pytest

from core import health, vision


def names(warnings):
    return [name for name, message in warnings]


def test_reading_the_pi_answers():
    assert health.read_throttled("throttled=0x0\n") == 0
    assert health.read_throttled("throttled=0x50005\n") == 0x50005
    assert health.read_throttled("") == 0                       # not a Pi
    assert health.read_temperature("temp=48.3'C\n") == 48.3
    assert health.read_temperature("") is None


def test_warnings():
    assert health.warnings_for(0x0, 45.0) == []                                 # all good
    assert names(health.warnings_for(0x50005)) == ["power", "hot"]              # weak charger, and slowed down
    assert names(health.warnings_for(0x1)) == ["power"]
    assert names(health.warnings_for(0x8)) == ["hot"]                           # near the temperature limit
    assert names(health.warnings_for(0x4)) == ["hot"]                           # slowed down right now
    assert health.warnings_for(0x50000, 50.0) == []                             # happened earlier, fine now
    assert names(health.warnings_for(0x0, 82.0)) == ["hot"]
    assert health.warnings_for(0x1)[0][1] == "I need a better charger!"
    assert health.warnings_for(0x8)[0][1] == "I'm too hot!"


def test_health_only_asks_every_few_seconds(log):
    time = [0.0]
    asked = []

    def ask(question):
        asked.append(question)
        return {"measure_temp": "temp=85.0'C", "get_throttled": "throttled=0x0"}[question]

    box_health = health.Health(ask, every_seconds=5, clock=lambda: time[0], log=log.append)
    assert names(box_health.check()) == ["hot"]
    time[0] = 2
    box_health.check()
    assert len(asked) == 2                                       # still the first two questions
    time[0] = 6
    box_health.check()
    assert len(asked) == 4
    assert len(log) == 1                                         # logged once, not every time


def test_health_on_a_mac_is_quiet():
    assert health.Health(lambda question: "").check() == []


def test_router_on_the_pi_with_the_ai_camera():
    routes = vision.route({"hands", "faces", "people", "objects", "pose"}, camera_has_ai=True, desktop=False)
    assert routes == {"people": "camera", "objects": "camera", "pose": "camera",
                      "hands": "processor", "faces": "processor"}


def test_router_without_the_ai_camera_or_on_the_desktop():
    everything = {"hands", "faces", "people", "objects", "pose"}
    assert set(vision.route(everything, camera_has_ai=False, desktop=False).values()) == {"processor"}
    assert set(vision.route(everything, camera_has_ai=True, desktop=True).values()) == {"processor"}
    assert vision.route(set(), True, False) == {}


def test_router_rejects_a_need_that_does_not_exist():
    with pytest.raises(ValueError):
        vision.route({"smells"}, False, True)


class PretendAICamera:
    has_ai = True

    def __init__(self):
        self.kind = None

    def use_ai(self, kind):
        self.kind = kind

    def ai_seen(self):
        return {"objects": [("person", 0.9, (0.1, 0.1, 0.3, 0.8)), ("cat", 0.7, (0.6, 0.6, 0.2, 0.2))],
                "poses": [[(0.5, 0.5)] * 17]}


def test_camera_results_flow_through_without_loading_any_model(tmp_path):
    camera = PretendAICamera()
    eyes = vision.Vision(camera, desktop=False, models_folder=tmp_path)     # an empty models folder
    eyes.open({"people"})
    assert camera.kind == "detect" and eyes.engines == {}
    seen = eyes.look(np.zeros((72, 128, 3), np.uint8))
    assert [thing.name for thing in seen.people] == ["person"] and seen.objects == []
    eyes.open({"pose", "objects"})
    assert camera.kind == "pose"
    assert len(eyes.look(np.zeros((72, 128, 3), np.uint8)).poses) == 1
    eyes.close()
    assert eyes.routes == {}


def test_a_missing_model_gives_a_helpful_message(tmp_path):
    eyes = vision.Vision(None, desktop=True, models_folder=tmp_path)
    with pytest.raises(vision.MissingModel, match="download_models.py hands"):
        eyes.open({"hands"})


def test_shrink_keeps_the_shape():
    picture = np.zeros((720, 1280, 3), np.uint8)
    assert vision.shrink(picture, 640).shape == (360, 640, 3)
    assert vision.shrink(picture, 2000) is picture               # already small enough
