<!--
Notes for turning this chapter into a page (for example with Claude Code):
- Match the look and features of door-greeter-build-guide.html: same colors, hero, mission map,
  step cards, badges, copy buttons on code, and checkmarks remembered in the browser.
- Each "## Step N" is one step card. "🎯 Kid challenge", "💡 Parent tip" and "⚠️" lines use the
  existing callout styles. <details> blocks are hidden answers: keep them collapsed.
- Terminal commands are code blocks too, with copy buttons.
- Nice interactive idea for "How the AI sees": a drawing of a hand with its 21 numbered points,
  where clicking a finger folds it and the finger count updates.
- The code also lives in chapter-3-code/ as ready-to-run files.
-->

# 🤖 Chapter 3: Robot Eyes

The MacBook's camera becomes the robot's eyes, and an AI becomes its brain. The robot greets you when it **sees your face**, counts the **fingers** you hold up, and plays **Rock Paper Scissors** against you, keeping score.

This is project #3 in the series. It uses the Chapter 1 wiring and adds no new parts.

## Who it's for

| | |
|---|---|
| **Builders** | Two kids, ages 13 (7th grade) and 10 (5th grade) |
| **Helper** | A parent. Step 1 (setup) is a parent job |
| **Time** | About 2 to 2½ hours. Works well as two Sundays: Steps 1 to 4, then Steps 5 and 6 |
| **Before this** | Chapter 1 finished. Chapter 2 is nice but not needed |
| **Computer** | A Mac with Apple silicon (M1 or newer). Check: Apple menu → **About This Mac** → Chip |

Two jobs this time, swap every step:

- 🧪 **Tester** stands in front of the camera and tries to fool the AI.
- ⌨️ **Coder** types the commands and makes the code changes.

## The big idea: a third input

In Chapter 1 the input was a sensor. In Chapter 2 it was a remote. Now it's an **AI**. The UNO is far too small to run an AI, so the work is split in two:

```
 Camera ──► MacBook (Python + AI) ──── USB cable ────► Arduino ──► screen, buzzer, LED
  eyes            the brain           message: "F"     hands and voice
```

The MacBook watches the camera and decides what it sees. Then it sends the Arduino a **one-letter message** down the same USB cable you use for uploading. The Arduino doesn't know or care that an AI is involved. To it, a message is just another input.

## How the AI sees

An AI **model** is a program that learned from many thousands of example photos. Nobody wrote rules like "a face has two eyes". The model found its own patterns by practicing on examples.

- The **face model** draws a box around each face and says how sure it is, like *93% sure*.
- The **hand model** finds **21 points** on your hand: the wrist, plus 4 points on each finger. It also recognizes a few hand shapes on its own, like ✊ fist, ✋ open hand, and ✌️ peace sign.

Everything runs on the MacBook. No pictures are sent anywhere, and the AI works without internet once it's set up.

💡 **Parent tip:** the most valuable moment in this chapter is when the AI gets something **wrong**. Ask "why do you think it missed that?" That's how kids learn what AI really is: pattern matching that's powerful, but not magic.

## What you need

- The Chapter 1 build, wired as before. Only the **LCD, buzzer and LED** are used. The sensor (and the Chapter 2 IR receiver) can stay plugged in.
- The USB cable, connected to the MacBook the whole time
- The MacBook's built-in camera
- Internet, for Step 1 only

## The 6 steps

| Step | Name | What you do | Time | The win |
|---|---|---|---|---|
| 1 | 🧰 Set up the AI | Terminal commands (parent) | 25 min | The Mac says "All set!" |
| 2 | 👀 Robot eyes | Run a Python program | 15 min | A green box on every face, with how sure the AI is |
| 3 | 🧠 Teach the Arduino to listen | Upload a sketch | 15 min | Type **F** and the robot greets you |
| 4 | 🚪 AI door greeter | Connect eyes and brain | 15 min | Walk into view and the robot says hi |
| 5 | ✋ Finger counter | Hands! | 20 min | Hold up 3 fingers: the screen says 3 and beeps 3 times |
| 6 | ✊✋✌️ Rock Paper Scissors | Play the robot | 30 min | A real game against your own robot |

## Step 1: 🧰 Set up the AI

This is a parent step. You'll type commands into **Terminal** (press ⌘ Space, type *Terminal*, press Return).

First, install **uv**, a tool that installs Python and its add-ons:

```bash
# 1. Install uv, a tool that installs Python and its add-ons
curl -LsSf https://astral.sh/uv/install.sh | sh
```

When it finishes, **close Terminal and open a new window** so the Mac knows where uv is. Then run these, one at a time:

```bash
# 2. Go to this chapter's folder
cd ~/"Claude Projects/Door Greeter Bot/chapter-3-code"

# 3. Make a private Python 3.12 just for this project, and switch it on
uv venv --python 3.12
source .venv/bin/activate

# 4. Install the add-ons: camera tools, the AI, and the USB messenger
uv pip install "mediapipe==1.0.1" opencv-python pyserial

# 5. Download the two AI models (the "trained brains")
curl -L -O https://storage.googleapis.com/mediapipe-models/face_detector/blaze_face_short_range/float16/1/blaze_face_short_range.tflite
curl -L -O https://storage.googleapis.com/mediapipe-models/gesture_recognizer/gesture_recognizer/float16/1/gesture_recognizer.task

# 6. Check that everything is ready
python -c "import cv2, mediapipe, serial; print('All set!')"
```

You should see **All set!** and two new model files in the `chapter-3-code` folder.

⚠️ **Why Python 3.12?** The AI library (MediaPipe) doesn't support newer Python versions yet. uv downloads the right version just for this folder, so it won't touch anything else on the Mac.

### Every time you open a new Terminal window

Run these two lines first, so Terminal uses this project's private Python:

```bash
cd ~/"Claude Projects/Door Greeter Bot/chapter-3-code"
source .venv/bin/activate
```

You'll know it worked when the line in Terminal starts with `(chapter-3-code)`.

## Step 2: 👀 Robot eyes

No Arduino yet. Just the camera and the AI.

```bash
python see_faces.py
```

A window opens with the camera. Every face gets a green box and a score showing how sure the AI is. To stop, click the camera window and press **Q**.

⚠️ **The first time,** the Mac asks whether Terminal may use the camera. Click **Allow**, then run the command again.

```python
# Chapter 3, Step 2: Robot Eyes
# The MacBook camera finds faces and draws a box around each one.
# Click the camera window and press Q to quit.

from pathlib import Path
import time

import cv2
import mediapipe as mp

CAMERA = 0   # if your iPhone's camera opens instead, change this to 1

FACE_MODEL = Path(__file__).parent / "blaze_face_short_range.tflite"
if not FACE_MODEL.exists():
    raise SystemExit("Missing the face model. Do Step 1 (download the AI models) first.")

options = mp.tasks.vision.FaceDetectorOptions(
    base_options=mp.tasks.BaseOptions(model_asset_path=str(FACE_MODEL)),
    running_mode=mp.tasks.vision.RunningMode.VIDEO,
    min_detection_confidence=0.6,      # how sure the AI must be before it says "face"
)
face_finder = mp.tasks.vision.FaceDetector.create_from_options(options)
camera = cv2.VideoCapture(CAMERA)

while True:
    ok, frame = camera.read()
    if not ok:
        print("Can't read the camera. See 'Camera won't open' in Troubleshooting.")
        break

    frame = cv2.flip(frame, 1)                       # mirror it, like a selfie
    rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)     # the AI wants colors in RGB order
    image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb)
    result = face_finder.detect_for_video(image, int(time.monotonic() * 1000))

    for face in result.detections:
        box = face.bounding_box
        sure = face.categories[0].score               # 0.0 to 1.0
        cv2.rectangle(frame, (box.origin_x, box.origin_y),
                      (box.origin_x + box.width, box.origin_y + box.height), (0, 255, 0), 4)
        cv2.putText(frame, f"{sure:.0%} sure", (box.origin_x, box.origin_y - 12),
                    cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)

    cv2.putText(frame, f"Faces: {len(result.detections)}", (30, 70),
                cv2.FONT_HERSHEY_SIMPLEX, 2, (0, 255, 255), 4)
    cv2.imshow("Robot Eyes - press Q to quit", frame)
    if cv2.waitKey(1) & 0xFF == ord("q"):
        break

camera.release()
cv2.destroyAllWindows()
```

🎯 **Kid challenge: fool the AI.** Watch the "% sure" number while you try:

- Sunglasses, a hat, or a hand over half your face
- Turn sideways, then slowly turn back
- Walk far away. How far can you go before it loses you?
- Hold up a photo of a face on a phone, or a drawing of a smiley face
- Show it the dog, or a teddy bear

Which tricks worked? Here's a question to talk about: if it thinks a **photo** is a real face, would this be a safe way to unlock a door?

## Step 3: 🧠 Teach the Arduino to listen

Before connecting the eyes to the robot, test the robot by itself. Testers call this **testing one piece at a time**: if something breaks later, you'll know which half to check.

Upload this sketch. You can also open it from `chapter-3-code/robot_brain/robot_brain.ino`.

```cpp
// Chapter 3: Robot Brain
// The Arduino listens to the MacBook over the USB cable.
// The MacBook does the seeing. The Arduino does the beeping, blinking, and talking.
//
// Messages it understands (one letter each):
//   F = I see a face          N = nobody there
//   0 to 5 = number of fingers
//   r = rock    p = paper    s = scissors
#include <LiquidCrystal.h>

LiquidCrystal lcd(12, 11, 5, 4, 3, 2);   // RS, E, D4, D5, D6, D7

const int BUZZER_PIN = 8;
const int LED_PIN    = 7;

// Change these! Max 16 characters each.
const char* greetings[] = {
  "Hello, human!",
  "Nice face!",
  "Welcome back!",
  "Robot says hi!",
  "Looking sharp!"
};
const int NUM_GREETINGS = sizeof(greetings) / sizeof(greetings[0]);

const char* MOVES[] = {"ROCK", "PAPER", "SCISSORS"};
int yourScore = 0;
int robotScore = 0;

void setup() {
  pinMode(BUZZER_PIN, OUTPUT);
  pinMode(LED_PIN, OUTPUT);
  Serial.begin(9600);
  lcd.begin(16, 2);
  randomSeed(analogRead(A0));
  showIdle();
  Serial.println("Robot brain ready! Type F, N, 0-5, r, p or s.");
}

void loop() {
  if (Serial.available() > 0) {          // did a message arrive?
    char message = Serial.read();

    if (message == 'F') sawFace();
    else if (message == 'N') showIdle();
    else if (message >= '0' && message <= '5') showFingers(message - '0');
    else if (message == 'r') playRound(0);
    else if (message == 'p') playRound(1);
    else if (message == 's') playRound(2);
    // anything else (like the Enter key) is ignored
  }
}

void showIdle() {
  digitalWrite(LED_PIN, LOW);
  lcd.clear();
  lcd.print("Robot eyes: ON");
  lcd.setCursor(0, 1);
  lcd.print("Waiting...");
}

void sawFace() {
  Serial.println("Got F: I see a face!");
  digitalWrite(LED_PIN, HIGH);
  lcd.clear();
  lcd.print("I SEE YOU!");
  lcd.setCursor(0, 1);
  lcd.print(greetings[random(NUM_GREETINGS)]);
  playHello();
}

void showFingers(int count) {
  Serial.print("Got fingers: ");
  Serial.println(count);
  digitalWrite(LED_PIN, HIGH);
  lcd.clear();
  lcd.print("Fingers: ");
  lcd.print(count);
  lcd.setCursor(0, 1);
  for (int i = 0; i < count; i++) {
    lcd.print("| ");                     // one bar per finger
  }
  for (int i = 0; i < count; i++) {      // one beep per finger
    tone(BUZZER_PIN, 880, 80);
    delay(150);
  }
}

// Rock = 0, Paper = 1, Scissors = 2
void playRound(int yourMove) {
  int robotMove = random(3);             // the robot picks at random. Or does it?

  Serial.print("You: ");
  Serial.print(MOVES[yourMove]);
  Serial.print("   Robot: ");
  Serial.println(MOVES[robotMove]);

  // Dramatic countdown
  lcd.clear(); lcd.print("Rock...");     tone(BUZZER_PIN, 523, 150);  delay(350);
  lcd.clear(); lcd.print("Paper...");    tone(BUZZER_PIN, 587, 150);  delay(350);
  lcd.clear(); lcd.print("Scissors...");  tone(BUZZER_PIN, 659, 150);  delay(350);
  lcd.clear(); lcd.print("SHOOT!");      tone(BUZZER_PIN, 1047, 250); delay(500);

  // Show both moves
  lcd.clear();
  lcd.print("You:   ");
  lcd.print(MOVES[yourMove]);
  lcd.setCursor(0, 1);
  lcd.print("Robot: ");
  lcd.print(MOVES[robotMove]);
  delay(1500);

  // Who won?  0 = tie, 1 = you, 2 = robot
  int result = (yourMove - robotMove + 3) % 3;
  lcd.clear();
  if (result == 0) {
    lcd.print("TIE!");
    playTie();
  } else if (result == 1) {
    lcd.print("YOU WIN!");
    yourScore++;
    playWin();
  } else {
    lcd.print("ROBOT WINS!");
    robotScore++;
    playLose();
  }
  lcd.setCursor(0, 1);
  lcd.print("You ");
  lcd.print(yourScore);
  lcd.print(" Robot ");
  lcd.print(robotScore);
}

// ---------- Sounds ----------
void playHello() {
  int notes[] = {523, 659, 784, 1047};     // C, E, G, high C
  for (int i = 0; i < 4; i++) {
    tone(BUZZER_PIN, notes[i], 150);
    delay(180);
  }
}

void playWin() {
  int notes[] = {784, 988, 1175, 1568};    // a happy climb
  for (int i = 0; i < 4; i++) {
    tone(BUZZER_PIN, notes[i], 120);
    delay(140);
  }
}

void playLose() {
  int notes[] = {392, 370, 349, 330};      // sad trombone
  for (int i = 0; i < 4; i++) {
    tone(BUZZER_PIN, notes[i], 250);
    delay(300);
  }
}

void playTie() {
  tone(BUZZER_PIN, 659, 200);
  delay(250);
  tone(BUZZER_PIN, 659, 200);
  delay(250);
}
```

Open the **Serial Monitor** at **9600 baud**. Type one of these letters in the box at the top, press Return, and watch the robot:

| Type | The robot does |
|---|---|
| **F** | "I SEE YOU!", a random greeting, tune, LED on |
| **N** | Back to "Robot eyes: ON / Waiting..." |
| **3** | "Fingers: 3", three bars, three beeps (try 0 to 5) |
| **r**, **p**, **s** | Plays a round of Rock Paper Scissors with your move |

⚠️ **Close the Serial Monitor when you're done.** Only one program at a time can talk to the Arduino over USB. In the next steps, that program is Python.

## Step 4: 🚪 AI door greeter

Now connect the eyes to the robot. Make sure the Serial Monitor is closed, then run:

```bash
python face_greeter.py
```

Step into view and the robot greets you. Leave for 2 seconds and it goes back to waiting. Come back and it greets you again.

```python
# Chapter 3, Step 4: AI Door Greeter
# When the camera sees a face, tell the Arduino "F".
# When the face has been gone for a while, tell it "N".
# Click the camera window and press Q to quit.

from pathlib import Path
import glob
import time

import cv2
import mediapipe as mp
import serial

CAMERA = 0                 # if your iPhone's camera opens instead, change this to 1
STAY_GONE_SECONDS = 2      # how long the face must be gone before the robot resets


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


FACE_MODEL = Path(__file__).parent / "blaze_face_short_range.tflite"
if not FACE_MODEL.exists():
    raise SystemExit("Missing the face model. Do Step 1 (download the AI models) first.")

options = mp.tasks.vision.FaceDetectorOptions(
    base_options=mp.tasks.BaseOptions(model_asset_path=str(FACE_MODEL)),
    running_mode=mp.tasks.vision.RunningMode.VIDEO,
    min_detection_confidence=0.6,
)
face_finder = mp.tasks.vision.FaceDetector.create_from_options(options)
arduino = connect_to_arduino()
camera = cv2.VideoCapture(CAMERA)

greeted = False            # have we already said hi to this face?
last_seen = 0.0            # when did we last see a face?

while True:
    ok, frame = camera.read()
    if not ok:
        print("Can't read the camera. See 'Camera won't open' in Troubleshooting.")
        break

    frame = cv2.flip(frame, 1)
    rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb)
    result = face_finder.detect_for_video(image, int(time.monotonic() * 1000))
    now = time.monotonic()

    if result.detections:                            # a face is here
        last_seen = now
        if not greeted:
            arduino.write(b"F")                      # tell the Arduino: say hi!
            print("Face! Sent F")
            greeted = True
    elif greeted and now - last_seen > STAY_GONE_SECONDS:
        arduino.write(b"N")                          # tell the Arduino: nobody here
        print("Gone. Sent N")
        greeted = False

    for face in result.detections:
        box = face.bounding_box
        cv2.rectangle(frame, (box.origin_x, box.origin_y),
                      (box.origin_x + box.width, box.origin_y + box.height), (0, 255, 0), 4)

    status = "Greeted!" if greeted else "Waiting for a face..."
    cv2.putText(frame, status, (30, 70), cv2.FONT_HERSHEY_SIMPLEX, 2, (0, 255, 255), 4)
    cv2.imshow("AI Door Greeter - press Q to quit", frame)
    if cv2.waitKey(1) & 0xFF == ord("q"):
        break

arduino.write(b"N")        # leave the robot in its waiting screen
arduino.close()
camera.release()
cv2.destroyAllWindows()
```

The Python program only sends a message when something **changes**: a face arrives (**F**) or a face leaves (**N**). It doesn't shout "F F F F" 30 times a second.

🎯 **Kid challenge:** change `STAY_GONE_SECONDS = 2` to `0` and run it again. Look away for a moment. What goes wrong? Now try `10`. Which number feels best?

🎯 **Kid challenge:** write your own greetings in `robot_brain.ino`. To upload, press **Q** to stop Python first, upload, then run Python again.

## Step 5: ✋ Finger counter

```bash
python finger_counter.py
```

Hold your hand up to the camera. The AI draws your hand's skeleton, and the robot shows how many fingers are up and beeps that many times.

```python
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
```

### How it counts

The AI only gives us 21 points. Counting fingers is **our** code, with one simple rule:

> A finger is **up** when its tip is **farther from your wrist** than its middle knuckle.

When you curl a finger, the tip folds back toward your wrist. The thumb gets its own rule, because it bends sideways: it's up when its tip is farther from the pinky's knuckle than its own middle joint is.

🎯 **Kid challenge: why wait?** Change `HOLD_SECONDS = 0.5` to `0`. Open and close your hand slowly. What does the robot do? Now try `2`. The waiting is called **debouncing**. It stops the robot from reacting to every tiny wobble.

🎯 **Kid challenge:** which finger counts are hardest for the AI? Try 3 fingers different ways: thumb, index and middle, versus index, middle and ring.

## Step 6: ✊✋✌️ Rock Paper Scissors vs the robot

```bash
python rps_battle.py
```

How to play:

1. Show your move to the camera and **hold it still** for a moment: ✊ rock, ✋ paper, or ✌️ scissors.
2. Look at the robot's screen: Rock... Paper... Scissors... SHOOT!
3. It shows both moves, who won, and the score.
4. Pull your hand away, then go again.

```python
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
```

The camera window shows what the AI thinks it sees, like `Victory (91%)`. The AI calls the peace sign **Victory**, a fist **Closed_Fist**, and an open hand **Open_Palm**. Our code turns those into game moves.

🎯 **Kid challenge: tournament.** Brother vs robot, best of 5. Then the other brother. Who beat the robot by more? Press the Arduino's reset button to clear the score.

### 🎯 Kid challenge: make the robot cheat

Look at this line in `robot_brain.ino`:

```cpp
  int robotMove = random(3);             // the robot picks at random. Or does it?
```

The robot gets **your** move before it picks its own. Can you change this one line so the robot **always** wins?

Hint: Rock is 0, Paper is 1, Scissors is 2. Which number beats each one?

<details>
<summary>Show the answer</summary>

```cpp
  int robotMove = (yourMove + 1) % 3;   // always picks the move that beats yours
```

Rock (0) loses to Paper (1). Paper (1) loses to Scissors (2). Scissors (2) loses to Rock, and `% 3` wraps 3 back around to 0.

Something to talk about: a game app could do this too, and you'd never see the code. How would you find out if a game was cheating?

</details>

### 🏆 Boss challenge: a secret gesture

The AI already knows more shapes than rock, paper and scissors: 👍 **Thumb_Up**, 👎 **Thumb_Down**, ☝️ **Pointing_Up**, and 🤟 **ILoveYou**. Make the robot play a special song when you show 🤟.

You'll need to change **both** programs: Python has to send a new letter, and the Arduino has to understand it. That's how real engineers add a feature that crosses from one part of a system to another.

<details>
<summary>Show the answer</summary>

**1. In `rps_battle.py`,** replace the two lines near the top with:

```python
GESTURE_TO_MOVE = {"Closed_Fist": "rock", "Open_Palm": "paper", "Victory": "scissors", "ILoveYou": "love"}
MOVE_TO_LETTER = {"rock": b"r", "paper": b"p", "scissors": b"s", "love": b"L"}
```

**2. In `robot_brain.ino`,** add this line in `loop()`, right after the line for `'s'`:

```cpp
    else if (message == 'L') showLove();
```

**3. Still in `robot_brain.ino`,** add this function above the `// ---------- Sounds ----------` line:

```cpp
void showLove() {
  lcd.clear();
  lcd.print("Robot loves you");
  lcd.setCursor(0, 1);
  lcd.print("too! <3");
  playWin();
}
```

Press **Q** to stop Python, upload the sketch, run `python rps_battle.py` again, and show the robot 🤟.

</details>

## Pin map

Nothing new. Chapter 3 uses these from Chapter 1:

| UNO pin | Goes to |
|---|---|
| **8** | Passive buzzer **+** leg |
| **7** | 220 Ω resistor → LED long leg |
| **12, 11, 5, 4, 3, 2** | LCD (same as Chapter 1) |
| **USB** | The MacBook. This is how the messages arrive |

The sensor (pins 9, 10) and the IR receiver (pin 6) can stay plugged in. This chapter just doesn't use them.

## Troubleshooting

**"command not found: uv"**
Close Terminal and open a new window. If it still happens, run `source $HOME/.local/bin/env`.

**"No module named cv2" or "No module named mediapipe"**
You skipped the "every time" lines. Run `source .venv/bin/activate` in the `chapter-3-code` folder.

**Installing mediapipe fails ("no matching distribution")**
MediaPipe needs Python 3.12 or older and a Mac with Apple silicon. Make sure you made the private Python with `uv venv --python 3.12`.

**"Missing the face model" or "Missing the hand model"**
Run the two `curl` lines from Step 1 again, inside the `chapter-3-code` folder.

**Camera won't open ("Can't read the camera")**
The first time, the Mac asks for permission: click Allow and run it again. If you clicked Don't Allow, go to **System Settings → Privacy & Security → Camera**, turn on **Terminal**, then quit and reopen Terminal.

**It opens your iPhone's camera instead**
Change `CAMERA = 0` to `CAMERA = 1` at the top of the program.

**"No Arduino found"**
Check the USB cable. In Terminal, `ls /dev/cu.*` should list something with `usbmodem` or `usbserial` in its name.

**"The Arduino is busy"**
Close the Serial Monitor in the Arduino IDE (or quit the IDE).

**Upload fails because the port is busy**
Python is still using the Arduino. Click the camera window and press **Q**, then upload.

**Pressing Q does nothing**
Click on the camera window first, then press Q. Or click the Terminal window and press **Control + C**.

**The AI keeps missing faces or hands**
Light matters. Face a window or a lamp instead of having one behind you. Stay about half a meter to a meter and a half from the camera, and keep your whole hand in the picture.

**The robot reacts late or plays old moves**
The Arduino is still finishing its last round. Wait for the score to show before the next move. If it gets confused, press the Arduino's reset button.

## What's in this chapter

```
Door Greeter Bot/
├── chapter-3-ai-vision.md          ← you are here
└── chapter-3-code/
    ├── robot_brain/robot_brain.ino ← upload this to the Arduino (Step 3)
    ├── see_faces.py                ← Step 2
    ├── face_greeter.py             ← Step 4
    ├── finger_counter.py           ← Step 5
    ├── rps_battle.py               ← Step 6
    ├── blaze_face_short_range.tflite  (downloaded in Step 1)
    ├── gesture_recognizer.task        (downloaded in Step 1)
    └── .venv/                         (made in Step 1: the private Python)
```

Tested with: Python 3.12, MediaPipe 1.0.1, OpenCV 5.0, pyserial 3.5, LiquidCrystal 1.0.7. The sketch compiles for the UNO, and each Python program was run against a simulated camera and Arduino to check it sends the right messages. The live camera part needs your Mac.

## Where this goes next

- **Wireless:** an ESP32 board has Wi-Fi, so the MacBook could send its messages over the home network and the robot wouldn't need the USB cable.
- **Robot car:** send the moves to the ELEGOO Smart Robot Car instead. Point left and it turns left.
- **Your own gestures:** MediaPipe can learn new hand shapes from your own photos.
