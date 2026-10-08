# Chapter 3, Bonus: Gesture Talk
# The AI knows 7 hand gestures: peace, thumbs up, thumbs down, open hand,
# fist, pointing up, and "I love you". Show one and the Mac answers out loud.
# Arduino plugged in: the robot shows the gesture on its screen and beeps too.
# No Arduino: it still works, just with the Mac's voice.
# Click the camera window and press Q to quit.

from pathlib import Path
import glob
import subprocess
import time

import cv2
import mediapipe as mp
import serial

CAMERA = 0              # if your iPhone's camera opens instead, change this to 1
HOLD_SECONDS = 0.5      # hold the same gesture this long before it counts
HOW_SURE = 0.5          # how sure the AI must be (0.0 to 1.0)

# What the AI calls each gesture: (its name on screen, what the Mac says, the letter for the Arduino)
# Change the words! Keep the letters the same as in robot_brain.ino.
GESTURES = {
    "Victory":     ("Peace",       "Peace!",           b"V"),
    "Thumb_Up":    ("Thumbs up",   "Awesome!",         b"U"),
    "Thumb_Down":  ("Thumbs down", "Oh no!",           b"D"),
    "Open_Palm":   ("Open hand",   "High five!",       b"H"),
    "Closed_Fist": ("Fist",        "Fist bump!",       b"B"),
    "Pointing_Up": ("Pointing up", "You are number one!", b"O"),
    "ILoveYou":    ("I love you",  "I love you too!",  b"L"),
}

HAND_LINES = [(0, 1), (1, 2), (2, 3), (3, 4), (0, 5), (5, 6), (6, 7), (7, 8),
              (5, 9), (9, 10), (10, 11), (11, 12), (9, 13), (13, 14), (14, 15),
              (15, 16), (13, 17), (17, 18), (18, 19), (19, 20), (0, 17)]


def connect_to_arduino():
    """Returns the Arduino, or None if there isn't one (then only the Mac answers)."""
    ports = (glob.glob("/dev/cu.usbmodem*") + glob.glob("/dev/cu.usbserial*")
             + glob.glob("/dev/cu.wchusbserial*"))
    if not ports:
        print("No Arduino found, so only the Mac will answer.")
        return None
    try:
        arduino = serial.Serial(ports[0], 9600)
    except serial.SerialException:
        raise SystemExit("The Arduino is busy. Close the Serial Monitor, then try again.")
    print("Connected to the Arduino on", ports[0])
    time.sleep(2)          # the Arduino restarts when we connect, so give it a moment
    return arduino


def say_out_loud(words):
    # "say" is the Mac's built-in voice. Popen doesn't wait, so the video keeps moving.
    subprocess.Popen(["say", words])                 # a list, never shell=True


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

answered = None         # the last gesture we answered
candidate = None        # the gesture we are seeing right now
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

    gesture = None
    ai_says = "no hand"
    if result.hand_landmarks:
        points = [(int(p.x * width), int(p.y * height)) for p in result.hand_landmarks[0]]
        draw_hand(frame, points)
        last_hand = now
    if result.gestures:
        best_guess = result.gestures[0][0]           # the AI's best guess for this hand
        ai_says = f"{best_guess.category_name} ({best_guess.score:.0%})"
        if best_guess.score >= HOW_SURE and best_guess.category_name in GESTURES:
            gesture = best_guess.category_name

    # Only answer after the gesture stays the same for HOLD_SECONDS
    if gesture != candidate:
        candidate = gesture
        candidate_since = now
    elif gesture is not None and gesture != answered and now - candidate_since >= HOLD_SECONDS:
        name, words, letter = GESTURES[gesture]
        say_out_loud(words)
        if arduino:
            arduino.write(letter)
        print(f"{name}: {words}")
        answered = gesture

    # Hand gone for a second: forget the gesture and put the robot back to waiting
    if not result.hand_landmarks and answered is not None and now - last_hand > 1:
        if arduino:
            arduino.write(b"N")
        print("Hand gone.")
        answered = None

    if answered:
        name, words, letter = GESTURES[answered]
        label = f"{name}: {words}"
    else:
        label = "Show me a gesture!"
    cv2.putText(frame, label, (30, 70), cv2.FONT_HERSHEY_SIMPLEX, 1.6, (0, 255, 255), 4)
    cv2.putText(frame, "AI sees: " + ai_says, (30, 130), cv2.FONT_HERSHEY_SIMPLEX, 1.1, (255, 255, 0), 3)
    cv2.imshow("Gesture Talk - press Q to quit", frame)
    if cv2.waitKey(1) & 0xFF == ord("q"):
        break

if arduino:
    arduino.write(b"N")    # leave the robot in its waiting screen
    arduino.close()
camera.release()
cv2.destroyAllWindows()
