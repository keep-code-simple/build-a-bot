import json

import numpy as np
import pytest

from bridge import faces

rng = np.random.default_rng(42)


def direction():
    """A random 128-number 'face', length 1."""
    vector = rng.normal(size=128)
    return vector / np.linalg.norm(vector)


def lookalike(face, how_alike):
    """A new 128-number vector whose similarity to `face` is exactly how_alike."""
    other = direction()
    other -= (other @ face) * face
    other /= np.linalg.norm(other)
    return how_alike * face + np.sqrt(1 - how_alike ** 2) * other


KID_1, KID_2 = direction(), direction()
PEOPLE = {
    "kid-1": [lookalike(KID_1, 0.9) for _ in range(20)],
    "kid-2": [lookalike(KID_2, 0.9) for _ in range(20)],
}


# ---------- scores ----------

def test_embeddings_are_128_numbers():
    assert KID_1.shape == (128,) and len(PEOPLE["kid-1"]) == 20


def test_similarity():
    assert faces.similarity(KID_1, KID_1) == pytest.approx(1.0)
    assert faces.similarity(KID_1, -KID_1) == pytest.approx(-1.0)
    assert faces.similarity(KID_1, lookalike(KID_1, 0.5)) == pytest.approx(0.5)
    assert faces.similarity(KID_1 * 7, KID_1) == pytest.approx(1.0)     # length doesn't matter


def test_person_score_is_the_average_of_the_top_3():
    compare = lambda face, sample: sample           # pretend each sample IS its own score
    assert faces.person_score(None, [0.1, 0.9, 0.5, 0.7, 0.2], compare) == pytest.approx(0.7)
    assert faces.person_score(None, [0.4, 0.6], compare) == pytest.approx(0.5)
    assert faces.person_score(None, [], compare) == 0.0


# ---------- the decision rule ----------

def test_clear_match():
    scores = faces.all_scores(lookalike(KID_1, 0.9), PEOPLE)
    assert scores["kid-1"] > 0.7 and scores["kid-2"] < 0.3
    assert faces.decide(scores) == "kid-1"
    assert faces.decide(faces.all_scores(lookalike(KID_2, 0.9), PEOPLE)) == "kid-2"


def test_stranger_is_a_friend():
    scores = faces.all_scores(direction(), PEOPLE)
    assert max(scores.values()) < 0.45
    assert faces.decide(scores) == faces.FRIEND


def test_brother_too_close_is_a_friend():
    # A face that looks a lot like BOTH brothers: high scores, but nearly a tie.
    between = (KID_1 + KID_2) / np.linalg.norm(KID_1 + KID_2)
    scores = faces.all_scores(between, PEOPLE)
    assert min(scores.values()) >= 0.45            # both are "sure enough"...
    assert abs(scores["kid-1"] - scores["kid-2"]) < 0.06
    assert faces.decide(scores) == faces.FRIEND    # ...so the robot refuses to guess


@pytest.mark.parametrize("scores, answer", [
    ({"kid-1": 0.62, "kid-2": 0.30}, "kid-1"),
    ({"kid-1": 0.62, "kid-2": 0.57}, faces.FRIEND),     # only 0.05 ahead
    ({"kid-1": 0.62, "kid-2": 0.56}, "kid-1"),          # 0.06 ahead: just enough
    ({"kid-1": 0.44, "kid-2": 0.10}, faces.FRIEND),     # below 0.45
    ({"kid-1": 0.45, "kid-2": 0.10}, "kid-1"),          # exactly 0.45 counts
    ({"kid-1": 0.40, "kid-2": 0.80}, "kid-2"),
    ({"kid-1": 0.50}, "kid-1"),                         # only one person enrolled
    ({"kid-1": 0.20}, faces.FRIEND),
    ({}, faces.FRIEND),                                 # nobody enrolled
])
def test_decide(scores, answer):
    assert faces.decide(scores) == answer


def test_opencv_suggested_threshold_would_be_too_trusting():
    scores = {"kid-1": 0.40, "kid-2": 0.38}
    assert faces.decide(scores, sure_enough=0.363, beat_second_by=0) == "kid-1"   # a guess!
    assert faces.decide(scores) == faces.FRIEND                                    # our rule


def test_thresholds_can_be_changed():
    assert faces.decide({"kid-1": 0.40, "kid-2": 0.1}, sure_enough=0.35) == "kid-1"
    assert faces.decide({"kid-1": 0.90, "kid-2": 0.75}, beat_second_by=0.2) == faces.FRIEND


# ---------- the 3-of-5 frames rule ----------

def feed(vote, answers):
    return [vote.add(answer) for answer in answers]


def test_needs_3_of_the_last_5_frames():
    assert feed(faces.FrameVote(), ["kid-1", "kid-1", "kid-1"]) == [None, None, "kid-1"]


def test_3_of_5_with_other_answers_mixed_in():
    assert feed(faces.FrameVote(), ["kid-1", "friend", "kid-1", None, "kid-1"])[-1] == "kid-1"


def test_two_frames_are_not_enough_and_old_frames_fall_out():
    answers = ["kid-1", "kid-1", "friend", None, "kid-2", "kid-1"]
    assert feed(faces.FrameVote(), answers) == [None] * 6      # the first kid-1 fell out of the window


def test_one_wrong_frame_never_names_the_wrong_brother():
    answers = ["kid-1", "kid-2", "kid-1", "kid-2", "kid-1"]
    assert feed(faces.FrameVote(), answers)[-1] == "kid-1"
    assert "kid-2" not in feed(faces.FrameVote(), answers)


def test_no_face_never_wins_the_vote():
    assert feed(faces.FrameVote(), [None] * 10) == [None] * 10


# ---------- the doorman: when to greet ----------

class Stopwatch:
    time = 0.0

    def __call__(self):
        return self.time


def test_doorman_greets_a_name_once_per_visit():
    watch = Stopwatch()
    doorman = faces.Doorman(clock=watch)
    greeted = []
    for _ in range(100):                                # 10 seconds standing there
        greeted.append(doorman.see("kid-1"))
        watch.time += 0.1
    assert [who for who in greeted if who] == ["kid-1"]
    assert greeted.index("kid-1") == 2                  # on the third frame


def test_doorman_makes_friend_wait_so_a_name_can_win():
    watch = Stopwatch()
    doorman = faces.Doorman(clock=watch)
    greeted = []
    for answer in ["friend"] * 6 + ["kid-1"] * 6 + ["friend"] * 40:
        greeted.append(doorman.see(answer))
        watch.time += 0.1
    assert [who for who in greeted if who] == ["kid-1"]   # no "Hello, friend!" before or after


def test_doorman_greets_a_stranger_as_friend_after_2_seconds():
    watch = Stopwatch()
    doorman = faces.Doorman(clock=watch)
    greeted = []
    for _ in range(50):
        greeted.append(doorman.see("friend"))
        watch.time += 0.1
    assert [who for who in greeted if who] == ["friend"]
    assert greeted.index("friend") >= 20


def test_doorman_starts_a_new_visit_after_5_seconds_away():
    watch = Stopwatch()
    doorman = faces.Doorman(clock=watch)
    greeted = []
    for answer in ["kid-1"] * 10 + [None] * 30 + ["kid-1"] * 10 + [None] * 70 + ["kid-1"] * 10:
        greeted.append(doorman.see(answer))
        watch.time += 0.1
    assert [who for who in greeted if who] == ["kid-1", "kid-1"]   # a 3 s gap is the same visit


# ---------- saving, loading and forgetting ----------

INFO = {"name": "Kid 1", "say_as": "Kid One", "catchphrase": "Legend is here!", "tune": [523, 659, 784]}


def test_make_id():
    assert faces.make_id("Kid 1") == "kid-1"
    assert faces.make_id("  !!  ") == "person"


def test_save_then_load(tmp_path):
    people_file, folder = tmp_path / "people.json", tmp_path / "faces"
    faces.save_person("kid-1", INFO, PEOPLE["kid-1"], people_file, folder)
    details, samples = faces.load_people(people_file, folder)
    assert details == {"kid-1": INFO}
    assert samples["kid-1"].shape == (20, 128)
    assert sorted(path.name for path in tmp_path.rglob("*") if path.is_file()) == ["kid-1.npy", "people.json"]


def test_only_numbers_are_stored_no_photos(tmp_path):
    people_file, folder = tmp_path / "people.json", tmp_path / "faces"
    faces.save_person("kid-1", INFO, PEOPLE["kid-1"], people_file, folder)
    assert (folder / "kid-1.npy").stat().st_size < 20_000      # 20 x 128 small numbers: about 10 KB
    assert not list(tmp_path.rglob("*.jpg")) and not list(tmp_path.rglob("*.png"))


def test_forget_removes_every_trace(tmp_path):
    people_file, folder = tmp_path / "people.json", tmp_path / "faces"
    faces.save_person("kid-1", INFO, PEOPLE["kid-1"], people_file, folder)
    faces.save_person("kid-2", {**INFO, "name": "Kid 2"}, PEOPLE["kid-2"], people_file, folder)

    assert faces.forget_person("Kid 1", people_file, folder)
    assert not (folder / "kid-1.npy").exists()
    assert "kid-1" not in json.loads(people_file.read_text())
    assert "Kid 1" not in people_file.read_text()
    assert (folder / "kid-2.npy").exists()                     # the other brother is untouched

    assert faces.forget_person("kid 2", people_file, folder)   # capital letters don't matter
    assert not people_file.exists()
    assert list(folder.iterdir()) == []
    assert not faces.forget_person("Kid 1", people_file, folder)


def test_a_name_without_numbers_is_ignored(tmp_path):
    people_file, folder = tmp_path / "people.json", tmp_path / "faces"
    people_file.write_text(json.dumps({"ghost": INFO}))
    assert faces.load_people(people_file, folder) == ({}, {})


# ---------- the real OpenCV face tools (skipped if OpenCV or the models aren't here) ----------

def test_opencv_match_agrees_with_our_similarity():
    cv2 = pytest.importorskip("cv2")
    if not (faces.MODELS / faces.FINGERPRINT_MODEL).exists():
        pytest.skip("the face models have not been downloaded")
    engine = faces.FaceEngine()
    a, b = direction().astype(np.float32), direction().astype(np.float32)
    assert engine.compare(a, b) == pytest.approx(faces.similarity(a, b), abs=1e-4)
