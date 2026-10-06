# Face recognition, all on this Mac. Nothing is uploaded and no photos are saved.
#
# How it works:
#   1. A "face finder" AI draws a box around each face.
#   2. A "fingerprint maker" AI turns a face into 128 numbers (an EMBEDDING).
#   3. We compare numbers with numbers. Close numbers = probably the same person.
#
# The AI only gives SCORES. The rule for "sure enough to say a name" is ours, and it is strict:
# saying "friend" is always better than saying the wrong brother's name.

import json
import re
import time
from collections import deque
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent.parent
MODELS = HERE / "models"
FACES = HERE / "faces"                  # PRIVATE: one file of numbers per person
PEOPLE_FILE = HERE / "people.json"      # PRIVATE: names, catchphrases and tunes

FINDER_MODEL = "face_detection_yunet_2023mar.onnx"
FINGERPRINT_MODEL = "face_recognition_sface_2021dec.onnx"

FRIEND = "friend"
SURE_ENOUGH = 0.45       # the best score must be at least this...
BEAT_SECOND_BY = 0.06    # ...and beat the next person by at least this


# ---------- the decision rule (plain maths, no camera needed) ----------

def similarity(a, b):
    """Cosine similarity: 1.0 = pointing the same way, 0 = nothing alike."""
    a, b = np.asarray(a, dtype=float).ravel(), np.asarray(b, dtype=float).ravel()
    return float(a @ b / (np.linalg.norm(a) * np.linalg.norm(b) + 1e-9))


def person_score(face, samples, compare=similarity):
    """How much does this face look like one person? The average of their 3 best matches."""
    scores = sorted((compare(face, sample) for sample in samples), reverse=True)
    best = scores[:3]
    return sum(best) / len(best) if best else 0.0


def all_scores(face, people, compare=similarity):
    """people is {person_id: [samples]}. Gives back {person_id: score}."""
    return {who: person_score(face, samples, compare) for who, samples in people.items()}


def decide(scores, sure_enough=SURE_ENOUGH, beat_second_by=BEAT_SECOND_BY):
    """Pick a name ONLY if the AI is sure and nobody else is close. Otherwise: friend."""
    if not scores:
        return FRIEND
    ranked = sorted(scores.items(), key=lambda pair: pair[1], reverse=True)
    best_name, best = ranked[0]
    second = ranked[1][1] if len(ranked) > 1 else -1.0
    tiny = 1e-9                          # computers are a hair off with decimals
    if best >= sure_enough - tiny and best - second >= beat_second_by - tiny:
        return best_name
    return FRIEND


class FrameVote:
    """One frame can be wrong. Wait until the same answer shows up in 3 of the last 5 frames."""

    def __init__(self, needed=3, window=5):
        self.needed = needed
        self.recent = deque(maxlen=window)

    def add(self, answer):
        """Add this frame's answer (None = no face). Returns the winner, or None if not sure yet."""
        self.recent.append(answer)
        for candidate in set(self.recent):
            if candidate is not None and list(self.recent).count(candidate) >= self.needed:
                return candidate
        return None

    def clear(self):
        self.recent.clear()


class Doorman:
    """Decides WHEN to greet. Feed it every frame's answer; it says who to greet, or None.

    - A name needs 3 of the last 5 frames.
    - "friend" also has to wait 2 seconds, in case the AI just needs a better look.
    - Everyone is greeted once per visit. A new visit starts after 5 seconds with no face.
    """

    def __init__(self, needed=3, window=5, clock=None, friend_wait=2, gone_after=5):
        self.vote = FrameVote(needed, window)
        self.clock = clock or time.monotonic
        self.friend_wait = friend_wait
        self.gone_after = gone_after
        self.visit_started = None          # None = nobody is here
        self.last_face = 0
        self.greeted = set()

    def see(self, answer):
        """answer is a person's id, FRIEND, or None when there is no face in the frame."""
        now = self.clock()
        if answer is None:
            if self.visit_started is not None and now - self.last_face > self.gone_after:
                self.visit_started = None  # they left: the next face is a new visit
                self.greeted.clear()
                self.vote.clear()
        else:
            if self.visit_started is None:
                self.visit_started = now
            self.last_face = now

        winner = self.vote.add(answer)
        if winner is None or winner in self.greeted:
            return None
        if winner == FRIEND and (self.greeted or now - self.visit_started < self.friend_wait):
            return None
        self.greeted.add(winner)
        return winner


# ---------- saving and forgetting people ----------

def make_id(name):
    """ "Kid 1" -> "kid-1": a safe file name."""
    return re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-") or "person"


def load_people(people_file=PEOPLE_FILE, faces_folder=FACES):
    """Returns (details, samples): details[id] = name and catchphrase, samples[id] = their numbers."""
    people_file, faces_folder = Path(people_file), Path(faces_folder)
    details = json.loads(people_file.read_text()) if people_file.exists() else {}
    samples = {}
    for who in list(details):
        numbers_file = faces_folder / f"{who}.npy"
        if numbers_file.exists():
            samples[who] = np.load(numbers_file)
        else:
            del details[who]            # a name with no numbers can't be recognized
    return details, samples


def save_person(who, info, embeddings, people_file=PEOPLE_FILE, faces_folder=FACES):
    people_file, faces_folder = Path(people_file), Path(faces_folder)
    faces_folder.mkdir(exist_ok=True)
    np.save(faces_folder / f"{who}.npy", np.asarray(embeddings, dtype=np.float32))
    details = json.loads(people_file.read_text()) if people_file.exists() else {}
    details[who] = info
    people_file.write_text(json.dumps(details, indent=2) + "\n")


def forget_person(name, people_file=PEOPLE_FILE, faces_folder=FACES):
    """Delete every trace of a person. Returns True if there was something to delete."""
    people_file, faces_folder = Path(people_file), Path(faces_folder)
    details = json.loads(people_file.read_text()) if people_file.exists() else {}
    matches = [who for who, info in details.items()
               if name.lower() in (who, info.get("name", "").lower())]
    matches = matches or [make_id(name)]
    found = False
    for who in matches:
        numbers_file = faces_folder / f"{who}.npy"
        if numbers_file.exists():
            numbers_file.unlink()
            found = True
        if details.pop(who, None) is not None:
            found = True
    if people_file.exists():
        if details:
            people_file.write_text(json.dumps(details, indent=2) + "\n")
        else:
            people_file.unlink()        # nobody left: remove the file too
    return found


# ---------- the camera part (needs OpenCV and the two model files) ----------

class FaceEngine:
    def __init__(self, models=MODELS):
        import cv2                       # only needed when the camera is really used
        self.cv2 = cv2
        finder, fingerprint = Path(models) / FINDER_MODEL, Path(models) / FINGERPRINT_MODEL
        if not finder.exists() or not fingerprint.exists():
            raise SystemExit("Missing the face models. Do the 'download the models' part of Step 5.")
        self.finder = cv2.FaceDetectorYN.create(str(finder), "", (320, 320), 0.8)
        self.fingerprinter = cv2.FaceRecognizerSF.create(str(fingerprint), "")

    def find_faces(self, frame):
        """Every face in the picture, biggest (closest) first. Each face is a row of numbers."""
        height, width = frame.shape[:2]
        self.finder.setInputSize((width, height))
        _, faces = self.finder.detect(frame)
        if faces is None:
            return []
        return sorted(faces, key=lambda face: face[2] * face[3], reverse=True)

    def embedding(self, frame, face):
        """Turn one face into its 128 numbers."""
        straightened = self.fingerprinter.alignCrop(frame, face)
        return self.fingerprinter.feature(straightened).copy()

    def compare(self, a, b):
        """OpenCV's own cosine score for two embeddings."""
        a = np.asarray(a, dtype=np.float32).reshape(1, -1)
        b = np.asarray(b, dtype=np.float32).reshape(1, -1)
        return float(self.fingerprinter.match(a, b, self.cv2.FaceRecognizerSF_FR_COSINE))


def box(face):
    """The face's rectangle as whole numbers: x, y, width, height."""
    return int(face[0]), int(face[1]), int(face[2]), int(face[3])


def open_camera(number=0):
    import cv2
    camera = cv2.VideoCapture(number)
    if not camera.isOpened():
        raise SystemExit("Can't open the camera. See 'Camera won't open' in Troubleshooting.")
    return camera
