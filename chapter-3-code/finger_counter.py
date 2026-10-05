# Chapter 3, Step 5: Finger Counter
# The AI finds 21 points on your hand. We use them to count your fingers
# and send the number (0 to 5) to the Arduino.
# Click the camera window and press Q to quit.

from pathlib import Path
import glob
import math
import time

import cv2
import mediapipe as mp
import serial

CAMERA = 0              # if your iPhone's camera opens instead, change this to 1
HOLD_SECONDS = 0.5      # hold the same number this long before it counts

# The 21 hand points: 0 = wrist, 4 = thumb tip, 8 = index tip,
# 12 = middle tip, 16 = ring tip, 20 = pinky tip.
FINGER_TIPS_AND_JOINTS = [(8, 6), (12, 10), (16, 14), (20, 18)]   # index, middle, ring, pinky
HAND_LINES = [(0, 1), (1, 2), (2, 3), (3, 4), (0, 5), (5, 6), (6, 7), (7, 8),
              (5, 9), (9, 10), (10, 11), (11, 12), (9, 13), (13, 14), (14, 15),
              (15, 16), (13, 17), (17, 18), (18, 19), (19, 20), (0, 17)]


def connect_to_arduino():
    ports = (glob.glob("/dev/cu.usbmodem*") + glob.glob("/dev/cu.usbserial*")
             + glob.glob("/dev/cu.wchusbserial*"))
    if not ports:
        raise SystemExit("No Arduino found. Is the USB cable plugged in?")
    try:
        arduino = serial.Serial(ports[0], 9600)
    except serial.SerialException:
        raise SystemExit("The Arduino is busy. Close the Serial Monitor, then try again.")
    print("Connected to the Arduino on", ports[0])
    time.sleep(2)          # the Arduino restarts when we connect, so give it a moment
    return arduino


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


HAND_MODEL = Path(__file__).parent / "gesture_recognizer.task"
if not HAND_MODEL.exists():
    raise SystemExit("Missing the hand model. Do Step 1 (download the AI models) first.")

options = mp.tasks.vision.GestureRecognizerOptions(
    base_options=mp.tasks.BaseOptions(model_asset_path=str(HAND_MODEL)),
    running_mode=mp.tasks.vision.RunningMode.VIDEO,
    num_hands=1,
)
hand_ai = mp.tasks.vision.GestureRecognizer.create_from_options(options)
arduino = connect_to_arduino()
camera = cv2.VideoCapture(CAMERA)

sent = None             # the last number we sent to the Arduino
candidate = None        # the number we are seeing right now
candidate_since = 0.0   # when we started seeing it
last_hand = 0.0         # when we last saw a hand

while True:
    ok, frame = camera.read()
    if not ok:
        print("Can't read the camera. See 'Camera won't open' in Troubleshooting.")
        break

    frame = cv2.flip(frame, 1)
    height, width = frame.shape[:2]
    rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb)
    result = hand_ai.recognize_for_video(image, int(time.monotonic() * 1000))
    now = time.monotonic()

    count = None
    if result.hand_landmarks:
        hand = result.hand_landmarks[0]
        points = [(int(p.x * width), int(p.y * height)) for p in hand]
        draw_hand(frame, points)
        count = sum(fingers_up(points))
        last_hand = now

    # Only send a number after it stays the same for HOLD_SECONDS
    if count != candidate:
        candidate = count
        candidate_since = now
    elif count is not None and count != sent and now - candidate_since >= HOLD_SECONDS:
        arduino.write(str(count).encode())
        print("Sent", count)
        sent = count

    # Hand gone for a second: put the robot back to waiting
    if count is None and sent is not None and now - last_hand > 1:
        arduino.write(b"N")
        print("Hand gone. Sent N")
        sent = None

    label = "Show me your hand!" if count is None else f"Fingers: {count}"
    cv2.putText(frame, label, (30, 70), cv2.FONT_HERSHEY_SIMPLEX, 2, (0, 255, 255), 4)
    cv2.imshow("Finger Counter - press Q to quit", frame)
    if cv2.waitKey(1) & 0xFF == ord("q"):
        break

arduino.write(b"N")
arduino.close()
camera.release()
cv2.destroyAllWindows()
