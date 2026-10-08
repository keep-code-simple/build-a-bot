# 📦 Chapter 7: The Robot Box

The robot gets **its own body**. A Raspberry Pi, a camera and a small touchscreen go inside a project box, and the AI from Chapters 3 and 4 runs **without the MacBook**. Carry it to a friend's house, plug it in, play.

The first program is **Rock Paper Scissors**. When the boys get bored of it, they don't put the box away. They **reprogram it into something new**. Same box, new brain.

> **The hardware is fixed. The behavior is software.** Change the code, and the box becomes a different gadget.

| | |
|---|---|
| **Builders** | Two kids, plus a parent |
| **Time** | Path A: one Sunday. Path B: two or three Sundays, then new apps whenever they get bored |
| **Before this** | Chapter 3 (they've seen the AI find faces and hands). Chapter 1's Arduino is reused in Path A |
| **Budget** | Path A roughly $230 to $250. Path B roughly $300 to $350, both with the 8 GB Pi (see [Shopping list](#shopping-list)). Pi prices rose three times in 2026, so check before buying |

---

## Notes for the builder (Claude Code)

This file is the chapter content and the build spec. Please create:

1. **`robot-box/`**, a small app platform plus the first app, as listed in [Code layout](#code-layout).
2. **`chapter-7-robot-box.html`**, the kid guide, matching the other chapter pages: mission map, step cards, badges, copy buttons, saved checkmarks, dark mode. Link it from `index.html`, and add rows to the README chapter table and `roadmap.md`.
3. **A "Make a new app" page section** that walks through copying the template app. This is the part the boys come back to every few weeks.

Ground rules:

- **Two paths, same software.** Path A (start simple, no screen) and Path B (full box) run the same code. Path B just adds the screen, speaker and buttons.
- **Apps are folders.** Dropping a new folder into `apps/` makes it show up in the menu. No other file changes.
- **Runs on the Mac too.** A `--desktop` mode uses the Mac's camera, a normal window, and keyboard keys as buttons. The family develops on the Mac and deploys to the box.
- **Kid-readable code**, like every chapter: short files and plain-English comments.
- **This repo is public on GitHub.** Models, scores, photos and face data are never committed (see [Privacy](#privacy)).
- **Feel as fast and solid as the MacBook.** Follow [Performance and reliability](#performance-and-reliability): the AI Camera does the seeing it can do on its own chip, the Pi only runs the AI the current app needs, and the box watches its own temperature and power.

---

## The big idea: the robot moves out of the laptop

```
 Chapters 3 and 4:   📷 MacBook camera ─► 💻 MacBook (AI) ─USB─► 🤖 Arduino (screen, buzzer)

 Chapter 7, Path A:  📷 Pi camera ─────► 🍓 Raspberry Pi (AI) ─USB─► 🤖 Arduino (screen, buzzer)
 Chapter 7, Path B:  📷 Pi camera ─────► 🍓 Raspberry Pi (AI) ─► 📱 touchscreen + 🔊 speaker + 🔘 buttons
                                         (all inside one box)
```

A **Raspberry Pi** is a whole computer the size of a deck of cards. It runs Linux and Python, has a camera port, a screen port, Wi-Fi and USB. It's slower than the MacBook. The trick to making it *feel* just as fast is the **AI Camera**: it has its own little AI chip, so it can find people and body poses by itself and just hand the Pi the answer.

---

## Shopping list

Prices checked October 2026. Raspberry Pi prices keep changing because of a worldwide memory shortage.

| Part | Path A | Path B | Notes |
|---|---|---|---|
| **Raspberry Pi 5, 8 GB** | ✅ | ✅ | **$130 list price. This is the default for the box**: seeing and speaking at the same time (camera, AI models, voice, screen) needs the headroom. The 4 GB ($85) works for a single light app |
| **Official 27 W USB-C power supply** | ✅ | ✅ | **Required.** Flaky power is the top cause of random Pi crashes and corrupted cards. Don't use a phone charger |
| **Active Cooler** (fan for the Pi 5) | ✅ | ✅ | **Required.** AI keeps the chip busy, and without the fan the Pi quietly slows itself down when hot |
| **microSD card, 32 to 64 GB** | ✅ | ✅ | A **reputable brand, A2-rated**. Cheap cards wear out and corrupt, which is the most common way a Pi "dies" |
| *Later upgrade:* **NVMe SSD + M.2 HAT+** | | optional | The Pi 5 can boot from a fast SSD instead of the SD card. Snappier and more durable. A phase-two upgrade, not day one |
| **Raspberry Pi AI Camera** | ✅ | ✅ | **The default camera** ($70 list, $77 at Adafruit). It works as a normal camera for every app **and** runs person, object and pose AI on its own chip, so the Pi doesn't have to (see [Performance and reliability](#performance-and-reliability)). Camera Module 3 is cheaper but has no on-camera AI, so every model would run on the Pi |
| **Touch Display 2** | | ✅ | **5-inch, $40** (or 7-inch, $60). 720 × 1280, plugs into the Pi's display port, no extra power |
| **Small USB speaker** | | ✅ | The Pi 5 has **no headphone jack**. A USB speaker is the simplest way to get sound |
| **2 arcade buttons** (+ jumper wires) | | ✅ | Big, clicky buttons are half the fun |
| **Project box** | | ✅ | Big enough for the Pi, cooler, screen and speaker, with a window for the screen and holes for the camera and buttons |
| **The Chapter 1 Arduino** (LCD + buzzer) | ✅ | optional | Path A uses it as the screen and voice |

---

## Performance and reliability

The goal: the box should feel as quick and solid as the MacBook did in Chapters 3 and 4. A Pi can't match the Mac's raw speed, but it gets close by **not doing work it doesn't have to**, and it can fully match the Mac on reliability.

### Who does the seeing

The AI Camera's chip can only run certain kinds of models. Its model zoo has object detection (people, pets, everyday things), body pose and image classification. It has **no face or hand models**. So the work is split:

| What the app needs | Who runs it | Model |
|---|---|---|
| **People** (is someone there, where are they) | 🎥 **AI Camera chip** | Object detection (COCO, which includes person, cat, dog) |
| **Pets and everyday objects** | 🎥 **AI Camera chip** | Same object detection |
| **Body pose** (skeleton) | 🎥 **AI Camera chip** | Pose estimation (HigherHRNet, 17 body points) |
| **Hand gestures** (Rock Paper Scissors) | 🍓 **Pi processor** | MediaPipe Gesture Recognizer |
| **Faces** (find, recognize, blink) | 🍓 **Pi processor** | MediaPipe face models / OpenCV YuNet + SFace (Chapter 4) |

The same camera picture feeds both: the AI Camera sends the Pi each frame **plus** its own AI results for that frame.

### Rules that keep it fast

1. **Vision router.** Apps ask for what they need (`needs = {"hands"}`), never for a specific model. `core/vision.py` decides where it runs: on the AI Camera when it can, on the Pi when it must. In `--desktop` mode on the Mac, everything runs on the Mac's processor.
2. **Only run what's needed.** Load an app's models when it opens and release them when it closes. Nothing runs "just in case".
3. **Small pictures for the Pi.** Pi-side models get a shrunken copy of the frame (about 320 to 640 pixels wide), while the screen shows the full-size picture.
4. **Load the camera's AI once.** Switching the AI Camera's on-chip model takes a while (the first load can take minutes). Load person detection at boot and keep it. Only pose apps switch to the pose model, with a friendly "Loading the robot's eyes..." screen.
5. **Speech never blocks the game.** The voice (Piper) runs in its own thread with a queue.
6. **Measure, don't guess.** A debug overlay (toggled with a long press on button B) shows camera FPS, Pi AI FPS, CPU temperature and the warnings below. Fill in the real numbers in the guide after the first build.

### Rules that keep it solid

1. **Cooler and official power supply:** not optional (see the shopping list).
2. **The box watches itself.** `core/health.py` reads the Pi's temperature and its built-in "low power / too hot" warnings (`vcgencmd get_throttled`) every few seconds. If there's a problem, show a small kid-friendly icon (🔥 "I'm too hot!" or 🔌 "I need a better charger!") and log it.
3. **Safe shutdown only:** the Pi 5's power button. Never pull the plug while it's running.
4. **Crashes recover.** An app crash goes back to the menu with a friendly message. A crash of the launcher itself restarts it automatically (the autostart runs it in a restart loop or as a service).
5. **Write less to the card.** Keep logs small and rotated, and save scores only when they change.

### What to expect

The MacBook processed roughly 30 or more camera frames a second in Chapter 3. Pi-side models (hands, faces) will be slower. That's fine for games that read a hand or face **once per round**, like Rock Paper Scissors or a greeter. Smooth, continuous tracking, like the follow-me head, is exactly what the AI Camera's own chip is for. The real numbers come from the debug overlay, not from this page.

---

## Path A: start simple (one Sunday)

The quickest win: the Pi replaces the MacBook, and **Chapter 3's Rock Paper Scissors runs on it almost unchanged**.

### Step A1: 🍓 Set up the Pi (parent, 30 min)

1. On the Mac, use **Raspberry Pi Imager** to write **Raspberry Pi OS (64-bit)** to the microSD card. In the settings, set the hostname to `robotbox`, a username, the home Wi-Fi, and **turn on SSH**.
2. Attach the cooler and the camera ribbon cable (power off!), insert the card, and power on.
3. From the Mac's Terminal: `ssh <username>@robotbox.local`. You're now typing on the box.

### Step A2: 📷 Camera check (10 min)

`rpicam-hello --timeout 5000` shows a 5-second preview, if a monitor is attached. Headless, `rpicam-still -o test.jpg` takes a photo you can copy to the Mac.

For the AI Camera, also run `sudo apt install imx500-all` once, which installs its firmware and the built-in models. The first start can take several minutes while it loads.

### Step A3: 🧠 Move the brain (30 min)

1. Plug the **Chapter 1 Arduino** (with `robot_brain.ino` from Chapter 3) into the Pi's USB port.
2. Clone this repo onto the Pi and run the Path A setup script. It installs MediaPipe and downloads the models, as described in the spec below.
3. Run `python robot-box/box.py --app rps --arduino`. Show your hand to the Pi's camera, and the Arduino's LCD plays the round, exactly like Chapter 3, with no laptop.

### Step A4: 🔌 Make it start on its own (15 min)

Turn on autostart (the script sets it up), unplug the keyboard and SSH, and power-cycle. Within about a minute of plugging in, the box is ready to play. **No computer anywhere.**

🏅 **Badge:** *Brain Transplant*. The AI moved from the laptop into its own little computer.

---

## Path B: the full box (two or three Sundays)

### Step B1: 📱 Screen and sound (30 min)

Connect the Touch Display 2 (ribbon cable to the display port, power from the GPIO pins, as its instructions show) and the USB speaker. The menu now appears on the touchscreen.

### Step B2: 🔘 Arcade buttons (20 min)

Wire two arcade buttons. Each one goes between a GPIO pin and GND (the software turns on the internal pull-ups):

| Button | GPIO | Job |
|---|---|---|
| **A** (green) | GPIO 17 | Select / play |
| **B** (red) | GPIO 27 | Back / menu |

The Pi 5's own **power button** does a safe shutdown. Make it reachable from outside the box. Pulling the plug while it's writing to the SD card can corrupt the card.

### Step B3: 📦 Build the box (60 to 90 min)

Mount the Pi with standoffs, the screen in a window, the camera at the top facing out (at kid face height when the box sits on a table), the speaker behind a few drilled holes, the buttons on the front, and the power cable out the back. Leave **air holes near the fan**.

Kid jobs: design the face of the box (stickers, a name, a paint job). It's theirs.

### Step B4: ✊✋✌️ Play (forever)

The box boots straight into the **app menu**. Pick Rock Paper Scissors and play. 🏅 **Badge:** *It's Alive*.

---

## App 1: Rock Paper Scissors

### How it plays

1. **Attract screen:** "Show me your hand to play!", with the live camera in a corner and the robot's face idling (blinking eyes).
2. **Pick a player:** big touch buttons **Kid 1 / Kid 2 / Guest**, or button A to cycle through them. The display names are set in `config.json`; the public repo uses placeholders.
3. **The robot commits first.** At the start of each round, the robot secretly picks its move and shows a **sealed envelope** 🔒 on screen, *before* seeing yours. It can't cheat. (This is the fair-play fix for Chapter 3's "make the robot cheat" lesson.)
4. **Countdown:** big "ROCK... PAPER... SCISSORS... SHOOT!" with beeps and the robot's voice.
5. **Reading your move:** during the half-second after "SHOOT!", the box collects the gesture from every frame and takes the **majority vote** (Closed_Fist = rock, Open_Palm = paper, Victory = scissors). If it's unclear: "I couldn't see that, again!"
6. **Reveal:** the envelope opens. Both moves are drawn big, then who won, with a win, lose or tie sound and a voice line.
7. **Match:** first to 3 wins. The score shows at the top.
8. **Leaderboard:** best win streak per player, saved locally.

### Build requirements

- Gestures come from the **MediaPipe Gesture Recognizer** (same model as Chapter 3), in `VIDEO` mode with 1 hand.
- Camera frames are scaled down (for example 640 × 480) before the AI sees them, to keep the Pi fast.
- The UI is **pygame**, full screen at the display's resolution, with big fonts and big touch targets.
- Hidden **cheat switch** (`config.json` → `"robot_cheats": false`) for the Chapter 3 lesson. When it's `true`, the envelope shows "?" instead of 🔒, so the cheat is visible.

### Acceptance

- In normal room light, it reads a held gesture correctly in at least 9 of 10 rounds.
- A full round (countdown to result) runs smoothly on the Pi 5 with no visible freezing.
- The robot's move is fixed before the countdown and is recorded in the log line *before* the player's move is read (there's a unit test for the commit-before-read order).

---

## Make a new app (the part they come back to)

When they're bored of Rock Paper Scissors:

1. Copy `robot-box/apps/_template/` to `robot-box/apps/my_app/`.
2. Edit `app.py`: give it a name, pick which AI it needs, and fill in `update()` and `draw()`.
3. Restart the box. The new app is in the menu.

Starting ideas are in **`robot-box-ideas.md`**: a reaction-time tester (no AI, great first app), a staring-contest judge, a pet detector, and more.

### The app shape (what the template contains)

```python
class App:
    name = "My App"
    color = (255, 170, 0)        # menu tile color
    needs = {"hands"}            # any of: "hands", "faces", "pose", "objects" (or empty)

    def start(self, box): ...                       # app opens
    def update(self, box, frame, vision, dt): ...   # every frame: read the AI results, change the game state
    def draw(self, screen): ...                     # every frame: draw the game
    def on_button(self, box, name): ...             # "A", "B", or ("touch", x, y)
    def stop(self, box): ...                        # app closes
```

`box` gives every app the same helpers:

- `box.say(text)` (robot voice)
- `box.beep(hz, ms)` and `box.tune(name)`
- `box.scores` (save and load high scores)
- `box.arduino` (send Chapter 3 protocol letters, when one is plugged in)
- `box.config`

---

## Code layout

```
robot-box/
├── box.py                 launcher: menu, app switching, main loop (--desktop, --app NAME, --arduino)
├── core/
│   ├── camera.py          Picamera2 on the Pi; OpenCV VideoCapture with --desktop
│   ├── vision.py          vision router: routes each app's needs to the AI Camera or the Pi; loads only what's needed
│   ├── ai_camera.py       AI Camera (IMX500): on-chip person/object detection and pose results
│   ├── health.py          temperature and "low power / too hot" warnings, FPS for the debug overlay
│   ├── sound.py           beeps and tunes (pygame mixer), speech (Piper TTS, falls back to espeak-ng)
│   ├── buttons.py         gpiozero arcade buttons; keyboard keys with --desktop
│   ├── scores.py          high scores in a local JSON file
│   └── arduino.py         optional USB serial link (Chapter 3 protocol)
├── apps/
│   ├── _template/app.py   copy this to make a new app
│   ├── rps/app.py         App 1: Rock Paper Scissors
│   └── reaction/app.py    App 2: reaction-time tester (no AI): a small, complete example
├── setup/
│   ├── install.sh         apt and pip packages, venv, model downloads, autostart
│   └── download_models.py
├── config.example.json    committed (placeholder names)
├── tests/                 pytest: game logic, majority vote, scores, app loading
└── README.md              how to run, deploy and add an app
```

### Technical constraints (checked October 2026)

- **OS:** Raspberry Pi OS 64-bit (Debian 13 "Trixie"), with the system **Python 3.13**.
- **Camera library:**
  - Picamera2 comes from apt (`python3-picamera2`) and can't simply be pip-installed.
  - So the venv is created **from the system Python with system packages visible**: `uv venv --python /usr/bin/python3 --system-site-packages` (or `python3 -m venv --system-site-packages .venv`).
  - Install the rest with pip inside it.
- **Pip packages:**
  - `mediapipe` 1.1.0, which now ships Linux ARM64 wheels and supports Python 3.9 to 3.14.
  - `opencv-python`, `pygame` (2.6.x has ARM64 wheels for Python 3.13, or use apt `python3-pygame`), `pyserial` and `numpy`.
  - `piper-tts` 1.8.0 (ARM64 wheels; neural, offline voice).
- **AI models** are downloaded by the setup script into `robot-box/models/` (gitignored): the MediaPipe gesture recognizer (same URL as Chapter 3), plus face, pose and object models only when an app needs them.
- **Voice:**
  - Piper speaks with a downloaded voice model.
  - Speech runs in a background thread with a queue, so the game never freezes while the robot talks.
  - If Piper or its voice is missing, it falls back to `espeak-ng` (robotic but instant).
- **Performance:** follow [Performance and reliability](#performance-and-reliability): vision router, AI Camera first, models loaded per app, small frames for Pi-side models, and a debug overlay with FPS, temperature and warnings.
- **Autostart:** the box boots to the desktop with autologin, and the launcher starts full screen through the desktop's autostart (Raspberry Pi OS uses the labwc compositor). `install.sh` sets this up, and there's an `--uninstall-autostart` option to undo it.
- **Deploy:** develop on the Mac in `--desktop` mode and push to GitHub. On the box, `git pull` (or a "Check for updates" item in the menu's settings) brings the new apps in.
- **Never crash to a black screen.** If an app throws an error, the launcher shows "Oops! This app crashed" with a kid-readable message, logs the details, and returns to the menu.

## Testing

**Desktop (pytest, no Pi needed):**

- RPS winner rules for all 9 combinations.
- Majority vote: a clear gesture, a mixed or unclear one ("couldn't see"), and no hand.
- The robot commits before the player's move is read. Cheat mode, when on, is visible on screen.
- Scores save and reload, and a missing or corrupt scores file doesn't crash.
- **App loading:** every folder in `apps/` (except `_template`) loads and has the required parts. A broken app is skipped, with a message.
- Launcher smoke test: open the menu, enter RPS, return to the menu, with a fake camera and fake vision.
- **Vision router:** `people`, `objects` and `pose` go to the AI Camera when it's present. `hands` and `faces` always go to the Pi. With `--desktop`, everything goes to the Mac's processor.
- **Health:** parse sample `vcgencmd get_throttled` values (normal, under-voltage, throttled from heat) into the right icon and message.

**On the Mac:** `python box.py --desktop` runs the whole box in a window with the Mac camera.

**On the Pi (the family's checklist on the page):**

- Boots into the menu by itself.
- Debug overlay: no 🔥 or 🔌 warning after 20 minutes of play.
- RPS gets 9 of 10 gestures right.
- Buttons work, and voice and sound play.
- The power button shuts down cleanly.
- `git pull` brings in a new app.

## Privacy

- **Gitignored:** `robot-box/config.json`, `robot-box/models/`, `robot-box/data/` (scores and any future face data), and any `*.task` / `*.onnx` / `*.tflite` files.
- **No photos are saved** by RPS or the template. Apps that save pictures or recognize faces (see the ideas list) must say so on screen and be opt-in.
- Display names in committed files are always "Kid 1" and "Kid 2".

---

## Grown-up corner

| In this chapter | At work |
|---|---|
| Apps as folders with the same small interface | A plugin architecture |
| `box` helpers shared by every app | A platform layer / SDK |
| Develop on the Mac, `git pull` on the box | A deployment pipeline (very small) |
| Crashed app goes back to the menu | Fault isolation |
| Same software for Path A and Path B | Hardware abstraction |
| The robot commits its move before reading yours | Commit-reveal: fairness you can check |

---

## Facts checked (October 2026)

| Fact | Source |
|---|---|
| Pi 5 list prices: 8 GB $130 (the box's default), 4 GB $85 (after the October 2026 rise) | [Tom's Hardware, Oct 2 2026](https://www.tomshardware.com/raspberry-pi/component-shortages-drive-raspberry-pi-prices-up-by-up-to-23-percent-escalating-lpddr4-lpddr5-costs-trigger-the-third-price-hike-of-the-year) |
| AI Camera: Sony IMX500 with on-sensor AI; works with Pi 5 and Pi 4 (and Zero 2 W / 3B+ with tweaks); `imx500-all` package; MobileNet SSD and PoseNet built in; custom models need Sony's conversion tools | [Raspberry Pi AI Camera docs](https://www.raspberrypi.com/documentation/accessories/ai-camera.html) |
| AI Camera: $70 list, $77 at Adafruit; 12 MP; ~78° view; 30 fps at 2028 × 1520 | [Raspberry Pi news](https://www.raspberrypi.com/news/raspberry-pi-ai-camera-on-sale-now/), [Adafruit](https://www.adafruit.com/product/6009) |
| AI Camera model zoo: object detection (YOLO11n, YOLOv8n, EfficientDet Lite-0, SSD MobileNetV2 and others, COCO 80 classes), pose (HigherHRNet), segmentation, classification. No face or hand models | [raspberrypi/imx500-models](https://github.com/raspberrypi/imx500-models) |
| Touch Display 2: 5-inch $40, 7-inch $60, 720 × 1280, DSI ribbon + GPIO power, works with Pi 5 and Pi 4 | [Raspberry Pi Touch Display 2](https://www.raspberrypi.com/products/touch-display-2/) |
| MediaPipe 1.1.0: ARM64 Linux wheels, Python 3.9 to 3.14; same Tasks API (tested on Python 3.13) | [PyPI](https://pypi.org/project/mediapipe/), tested |
| Picamera2 in a venv: install with apt, then create the venv with system site-packages | [Using picamera2 with uv on Raspberry Pi](https://pydevtools.com/handbook/how-to/how-to-use-picamera2-and-gpio-with-uv-on-raspberry-pi/) |
| Piper TTS 1.8.0: offline neural voice, ARM64 wheels, GPL-3.0 | [piper1-gpl](https://github.com/OHF-Voice/piper1-gpl), PyPI |
| Raspberry Pi OS current release is Trixie | [Raspberry Pi news: Trixie](https://www.raspberrypi.com/news/trixie-the-new-version-of-raspberry-pi-os/) |

**Not verified:** how fast MediaPipe runs on a Pi 5 with this camera (the FPS counter will show it), and exact prices for the small parts.
