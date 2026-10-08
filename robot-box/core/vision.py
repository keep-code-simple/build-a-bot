# The box's eyes: the vision router.
# An app says WHAT it needs to see ("hands", "faces", "people", "objects", "pose").
# This file decides WHO does the seeing:
#   - the AI Camera's own chip, when it can (people, objects, pose)
#   - the Pi's processor, when it must (hands and faces)
#   - with --desktop, the Mac's processor does everything
# Only the AI an app asked for gets loaded, and it's let go when the app closes.

from dataclasses import dataclass, field
import time

import cv2

from .settings import MODELS_FOLDER

ALL_NEEDS = {"hands", "faces", "people", "objects", "pose"}
CAMERA_CAN_DO = {"people", "objects", "pose"}

# The model file each need uses on the processor, and where to download it from
GOOGLE = "https://storage.googleapis.com/mediapipe-models/"
MODEL_FOR = {
    "hands": ("gesture_recognizer.task", GOOGLE + "gesture_recognizer/gesture_recognizer/float16/1/gesture_recognizer.task"),
    "faces": ("blaze_face_short_range.tflite", GOOGLE + "face_detector/blaze_face_short_range/float16/1/blaze_face_short_range.tflite"),
    "pose": ("pose_landmarker_lite.task", GOOGLE + "pose_landmarker/pose_landmarker_lite/float16/1/pose_landmarker_lite.task"),
    "objects": ("efficientdet_lite0.tflite", GOOGLE + "object_detector/efficientdet_lite0/float16/1/efficientdet_lite0.tflite"),
}
MODEL_FOR["people"] = MODEL_FOR["objects"]          # people are found by the same model as objects


class MissingModel(Exception):
    pass


@dataclass
class Hand:
    gesture: str        # what the AI calls it: "Closed_Fist", "Open_Palm", "Victory", "None"...
    score: float        # how sure the AI is, 0.0 to 1.0
    points: list        # the 21 hand points as (x, y), each from 0.0 to 1.0 across the picture


@dataclass
class Thing:
    name: str           # "person", "cat", "dog", "face"...
    score: float
    box: tuple          # (x, y, width, height), each from 0.0 to 1.0 across the picture


@dataclass
class Seen:
    """Everything the AI found in one picture. Lists an app didn't ask for stay empty."""
    hands: list = field(default_factory=list)
    faces: list = field(default_factory=list)
    people: list = field(default_factory=list)
    objects: list = field(default_factory=list)
    poses: list = field(default_factory=list)       # each pose is a list of (x, y) body points


def route(needs, camera_has_ai, desktop):
    """Decides who does each job. Returns something like {"hands": "processor", "people": "camera"}."""
    unknown = set(needs) - ALL_NEEDS
    if unknown:
        raise ValueError(f"I don't know how to see {sorted(unknown)}. Pick from {sorted(ALL_NEEDS)}.")
    use_camera = camera_has_ai and not desktop
    return {need: "camera" if use_camera and need in CAMERA_CAN_DO else "processor" for need in needs}


def shrink(frame, width):
    """A smaller copy of the picture. The AI doesn't need all those pixels, and small is fast."""
    height, full_width = frame.shape[:2]
    if full_width <= width:
        return frame
    return cv2.resize(frame, (width, int(height * width / full_width)))


class Vision:
    def __init__(self, camera=None, desktop=False, picture_width=640, models_folder=MODELS_FOLDER):
        self.camera = camera
        self.desktop = desktop
        self.picture_width = picture_width
        self.models_folder = models_folder
        self.routes = {}
        self.engines = {}               # the AI models loaded on the processor right now
        self.last_stamp = 0

    def open(self, needs):
        """An app is starting: load exactly what it needs."""
        self.close()
        self.routes = route(needs, getattr(self.camera, "has_ai", False), self.desktop)
        if "pose" in self.routes and self.routes["pose"] == "camera":
            self.camera.use_ai("pose")
        elif "camera" in self.routes.values():
            self.camera.use_ai("detect")
        for need, who in self.routes.items():
            if who == "processor":
                kind = "objects" if need == "people" else need
                if kind not in self.engines:
                    self.engines[kind] = self._load(kind)

    def close(self):
        """An app is closing: let its AI models go."""
        for engine in self.engines.values():
            engine.close()
        self.engines = {}
        self.routes = {}

    def _load(self, kind):
        file_name = MODEL_FOR[kind][0]
        model = self.models_folder / file_name
        if not model.exists():
            raise MissingModel(f"The AI model {file_name} is missing. "
                               f"Run: python setup/download_models.py {kind}")
        import mediapipe as mp          # imported here so apps without AI start instantly
        vision, base = mp.tasks.vision, mp.tasks.BaseOptions(model_asset_path=str(model))
        video = vision.RunningMode.VIDEO
        if kind == "hands":
            return vision.GestureRecognizer.create_from_options(
                vision.GestureRecognizerOptions(base_options=base, running_mode=video, num_hands=1))
        if kind == "faces":
            return vision.FaceDetector.create_from_options(
                vision.FaceDetectorOptions(base_options=base, running_mode=video,
                                           min_detection_confidence=0.6))
        if kind == "pose":
            return vision.PoseLandmarker.create_from_options(
                vision.PoseLandmarkerOptions(base_options=base, running_mode=video, num_poses=2))
        return vision.ObjectDetector.create_from_options(
            vision.ObjectDetectorOptions(base_options=base, running_mode=video, score_threshold=0.4))

    def look(self, frame):
        """Runs the AI the current app asked for on one picture. Returns a Seen."""
        seen = Seen()
        if frame is None or not self.routes:
            return seen

        if "camera" in self.routes.values():          # the AI Camera already did this part
            from_chip = self.camera.ai_seen()
            things = [Thing(name, score, box) for name, score, box in from_chip.get("objects", [])]
            if self.routes.get("objects") == "camera":
                seen.objects = things
            if self.routes.get("people") == "camera":
                seen.people = [thing for thing in things if thing.name == "person"]
            if self.routes.get("pose") == "camera":
                seen.poses = from_chip.get("poses", [])

        if self.engines:
            import mediapipe as mp
            small = shrink(frame, self.picture_width)
            height, width = small.shape[:2]
            rgb = cv2.cvtColor(small, cv2.COLOR_BGR2RGB)      # the AI wants colors in RGB order
            image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb)
            stamp = max(int(time.monotonic() * 1000), self.last_stamp + 1)   # must always go up
            self.last_stamp = stamp

            def as_thing(found, name=None):
                box = found.bounding_box
                return Thing(name or found.categories[0].category_name, found.categories[0].score,
                             (box.origin_x / width, box.origin_y / height,
                              box.width / width, box.height / height))

            if "hands" in self.engines:
                result = self.engines["hands"].recognize_for_video(image, stamp)
                for points, guesses in zip(result.hand_landmarks, result.gestures):
                    seen.hands.append(Hand(guesses[0].category_name, guesses[0].score,
                                           [(p.x, p.y) for p in points]))
            if "faces" in self.engines:
                result = self.engines["faces"].detect_for_video(image, stamp)
                seen.faces = [as_thing(face, "face") for face in result.detections]
            if "pose" in self.engines:
                result = self.engines["pose"].detect_for_video(image, stamp)
                seen.poses = [[(p.x, p.y) for p in body] for body in result.pose_landmarks]
            if "objects" in self.engines:
                result = self.engines["objects"].detect_for_video(image, stamp)
                things = [as_thing(found) for found in result.detections]
                if "objects" in self.routes:
                    seen.objects = things
                if "people" in self.routes:
                    seen.people = [thing for thing in things if thing.name == "person"]
        return seen


class FakeVision:
    """Pretend eyes for tests: it "sees" whatever the test tells it to."""

    def __init__(self, seen_list=None):
        self.seen_list = list(seen_list or [])
        self.opened_with = None

    def open(self, needs):
        route(needs, False, True)                     # still complain about needs that don't exist
        self.opened_with = set(needs)

    def close(self):
        self.opened_with = None

    def look(self, frame):
        return self.seen_list.pop(0) if self.seen_list else Seen()
