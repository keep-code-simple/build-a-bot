# Chapter 3, Step 6: Rock Paper Scissors vs the Robot
# The AI recognizes your hand: fist = rock, open hand = paper, peace sign = scissors.
# The Arduino picks its own move, shows who won, and keeps score.
# Click the camera window and press Q to quit.

from pathlib import Path
import glob
import time

import cv2
import mediapipe as mp
import serial

CAMERA = 0                # if your iPhone's camera opens instead, change this to 1
HOLD_SECONDS = 0.6        # hold your move this long before it counts
ROBOT_TURN_SECONDS = 5    # how long the robot needs to play its turn

# The AI already knows these gestures. We turn them into game moves.
GESTURE_TO_MOVE = {"Closed_Fist": "rock", "Open_Palm": "paper", "Victory": "scissors"}
MOVE_TO_LETTER = {"rock": b"r", "paper": b"p", "scissors": b"s"}

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

candidate = None          # the move we are seeing right now
candidate_since = 0.0     # when we started seeing it
robot_busy_until = 0.0    # the robot is playing its turn until this time
need_empty_hand = False   # after a round, pull your hand away before the next one

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

    move = None
    ai_says = "no hand"
    if result.hand_landmarks:
        points = [(int(p.x * width), int(p.y * height)) for p in result.hand_landmarks[0]]
        draw_hand(frame, points)
    if result.gestures:
        best_guess = result.gestures[0][0]           # the AI's best guess for this hand
        ai_says = f"{best_guess.category_name} ({best_guess.score:.0%})"
        if best_guess.score >= 0.5:
            move = GESTURE_TO_MOVE.get(best_guess.category_name)

    if now < robot_busy_until:
        message = "Look at the robot!"
    elif need_empty_hand:
        message = "Hand away... then go again"
        if not result.hand_landmarks:
            need_empty_hand = False
    else:
        message = "Rock, paper or scissors?"
        if move != candidate:
            candidate = move
            candidate_since = now
        elif move is not None and now - candidate_since >= HOLD_SECONDS:
            arduino.write(MOVE_TO_LETTER[move])      # send your move to the robot
            print("You played", move)
            robot_busy_until = now + ROBOT_TURN_SECONDS
            need_empty_hand = True
            candidate = None

    cv2.putText(frame, message, (30, 70), cv2.FONT_HERSHEY_SIMPLEX, 1.6, (0, 255, 255), 4)
    cv2.putText(frame, "AI sees: " + ai_says, (30, 130), cv2.FONT_HERSHEY_SIMPLEX, 1.1, (255, 255, 0), 3)
    cv2.imshow("Rock Paper Scissors - press Q to quit", frame)
    if cv2.waitKey(1) & 0xFF == ord("q"):
        break

arduino.close()
camera.release()
cv2.destroyAllWindows()
