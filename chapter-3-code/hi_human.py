# Chapter 3, Bonus: Hi Human!
# Everything at once: the camera finds faces AND hands, guesses how old each
# face looks, and the Mac says "Hi Human" out loud when a face shows up.
# The age guess is only a GROUP (like 25-32), and it is often wrong.
# No Arduino needed. Click the camera window and press Q to quit.

from pathlib import Path
import math
import subprocess
import time

import cv2
import mediapipe as mp
import numpy as np

CAMERA = 0              # if your iPhone's camera opens instead, change this to 1
MAX_HANDS = 2           # how many hands to look for
GREETING = "Hi Human"   # what the Mac says when it sees a face
STAY_GONE_SECONDS = 3   # the face must be gone this long before the Mac says hi again
SMOOTHING = 0.9         # closer to 1 = the age guess changes more slowly (less flicker)

# The age AI can only answer with one of these 8 groups
AGE_GROUPS = ["0-2", "4-6", "8-12", "15-20", "25-32", "38-43", "48-53", "60+"]

# The 21 hand points: 0 = wrist, 4 = thumb tip, 8 = index tip,
# 12 = middle tip, 16 = ring tip, 20 = pinky tip.
FINGER_TIPS_AND_JOINTS = [(8, 6), (12, 10), (16, 14), (20, 18)]   # index, middle, ring, pinky
HAND_LINES = [(0, 1), (1, 2), (2, 3), (3, 4), (0, 5), (5, 6), (6, 7), (7, 8),
              (5, 9), (9, 10), (10, 11), (11, 12), (9, 13), (13, 14), (14, 15),
              (15, 16), (13, 17), (17, 18), (18, 19), (19, 20), (0, 17)]


def say_out_loud(words):
    # "say" is the Mac's built-in voice. Popen doesn't wait, so the video keeps moving.
    subprocess.Popen(["say", words])                 # a list, never shell=True


def fingers_up(points):
    """Returns 5 True/False values: thumb, index, middle, ring, pinky. True = up."""
    def far(a, b):
        return math.dist(points[a], points[b])
    # Thumb: up if its tip is farther from the pinky knuckle (17) than its middle joint (3) is
    thumb = far(4, 17) > far(3, 17)
    # Other fingers: up if the tip is farther from the wrist (0) than the middle joint is
    others = [far(tip, 0) > far(joint, 0) for tip, joint in FINGER_TIPS_AND_JOINTS]
    return [thumb] + others


def draw_hand(frame, points):
    for a, b in HAND_LINES:
        cv2.line(frame, points[a], points[b], (255, 255, 255), 3)
    for point in points:
        cv2.circle(frame, point, 7, (255, 0, 255), -1)


def guess_age(frame, box):
    """Cuts the face out of the picture and returns 8 scores, one for each age group."""
    height, width = frame.shape[:2]
    # Take a bit more than the box, so the AI also sees hair and chin
    pad = int(box.width * 0.3)
    left, top = max(box.origin_x - pad, 0), max(box.origin_y - pad, 0)
    right = min(box.origin_x + box.width + pad, width)
    bottom = min(box.origin_y + box.height + pad, height)
    if right <= left or bottom <= top:
        return None
    face = frame[top:bottom, left:right]
    # The age AI wants a 224x224 picture with these color numbers subtracted
    blob = cv2.dnn.blobFromImage(face, 1.0, (224, 224), (104, 117, 123))
    age_ai.setInput(blob)
    return age_ai.forward()[0]


FACE_MODEL = Path(__file__).parent / "blaze_face_short_range.tflite"
HAND_MODEL = Path(__file__).parent / "gesture_recognizer.task"
AGE_MODEL = Path(__file__).parent / "age_googlenet.onnx"
if not FACE_MODEL.exists() or not HAND_MODEL.exists():
    raise SystemExit("Missing an AI model. Do Step 1 (download the AI models) first.")
if not AGE_MODEL.exists():
    raise SystemExit("Missing the age model. Download it with:\n"
                     "curl -L -O https://github.com/onnx/models/raw/main/validated/vision/"
                     "body_analysis/age_gender/models/age_googlenet.onnx")

face_options = mp.tasks.vision.FaceDetectorOptions(
    base_options=mp.tasks.BaseOptions(model_asset_path=str(FACE_MODEL)),
    running_mode=mp.tasks.vision.RunningMode.VIDEO,
    min_detection_confidence=0.6,      # how sure the AI must be before it says "face"
)
hand_options = mp.tasks.vision.GestureRecognizerOptions(
    base_options=mp.tasks.BaseOptions(model_asset_path=str(HAND_MODEL)),
    running_mode=mp.tasks.vision.RunningMode.VIDEO,
    num_hands=MAX_HANDS,
)
face_finder = mp.tasks.vision.FaceDetector.create_from_options(face_options)
hand_ai = mp.tasks.vision.GestureRecognizer.create_from_options(hand_options)
age_ai = cv2.dnn.readNetFromONNX(str(AGE_MODEL))
camera = cv2.VideoCapture(CAMERA)

greeted = False         # have we already said hi to this face?
last_seen = 0.0         # when did we last see a face?
smooth_scores = []      # one running average of the 8 age scores for each face on screen

while True:
    ok, frame = camera.read()
    if not ok:
        print("Can't read the camera. See 'Camera won't open' in Troubleshooting.")
        break

    frame = cv2.flip(frame, 1)                       # mirror it, like a selfie
    height, width = frame.shape[:2]
    rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)     # the AI wants colors in RGB order
    image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb)

    # Both AIs look at the same picture
    now_ms = int(time.monotonic() * 1000)
    found = face_finder.detect_for_video(image, now_ms)
    hands = hand_ai.recognize_for_video(image, now_ms)
    now = time.monotonic()

    # Say hi once when a face shows up. Say it again only after the face has been gone a while.
    if found.detections:
        last_seen = now
        if not greeted:
            say_out_loud(GREETING)
            print("Face!", GREETING)
            greeted = True
    elif greeted and now - last_seen > STAY_GONE_SECONDS:
        print("Gone.")
        greeted = False

    # Go through the faces from left to right, so each one keeps its own age average
    faces = sorted(found.detections, key=lambda face: face.bounding_box.origin_x)
    if len(faces) != len(smooth_scores):
        smooth_scores = [None] * len(faces)          # someone came or left: start over

    for i, face in enumerate(faces):
        box = face.bounding_box
        cv2.rectangle(frame, (box.origin_x, box.origin_y),
                      (box.origin_x + box.width, box.origin_y + box.height), (0, 255, 0), 4)
        scores = guess_age(frame, box)
        if scores is None:
            continue
        # Mix the new guess into the average so the label doesn't jump around
        if smooth_scores[i] is None:
            smooth_scores[i] = scores
        else:
            smooth_scores[i] = SMOOTHING * smooth_scores[i] + (1 - SMOOTHING) * scores
        best = int(np.argmax(smooth_scores[i]))
        sure = smooth_scores[i][best]                 # 0.0 to 1.0
        cv2.putText(frame, f"Age {AGE_GROUPS[best]}? ({sure:.0%} sure)",
                    (box.origin_x, box.origin_y - 12),
                    cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)

    total_fingers = 0
    for hand in hands.hand_landmarks:
        points = [(int(p.x * width), int(p.y * height)) for p in hand]
        draw_hand(frame, points)
        count = sum(fingers_up(points))
        total_fingers += count
        # Write this hand's count next to its wrist (point 0)
        cv2.putText(frame, str(count), (points[0][0] - 20, points[0][1] + 60),
                    cv2.FONT_HERSHEY_SIMPLEX, 2, (255, 0, 255), 4)

    status = f"{GREETING}!" if greeted else "Waiting for a face..."
    cv2.putText(frame, status, (30, 70), cv2.FONT_HERSHEY_SIMPLEX, 2, (0, 255, 255), 4)
    cv2.putText(frame, f"Faces: {len(faces)}  Hands: {len(hands.hand_landmarks)}  "
                f"Fingers: {total_fingers}", (30, 130),
                cv2.FONT_HERSHEY_SIMPLEX, 1.2, (0, 255, 255), 3)
    cv2.imshow("Hi Human - press Q to quit", frame)
    if cv2.waitKey(1) & 0xFF == ord("q"):
        break

camera.release()
cv2.destroyAllWindows()
