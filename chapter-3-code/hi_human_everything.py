# Chapter 3, Bonus: Hi Human, everything!
# Everything at once: the camera finds faces AND hands, guesses how old each
# face looks, says "Hi Human" out loud when a face shows up, plays
# Rock Paper Scissors, and answers your hand gestures AND the faces you make.
#   Game:    fist = rock, open hand = paper, peace sign = scissors
#   Talking: thumbs up, thumbs down, pointing up, "I love you"
#   Faces:   smile, open mouth, wink, eyebrows up
#   Voice:   say "tell me a joke" and the robot tells one of its 24 jokes.
#            Say "another one" for the next joke.
# The listening happens on this Mac. Nothing you say is saved or sent anywhere.
# The first time, the Mac asks if Terminal may use the microphone: say yes.
# Arduino plugged in (with robot_brain.ino on it): the robot greets the face,
# picks its move, keeps score, and shows your gestures and faces.
# No Arduino: the Mac picks a move, says who won, and keeps score on screen.
# Click the camera window and press Q to quit.

from pathlib import Path
import glob
import json
import math
import queue
import random
import subprocess
import time

import cv2
import mediapipe as mp
import numpy as np
import serial
import sounddevice
import vosk

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

# The other gestures get an answer: (its name on screen, what the Mac says, the letter for the Arduino)
# Change the words! Keep the letters the same as in robot_brain.ino.
TALK_GESTURES = {
    "Thumb_Up":    ("Thumbs up",   "Awesome!",            b"U"),
    "Thumb_Down":  ("Thumbs down", "Oh no!",              b"D"),
    "Pointing_Up": ("Pointing up", "You are number one!", b"O"),
    "ILoveYou":    ("I love you",  "I love you too!",     b"L"),
}

# Faces you can make: (its name on screen, what the Mac says, the letter for the Arduino)
EXPRESSIONS = {
    "smile":      ("Smile",       "Nice smile!",        b"S"),
    "mouth_open": ("Mouth open",  "Wow!",               b"W"),
    "wink":       ("Wink",        "I saw that wink!",   b"K"),
    "eyebrows":   ("Eyebrows up", "Are you surprised?", b"E"),
}
# How strong each face must be, from 0.0 to 1.0. Make a number bigger if the
# robot sees that face when you aren't making it, smaller if it never sees it.
SMILE_LEVEL = 0.6
MOUTH_OPEN_LEVEL = 0.5
WINK_LEVEL = 0.4          # how much more closed one eye must be than the other
EYEBROWS_LEVEL = 0.7

JOKES = [
    "Why did the robot go on holiday? To recharge its batteries!",
    "What is a robot's favorite snack? Computer chips!",
    "Why was the robot so tired? It had a hard drive!",
    "What do you call a robot that always takes the long way? R 2 detour!",
    "Why did the robot cross the road? It was programmed by the chicken!",
    "What kind of music do robots like? Heavy metal!",
    "Why did the robot get angry? Someone kept pushing its buttons!",
    "What do you get when you cross a robot and a tractor? A transfarmer!",
    "Why did the computer go to the doctor? It had a virus!",
    "Why was the computer cold? It left its Windows open!",
    "How does a robot eat salsa? With micro chips!",
    "What did the robot say to the gas pump? Take your finger out of your ear and listen to me!",
    "Why don't robots ever get scared? They have nerves of steel!",
    "What is a robot's favorite dance? The robot, of course!",
    "Why did the robot sneeze? It had a bad case of the bugs!",
    "What do you call a pirate robot? Arrr 2 D 2!",
    "Why did the scarecrow win a prize? He was outstanding in his field!",
    "What do you call a sleeping dinosaur? A dino snore!",
    "Why can't you give a balloon to Elsa? She will let it go!",
    "What do you call cheese that isn't yours? Nacho cheese!",
    "Why did the banana go to the doctor? It wasn't peeling well!",
    "What has four wheels and flies? A garbage truck!",
    "Why did the student eat his homework? The teacher said it was a piece of cake!",
    "What do you call a bear with no teeth? A gummy bear!",
]
jokes_left = []         # the jokes the robot hasn't told yet this time around


def next_joke():
    """Tells every joke once, in a mixed-up order, before any joke comes again."""
    if not jokes_left:
        jokes_left.extend(random.sample(JOKES, len(JOKES)))
    return jokes_left.pop()

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


voice = None            # the Mac's voice, while it is talking


def say_out_loud(words):
    # "say" is the Mac's built-in voice. Popen doesn't wait, so the video keeps moving.
    global voice
    voice = subprocess.Popen(["say", words])         # a list, never shell=True


def mac_is_talking():
    return voice is not None and voice.poll() is None


def heard_any(heard, *things):
    """True if you said any of these. One word must match a whole word, so "hi" isn't found in "this"."""
    words = heard.split()
    return any(thing in heard if " " in thing else thing in words for thing in things)


def think_of_answer(heard):
    """Takes what you said and returns what the robot says back: a joke, if you asked for one.
    Returns None for anything else."""
    if heard_any(heard, "joke", "jokes", "funny", "another one", "one more", "make me laugh"):
        return next_joke()
    return None


sound_queue = queue.Queue()     # little pieces of sound from the microphone wait here
deaf_until = 0.0                # the robot doesn't listen until this time


def microphone_heard(sound, frames, when, status):
    sound_queue.put(bytes(sound))


def listen():
    """Returns the words you just finished saying, or "" if you are quiet or still talking."""
    global deaf_until
    heard = ""
    while not sound_queue.empty():
        sound = sound_queue.get()
        if mac_is_talking():
            deaf_until = time.monotonic() + 0.5      # don't let the robot hear its own voice
        if time.monotonic() < deaf_until:
            ears.Reset()
        elif ears.AcceptWaveform(sound):             # True when you stop talking
            heard = json.loads(ears.Result())["text"] or heard
    return heard


def read_expression(levels):
    """Takes the face AI's numbers (like how much the mouth smiles) and names the face you made."""
    left_eye, right_eye = levels["eyeBlinkLeft"], levels["eyeBlinkRight"]
    if abs(left_eye - right_eye) >= WINK_LEVEL:      # one eye closed, the other open
        return "wink"
    if levels["jawOpen"] >= MOUTH_OPEN_LEVEL:
        return "mouth_open"
    if (levels["mouthSmileLeft"] + levels["mouthSmileRight"]) / 2 >= SMILE_LEVEL:
        return "smile"
    if levels["browInnerUp"] >= EYEBROWS_LEVEL:
        return "eyebrows"
    return None


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
EXPRESSION_MODEL = Path(__file__).parent / "face_landmarker.task"
if not EXPRESSION_MODEL.exists():
    raise SystemExit("Missing the face expression model. Download it with:\n"
                     "curl -L -O https://storage.googleapis.com/mediapipe-models/face_landmarker/"
                     "face_landmarker/float16/1/face_landmarker.task")
EARS_MODEL = Path(__file__).parent / "vosk-model-small-en-us-0.15"
if not EARS_MODEL.exists():
    raise SystemExit("Missing the listening model. Download it with:\n"
                     "curl -L -O https://alphacephei.com/vosk/models/vosk-model-small-en-us-0.15.zip\n"
                     "unzip vosk-model-small-en-us-0.15.zip")
if not AGE_MODEL.exists():
    raise SystemExit("Missing the age model. Download it with:\n"
                     "curl -L -O https://github.com/onnx/models/raw/main/validated/vision/"
                     "body_analysis/age_gender/models/age_googlenet.onnx")

# The listening AI must be loaded BEFORE the seeing AIs, or the program crashes.
vosk.SetLogLevel(-1)                                 # keep the listening AI from filling the Terminal
ears = vosk.KaldiRecognizer(vosk.Model(str(EARS_MODEL)), 16000)

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
expression_options = mp.tasks.vision.FaceLandmarkerOptions(
    base_options=mp.tasks.BaseOptions(model_asset_path=str(EXPRESSION_MODEL)),
    running_mode=mp.tasks.vision.RunningMode.VIDEO,
    output_face_blendshapes=True,      # ask for the "how much is it smiling" numbers
    num_faces=1,
)
face_finder = mp.tasks.vision.FaceDetector.create_from_options(face_options)
expression_ai = mp.tasks.vision.FaceLandmarker.create_from_options(expression_options)
hand_ai = mp.tasks.vision.GestureRecognizer.create_from_options(hand_options)
age_ai = cv2.dnn.readNetFromONNX(str(AGE_MODEL))
microphone = sounddevice.RawInputStream(samplerate=16000, blocksize=4000, dtype="int16",
                                        channels=1, callback=microphone_heard)
microphone.start()
arduino = connect_to_arduino()
camera = cv2.VideoCapture(CAMERA)

greeted = False         # have we already said hi to this face?
last_seen = 0.0         # when did we last see a face?
smooth_scores = []      # one running average of the 8 age scores for each face on screen

candidate = None          # the gesture we are seeing right now
candidate_since = 0.0     # when we started seeing it
robot_busy_until = 0.0    # the robot is playing its turn until this time
need_empty_hand = False   # after a round, pull your hand away before the next one
round_result = ""         # who won the last round (only when the Mac is playing)
you_score = 0             # the score (only when the Mac is playing)
mac_score = 0
answered = None           # the last talking gesture we answered
last_hand = 0.0           # when we last saw a hand
face_candidate = None     # the face you are making right now
face_candidate_since = 0.0
face_answered = None      # the last face we answered
you_said = ""             # the last thing the robot heard you say
robot_said = ""           # what it answered
talk_until = 0.0          # keep those words on screen until this time

while True:
    ok, frame = camera.read()
    if not ok:
        print("Can't read the camera. See 'Camera won't open' in Troubleshooting.")
        break

    frame = cv2.flip(frame, 1)                       # mirror it, like a selfie
    height, width = frame.shape[:2]
    rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)     # the AI wants colors in RGB order
    image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb)

    # All the AIs look at the same picture
    now_ms = int(time.monotonic() * 1000)
    found = face_finder.detect_for_video(image, now_ms)
    hands = hand_ai.recognize_for_video(image, now_ms)
    looks = expression_ai.detect_for_video(image, now_ms)
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

    # Face gestures: which face is the (first) person making?
    expression = None
    if looks.face_blendshapes:
        levels = {shape.category_name: shape.score for shape in looks.face_blendshapes[0]}
        expression = read_expression(levels)
    if expression != face_candidate:
        face_candidate = expression
        face_candidate_since = now
        if expression is None:
            face_answered = None                     # back to a normal face: ready for the next one
    elif (expression is not None and expression != face_answered
          and now - face_candidate_since >= HOLD_SECONDS
          and robot_is_free and not mac_is_talking()):   # don't talk over the game or the greeting
        name, words, letter = EXPRESSIONS[expression]
        say_out_loud(words)
        if arduino:
            arduino.write(letter)                    # the robot shows the face too
        print(f"{name}: {words}")
        face_answered = expression

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

    # Gestures: the first hand the AI found is the one that plays and talks
    gesture = None
    ai_says = "no hand"
    if hands.hand_landmarks:
        last_hand = now
    if hands.gestures:
        best_guess = hands.gestures[0][0]            # the AI's best guess for this hand
        ai_says = f"{best_guess.category_name} ({best_guess.score:.0%})"
        if best_guess.score >= 0.5:
            gesture = best_guess.category_name
    move = GESTURE_TO_MOVE.get(gesture)              # rock, paper, scissors, or None

    if now < robot_busy_until:
        message = round_result or "Look at the robot!"
    elif need_empty_hand:
        message = "Hand away... then go again"
        if not hands.hand_landmarks:
            need_empty_hand = False
    else:
        message = "Rock, paper or scissors?"
        if answered:
            name, words, letter = TALK_GESTURES[answered]
            message = f"{name}: {words}"
        if gesture != candidate:
            candidate = gesture
            candidate_since = now
        elif now - candidate_since < HOLD_SECONDS:
            pass                                     # keep holding...
        elif gesture in TALK_GESTURES and gesture != answered:
            name, words, letter = TALK_GESTURES[gesture]
            say_out_loud(words)
            if arduino:
                arduino.write(letter)                # the robot shows the gesture too
            print(f"{name}: {words}")
            answered = gesture
        elif move is not None:
            print("You played", move)
            answered = None
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

    # Talking: did you just say something? If you asked for a joke, tell one.
    heard = listen()
    if heard:
        answer = think_of_answer(heard)
        print("You said:", heard)
        if answer:
            say_out_loud(answer)
            print("Robot:", answer)
        you_said, robot_said = heard, answer or 'Say "tell me a joke"!'
        talk_until = now + 8

    # Hand gone for a second: forget the gesture and put the robot back to waiting
    if answered and not hands.hand_landmarks and now - last_hand > 1:
        if arduino:
            arduino.write(b"N")
        answered = None

    cv2.putText(frame, message, (30, 70), cv2.FONT_HERSHEY_SIMPLEX, 1.6, (0, 255, 255), 4)
    cv2.putText(frame, "AI sees: " + ai_says, (30, 130), cv2.FONT_HERSHEY_SIMPLEX, 1.1, (255, 255, 0), 3)
    face_says = EXPRESSIONS[expression][0] if expression else "normal face"
    cv2.putText(frame, "Face: " + face_says, (30, 230), cv2.FONT_HERSHEY_SIMPLEX, 1.1, (255, 255, 0), 3)
    status = f"{GREETING}!" if greeted else "Waiting for a face..."
    cv2.putText(frame, f"{status}  Faces: {len(faces)}  Fingers: {total_fingers}", (30, 180),
                cv2.FONT_HERSHEY_SIMPLEX, 1.1, (0, 255, 255), 3)
    if now < talk_until:
        cv2.putText(frame, "You: " + you_said, (30, height - 140),
                    cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
        cv2.putText(frame, "Robot: " + robot_said, (30, height - 100),
                    cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
    if not arduino:
        cv2.putText(frame, f"You {you_score} - Mac {mac_score}", (30, height - 30),
                    cv2.FONT_HERSHEY_SIMPLEX, 1.6, (0, 255, 255), 4)
    cv2.imshow("Hi Human, everything - press Q to quit", frame)
    if cv2.waitKey(1) & 0xFF == ord("q"):
        break

if arduino:
    arduino.write(b"N")    # leave the robot in its waiting screen
    arduino.close()
microphone.stop()
camera.release()
cv2.destroyAllWindows()
