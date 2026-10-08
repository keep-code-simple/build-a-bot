# Chapter 3, Bonus: Hi Human, let's play!
# Everything at once: the camera finds faces AND hands, guesses how old each
# face looks, says "Hi Human" out loud when a face shows up, and plays
# Rock Paper Scissors: fist = rock, open hand = paper, peace sign = scissors.
# Arduino plugged in (with robot_brain.ino on it): the robot also greets the face on
# its screen, picks its own move, and keeps score, like in Steps 4 and 6.
# No Arduino: the Mac picks a move, says who won, and keeps score on screen.
# Click the camera window and press Q to quit.

from pathlib import Path
import glob
import math
import random
import subprocess
import time

import cv2
import mediapipe as mp
import numpy as np
import serial

CAMERA = 0              # if your iPhone's camera opens instead, change this to 1
MAX_HANDS = 2           # how many hands to look for
GREETING = "Hi Human"   # what the Mac says when it sees a face
STAY_GONE_SECONDS = 3   # the face must be gone this long before the Mac says hi again
SMOOTHING = 0.9         # closer to 1 = the age guess changes more slowly (less flicker)
HOLD_SECONDS = 0.6      # hold your move this long before it counts
ROBOT_TURN_SECONDS = 5  # how long the robot (or the Mac) needs to play its turn

# The AI already knows these gestures. We turn them into game moves.
GESTURE_TO_MOVE = {"Closed_Fist": "rock", "Open_Palm": "paper", "Victory": "scissors"}
MOVE_TO_LETTER = {"rock": b"r", "paper": b"p", "scissors": b"s"}
BEATS = {"rock": "scissors", "paper": "rock", "scissors": "paper"}   # rock beats scissors...

# The age AI can only answer with one of these 8 groups
AGE_GROUPS = ["0-2", "4-6", "8-12", "15-20", "25-32", "38-43", "48-53", "60+"]

# The 21 hand points: 0 = wrist, 4 = thumb tip, 8 = index tip,
# 12 = middle tip, 16 = ring tip, 20 = pinky tip.
FINGER_TIPS_AND_JOINTS = [(8, 6), (12, 10), (16, 14), (20, 18)]   # index, middle, ring, pinky
HAND_LINES = [(0, 1), (1, 2), (2, 3), (3, 4), (0, 5), (5, 6), (6, 7), (7, 8),
              (5, 9), (9, 10), (10, 11), (11, 12), (9, 13), (13, 14), (14, 15),
              (15, 16), (13, 17), (17, 18), (18, 19), (19, 20), (0, 17)]


def connect_to_arduino():
    """Returns the Arduino, or None if there isn't one (then the Mac plays instead)."""
    ports = (glob.glob("/dev/cu.usbmodem*") + glob.glob("/dev/cu.usbserial*")
             + glob.glob("/dev/cu.wchusbserial*"))
    if not ports:
        print("No Arduino found, so the Mac will play Rock Paper Scissors against you.")
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
arduino = connect_to_arduino()
camera = cv2.VideoCapture(CAMERA)

greeted = False         # have we already said hi to this face?
last_seen = 0.0         # when did we last see a face?
smooth_scores = []      # one running average of the 8 age scores for each face on screen

candidate = None          # the move we are seeing right now
candidate_since = 0.0     # when we started seeing it
robot_busy_until = 0.0    # the robot is playing its turn until this time
need_empty_hand = False   # after a round, pull your hand away before the next one
round_result = ""         # who won the last round (only when the Mac is playing)
you_score = 0             # the score (only when the Mac is playing)
mac_score = 0

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
    # We wait until the robot has finished its turn, so we don't wipe the score off its screen.
    robot_is_free = now >= robot_busy_until
    if found.detections:
        last_seen = now
        if not greeted and robot_is_free:
            say_out_loud(GREETING)
            if arduino:
                arduino.write(b"F")                  # tell the Arduino: say hi!
            print("Face!", GREETING)
            greeted = True
    elif greeted and robot_is_free and now - last_seen > STAY_GONE_SECONDS:
        if arduino:
            arduino.write(b"N")                      # tell the Arduino: nobody here
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

    # Rock Paper Scissors: the first hand the AI found is the one that plays
    move = None
    ai_says = "no hand"
    if hands.gestures:
        best_guess = hands.gestures[0][0]            # the AI's best guess for this hand
        ai_says = f"{best_guess.category_name} ({best_guess.score:.0%})"
        if best_guess.score >= 0.5:
            move = GESTURE_TO_MOVE.get(best_guess.category_name)

    if now < robot_busy_until:
        message = round_result or "Look at the robot!"
    elif need_empty_hand:
        message = "Hand away... then go again"
        if not hands.hand_landmarks:
            need_empty_hand = False
    else:
        message = "Rock, paper or scissors?"
        if move != candidate:
            candidate = move
            candidate_since = now
        elif move is not None and now - candidate_since >= HOLD_SECONDS:
            print("You played", move)
            if arduino:
                arduino.write(MOVE_TO_LETTER[move])  # send your move to the robot
            else:
                mac_move = random.choice(list(BEATS))   # the Mac picks without peeking
                if mac_move == move:
                    winner = "It's a tie"
                elif BEATS[move] == mac_move:
                    winner = "You win"
                    you_score += 1
                else:
                    winner = "I win"
                    mac_score += 1
                round_result = f"Mac: {mac_move}. {winner}!"
                say_out_loud(f"I pick {mac_move}. {winner}!")
                print(round_result, f"Score: you {you_score}, Mac {mac_score}")
            robot_busy_until = now + ROBOT_TURN_SECONDS
            need_empty_hand = True
            candidate = None

    cv2.putText(frame, message, (30, 70), cv2.FONT_HERSHEY_SIMPLEX, 1.6, (0, 255, 255), 4)
    cv2.putText(frame, "AI sees: " + ai_says, (30, 130), cv2.FONT_HERSHEY_SIMPLEX, 1.1, (255, 255, 0), 3)
    status = f"{GREETING}!" if greeted else "Waiting for a face..."
    cv2.putText(frame, f"{status}  Faces: {len(faces)}  Fingers: {total_fingers}", (30, 180),
                cv2.FONT_HERSHEY_SIMPLEX, 1.1, (0, 255, 255), 3)
    if not arduino:
        cv2.putText(frame, f"You {you_score} - Mac {mac_score}", (30, height - 30),
                    cv2.FONT_HERSHEY_SIMPLEX, 1.6, (0, 255, 255), 4)
    cv2.imshow("Hi Human, let's play - press Q to quit", frame)
    if cv2.waitKey(1) & 0xFF == ord("q"):
        break

if arduino:
    arduino.write(b"N")    # leave the robot in its waiting screen
    arduino.close()
camera.release()
cv2.destroyAllWindows()
