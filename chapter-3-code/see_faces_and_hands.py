# Chapter 3, Bonus: Robot Eyes + Hands
# The MacBook camera finds faces AND hands at the same time.
# It draws a box around each face, and dots on each hand with a finger count.
# No Arduino needed. Click the camera window and press Q to quit.

from pathlib import Path
import math
import time

import cv2
import mediapipe as mp

CAMERA = 0      # if your iPhone's camera opens instead, change this to 1
MAX_HANDS = 2   # how many hands to look for

# The 21 hand points: 0 = wrist, 4 = thumb tip, 8 = index tip,
# 12 = middle tip, 16 = ring tip, 20 = pinky tip.
FINGER_TIPS_AND_JOINTS = [(8, 6), (12, 10), (16, 14), (20, 18)]   # index, middle, ring, pinky
HAND_LINES = [(0, 1), (1, 2), (2, 3), (3, 4), (0, 5), (5, 6), (6, 7), (7, 8),
              (5, 9), (9, 10), (10, 11), (11, 12), (9, 13), (13, 14), (14, 15),
              (15, 16), (13, 17), (17, 18), (18, 19), (19, 20), (0, 17)]


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


FACE_MODEL = Path(__file__).parent / "blaze_face_short_range.tflite"
HAND_MODEL = Path(__file__).parent / "gesture_recognizer.task"
if not FACE_MODEL.exists() or not HAND_MODEL.exists():
    raise SystemExit("Missing an AI model. Do Step 1 (download the AI models) first.")

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
camera = cv2.VideoCapture(CAMERA)

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
    faces = face_finder.detect_for_video(image, now_ms)
    hands = hand_ai.recognize_for_video(image, now_ms)

    for face in faces.detections:
        box = face.bounding_box
        sure = face.categories[0].score               # 0.0 to 1.0
        cv2.rectangle(frame, (box.origin_x, box.origin_y),
                      (box.origin_x + box.width, box.origin_y + box.height), (0, 255, 0), 4)
        cv2.putText(frame, f"{sure:.0%} sure", (box.origin_x, box.origin_y - 12),
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

    cv2.putText(frame, f"Faces: {len(faces.detections)}", (30, 70),
                cv2.FONT_HERSHEY_SIMPLEX, 2, (0, 255, 255), 4)
    cv2.putText(frame, f"Hands: {len(hands.hand_landmarks)}  Fingers: {total_fingers}", (30, 140),
                cv2.FONT_HERSHEY_SIMPLEX, 2, (0, 255, 255), 4)
    cv2.imshow("Robot Eyes + Hands - press Q to quit", frame)
    if cv2.waitKey(1) & 0xFF == ord("q"):
        break

camera.release()
cv2.destroyAllWindows()
