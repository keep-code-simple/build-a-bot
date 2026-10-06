# 🗣️ Chapter 4: The Talking Robot

The robot learns to **talk**, to **take messages from a phone anywhere in the world**, to **text you back**, to **make announcements on a schedule**, and finally to **recognize each brother and greet him by name** with his own catchphrase and theme tune.

This chapter connects the real world (atoms) to the internet (bits) and back again: a full round trip.

| | |
|---|---|
| **Builders** | Two kids, ages 13 (7th grade) and 10 (5th grade), plus a parent |
| **Time** | About 3 hours. Best as two Sundays: Steps 1 to 3, then Steps 4 and 5. Step 6 is a bonus that needs a small purchase |
| **Before this** | Chapter 1 built. Chapter 3, Step 1 (Python and uv set up on the Mac) done |
| **Computer** | A Mac with Apple silicon. The Mac's built-in `say` command is the robot's voice |
| **Phone** | An iPhone or iPad (for Siri Shortcuts) or any phone with the free **ntfy** app |

---

## Notes for the builder (Claude Code)

This file is both the **chapter content** and the **build spec**. Please create:

1. **`chapter-4-code/`**, with everything listed in [Code layout](#code-layout).
2. **`chapter-4-talking-robot.html`**, the kid-facing guide, matching `door-greeter-build-guide.html` and `chapter-2-secret-code-bot.html`: same look, mission map, step cards, badges, copy buttons, saved checkmarks and dark mode. Link it from `index.html` and add a row to the README's chapter table.
3. **`.gitignore` additions** for every private file in [Privacy and secrets](#privacy-and-secrets). This repo is on GitHub. Nothing private may ever be committed.

Ground rules:

- **Each step ends with a win** that works on its own, like the earlier chapters.
- **Kid-readable code.** Short files, plain-English comments, friendly log lines (`📱 Phone said: ...`, `🤖 Robot: visitor #3`). The kids will open these files.
- **Never use real names or faces** in committed files or on the HTML page. Use "Kid 1" and "Kid 2" in examples.
- **Wiring:** Chapter 4 starts from the **Chapter 1 wiring** (sensor on 9 and 10, LED on 7, buzzer on 8, LCD on 12, 11, 5, 4, 3, 2). Chapter 2 (Secret Code Bot) removes the sensor, so the guide must say: "Put the ultrasonic sensor back as in Chapter 1."
- **Test everything that can run without hardware** (see [Testing](#testing)) and say clearly in the guide what was and wasn't tested on real hardware.

---

## The big idea: the full loop

```
 📱 Phone / Siri ──► ☁️ ntfy topic "to robot" ──► 💻 Mac bridge ──USB──► 🤖 Arduino ──► screen, buzzer, voice
                                                       ▲    │
 🔔 Phone notification ◄── ☁️ ntfy "from robot" ◄──────┘    │◄──USB── "EVENT VISITOR 23"
                                                            │
                                   📷 camera (faces) ───────┤
                                   ⏰ clock (schedule) ─────┘
```

- The **Mac bridge** is one Python program. It's the only program allowed to use the USB port, because only one program at a time can talk to the Arduino.
- The bridge **never opens a door into the house**. It reaches **out** to the ntfy server and asks "any messages for me?" No router settings, no open ports.
- **Reflex vs thinking.** The Arduino reacts instantly by itself (a chirp and the LED when someone walks up). The Mac does the slow, smart part (speech, names, internet). Brains work the same way: you pull your hand off a hot stove before your brain finishes thinking "hot!".

Kids' version: *"The robot has a little brain (the Arduino) for quick reflexes, and a big brain (the Mac) for talking, recognizing faces and using the internet. They pass notes to each other down the USB cable."*

---

## The 6 steps

| Step | Name | Time | The win |
|---|---|---|---|
| 1 | 🗣️ The robot speaks | 20 min | Type a sentence: the screen shows it **and** the robot says it out loud |
| 2 | 📱 Text the robot | 30 min | Say "Hey Siri, tell the robot..." from anywhere, and the robot speaks it |
| 3 | 🔔 The robot texts back | 20 min | Walk up to the robot and your phone buzzes: "Visitor #23" |
| 4 | ⏰ Robot alarm clock | 15 min | The robot announces "Snack time!" at 3:30 on school days |
| 5 | 🧑 It knows my name | 45 min | It recognizes each brother and plays his own entrance |
| 6 | 🔊 Talk without the Mac (bonus) | 45 min | Unplugged on a battery, it still talks |

---

## The message protocol (how the two brains pass notes)

All messages are short lines of plain text ending with a newline, at **9600 baud**. Kids can type them in the Serial Monitor to test the Arduino by itself, just like Chapter 3.

### Mac → Arduino (commands)

| Command | What the Arduino does | Reply |
|---|---|---|
| `PING` | Nothing, just answers | `PONG` |
| `SHOW <line 1>\|<line 2>` | Shows text on the LCD. Each line is cut to 16 characters | `OK SHOW` |
| `BEEP <hz> <ms>` | One beep. hz 100 to 5000, ms 10 to 2000 | `OK BEEP` |
| `TUNE <HELLO\|WIN\|SAD\|SIREN>` | Plays a built-in tune | `OK TUNE` |
| `NOTES <hz> <hz> ...` | Plays up to 8 notes (a kid's theme tune) | `OK NOTES` |
| `LED <ON\|OFF\|BLINK>` | LED on pin 7 | `OK LED` |
| `PLAY <n>` | Plays voice file n from the SD card (Step 6 only) | `OK PLAY`, or `ERR NO_PLAYER` |
| `IDLE` | Back to the waiting screen | `OK IDLE` |

Anything else gets `ERR UNKNOWN`. Bad numbers get `ERR RANGE`. Lines longer than 64 characters get `ERR TOO_LONG`.

### Arduino → Mac (events)

| Line | When |
|---|---|
| `READY` | Just started (every restart, including when the Mac connects) |
| `EVENT VISITOR <count>` | Someone came closer than 60 cm (same logic as Chapter 1) |
| `EVENT LEFT` | They walked away |
| `OK <verb>` / `ERR <reason>` | The answer to each command |

**Reflex rule:** on `EVENT VISITOR`, the Arduino chirps and lights the LED **by itself**. It does not wait for the Mac. Speech and words come from the Mac.

---

## Step 1: 🗣️ The robot speaks

### Kids see

1. **Instant magic, no code:** in Terminal, type `say "Hello, I am a robot"`. The Mac talks.
2. Try other voices: `say -v '?'` lists them. Try `say -r 300 "I am a very fast robot"` (words per minute).
3. Upload `robot_bridge.ino`. In the Serial Monitor, type `SHOW Hello|I am a robot`, then `TUNE HELLO`, then `PING`.
4. **Close the Serial Monitor**, then run `python say_it.py "Hello, I am a robot"`. The screen shows it **and** the robot says it, at the same time.
5. Run `python say_it.py` with nothing after it for chat mode: it keeps asking "What should I say?".

### Build requirements

- `say_it.py` sends `SHOW` with the text wrapped by words into two 16-character lines, then speaks it.
- Speech uses `subprocess.run(["say", "-v", voice, text])` with a **list of arguments, never `shell=True`**. Grown-up note: this stops text like `"; rm -rf ~"` from ever being run as a command. It just gets spoken.
- Clean the text first: printable ASCII only on the LCD (emoji become `?`), and at most 100 characters spoken.
- Speech is slow and blocking, so it runs through a **speech queue** with one worker thread. Messages never talk over each other.

### Kid challenges

- Find the funniest voice. Make the robot say a tongue twister at speed 350.
- Add a pause: `say "Wait for it [[slnc 1000]] robot!"`.

### Acceptance

- The LCD shows the text within half a second of the voice starting.
- Long sentences wrap on word boundaries, and emoji don't break the LCD.
- The text `"; echo HACKED"` is spoken out loud and never runs as a command (there's a unit test for this).

---

## Step 2: 📱 Text the robot

### Kids see

1. A parent runs `python setup_cloud.py` once. It creates the private `config.json` with two **secret topic names** (random, like passwords) and prints how to set up the phone.
2. On the iPhone or iPad, build a Shortcut called **"Tell the robot"**:
   - **Ask for Input** (Text): "What should the robot say?"
   - **Get Contents of URL**: `https://ntfy.sh/` (the root address, not the topic address), Method **POST**, Request Body **JSON**, with fields `topic` = *the secret "to robot" topic* and `message` = *Provided Input*.
3. Start the bridge: `caffeinate -i python robot_bridge.py`. (`caffeinate` keeps the Mac awake while the bridge runs.)
4. Say **"Hey Siri, tell the robot"**, speak a sentence, and the robot shows it and says it. It even works from the car or from Grandma's house.

### Build requirements

- `setup_cloud.py` generates topics with `secrets.token_urlsafe` (at least 16 random characters each, prefixed `bab-`) and writes `config.json` from `config.example.json`. It never overwrites an existing config without asking. It prints the exact Shortcut fields to type.
- The bridge subscribes with a streaming GET to `https://ntfy.sh/<to_robot>/json` and handles one JSON object per line. Act only on `"event": "message"`; ignore `open` and `keepalive`.
- **Reconnect forever** with backoff (1, 2, 4, up to 30 seconds) when the network drops. Skip duplicate message `id`s.
- **Phone commands:** plain text gets shown and spoken. `!beep`, `!tune win`, `!led on`, `!led off` and `!status` (replies with uptime and visitor count) are special commands.
- **House rules:**
  - Max 100 characters.
  - At most 1 message every 3 seconds, with a queue of 5. Extras are dropped, with a log line saying so.
  - **Quiet hours** (default 21:00 to 07:00, set in config): phone messages show on the LCD but are **not spoken**.
- If the USB cable is pulled out, the bridge keeps running, says so in the log, and reconnects when it's plugged back in.

### Grown-up corner

The ntfy topic plays the role of an SNS topic or SQS queue. The bridge is a consumer that **polls outward**, the same reason SQS consumers poll: no inbound ports, so nothing in the house is exposed. Topic names are the only lock, so treat them like passwords. ntfy topics are open to anyone who knows the name.

### Acceptance

- A phone message is spoken within about 3 seconds.
- Turn Wi-Fi off and back on: the bridge reconnects by itself within 30 seconds.
- Ten messages in a row: no crash, at most 5 queued, and the rest logged as dropped.
- During quiet hours, the message shows on the screen but isn't spoken.

---

## Step 3: 🔔 The robot texts back

### Kids see

1. On the phone, open the **ntfy** app (or `ntfy.sh/app` in Safari) and subscribe to the secret **"from robot"** topic.
2. Walk up to the robot: the phone buzzes with **"🤖 Door Greeter: visitor #24 at the door"**.
3. Text the robot `!status`, and it texts back how long it's been awake and how many visitors it's had.
4. That's the **full round trip**: phone → cloud → Mac → Arduino → Mac → cloud → phone.

### Build requirements

- On `EVENT VISITOR`, publish to `https://ntfy.sh/<from_robot>` with a title header and a short message.
- **Cooldown:** at most one visitor notification per 60 seconds (set in config). Nobody wants 40 buzzes while the kids test it.
- **No names** go to the internet by default (see Step 5).
- If publishing fails, retry 3 times with a short wait, then log it and move on. Never crash.

### Kid challenge: measure the latency

Use a stopwatch: how long from pressing send to hearing the robot? From walking up to the phone buzzing? This delay is called **latency**, and engineers fight for every millisecond of it.

### Acceptance

- The notification arrives within about 5 seconds.
- Walking past 5 times in one minute sends 1 notification, not 5.
- With the internet off, visits still chirp locally and the bridge logs "couldn't send".

---

## Step 4: ⏰ Robot alarm clock

### Kids see

Edit the `schedule` list in `config.json`, for example:

```json
"schedule": [
  { "time": "15:30", "days": ["mon", "tue", "wed", "thu", "fri"], "say": "Snack time!", "tune": "WIN" },
  { "time": "19:45", "days": ["sun", "mon", "tue", "wed", "thu"], "say": "Twenty minutes to bedtime", "tune": "HELLO" }
]
```

The robot announces each one on the screen, with the tune and the voice.

### Build requirements

- A scheduler thread checks every 20 seconds and fires each item **once** within its minute, on the listed days only.
- Times use the Mac's local time zone.
- Scheduled announcements are **not** blocked by quiet hours (the family chose those times on purpose). Phone messages are.

### Grown-up corner

This is EventBridge Scheduler or cron: time is just another event source that wakes the system.

### Acceptance

- Fires within 30 seconds of the set time, exactly once, and only on the listed days. Unit-tested with a fake clock.

---

## Step 5: 🧑 It knows my name (the finale)

### Kids see

1. **Ask first.** Each brother says yes before being added. The robot only learns faces of people who agree.
2. `python enroll_face.py`. It asks:
   - the name to show (for example, Kid 1),
   - **how to say it** (spelled the way it sounds, so the Mac pronounces it right),
   - a **catchphrase** ("The legend has arrived!"),
   - a **theme tune** (up to 8 notes from the Chapter 1 note chart).

   Then the camera opens and guides them: "look straight... turn a little left... a little right... smile!", taking 20 good samples in about 15 seconds.
3. `python calibrate_faces.py`. The camera shows **live scores for each brother**: how sure the AI is that this face is Kid 1, and how sure it is that it's Kid 2. Seeing those numbers is the real lesson.
4. `caffeinate -i python robot_bridge.py --faces`. Walk in: **"Hi Kid 1! The legend has arrived!"**, with the screen, the theme tune, and the voice.
5. A stranger, or anyone it isn't sure about, gets "Hello, friend!".
6. `python forget_face.py "Kid 1"` deletes a person completely.

### Build requirements

- **Models** (OpenCV only, no MediaPipe, no cloud). Download into `chapter-4-code/models/` (these exact URLs were tested):
  - Face finder (YuNet): `https://media.githubusercontent.com/media/opencv/opencv_zoo/main/models/face_detection_yunet/face_detection_yunet_2023mar.onnx`
  - Face "fingerprint" maker (SFace): `https://media.githubusercontent.com/media/opencv/opencv_zoo/main/models/face_recognition_sface/face_recognition_sface_2021dec.onnx`
- **Pipeline:** `cv2.FaceDetectorYN` finds faces, `cv2.FaceRecognizerSF.alignCrop` and `.feature` turn each face into **128 numbers** (an embedding), and `.match(..., cv2.FaceRecognizerSF_FR_COSINE)` compares them.
- **What's stored:** only the embeddings, in `faces/<id>.npy`, plus `people.json` (display name, how to say it, catchphrase, tune). **No photos are ever saved.**
- **Decision rule** (a pure function, unit-tested with synthetic vectors):
  - Each person's score is the average of their top 3 cosine similarities.
  - Say the name only if the best score is **≥ 0.45** **and** beats the second-best person by **≥ 0.06**. Otherwise the answer is "friend".
  - The same answer must appear in **3 of the last 5 frames** before greeting.
  - Why stricter than OpenCV's suggested 0.363: brothers look alike, and **saying "friend" is better than saying the wrong brother's name**. Put both numbers in the config so the 13-year-old can experiment.
- **Cooldowns:** 2 minutes per person, 1 minute for "friend".
- **Greeting:** `SHOW Hi <name>!|<catchphrase>`, then `NOTES <tune>`, then say "<how to say it>. <catchphrase>".
- **Privacy defaults:**
  - Phone notifications say "someone is home", not the name, unless `notify_names` is set to `true` in config (default `false`).
  - Recognition runs only on the Mac, offline.

### Kids' lesson (for the HTML page)

- A **face embedding** is 128 numbers that describe your face, like a fingerprint made of numbers. The robot compares numbers, not pictures.
- The AI is never 100% sure. It gives scores, and **we** choose the rule for when it's sure enough.
- It can be fooled. A photo of a face on a phone might work, because this robot can't tell a real face from a picture. That's why real face unlock uses special 3D cameras.
- **Your face is yours.** It stays on this Mac, it's never uploaded, and you can delete it any time.

### Kid challenge: the brother test

Swap hats, borrow glasses, make weird faces, walk in together. Can it still tell you apart? When does it give up and say "friend"? Change the 0.45 and see what happens.

### Acceptance

- Each enrolled brother is greeted by name in at least **8 of 10** normal walk-ups.
- **Never the wrong name** in 20 "brother swap" tries. If it's unsure, it says "friend".
- `forget_face.py` removes every trace of that person: the embedding file and their entry in `people.json`.
- Nothing in `faces/`, `people.json` or `config.json` shows up in `git status`.

---

## Step 6: 🔊 Talk without the Mac (bonus, needs parts)

### Shopping list

| Part | Notes |
|---|---|
| **DFPlayer Mini** MP3 module | A tiny board with a micro-SD slot and a built-in amplifier. Clones exist and some behave a little differently |
| **Micro-SD card**, 32 GB or smaller | Formatted **FAT32** |
| **Small speaker, 4 to 8 Ω**, under 3 W | The speaker currently holding up the sensor might work. Check its label |
| **1 kΩ resistor** | In the kit |

### Wiring (Chapter 1 wiring stays)

| DFPlayer pin | Goes to |
|---|---|
| **VCC** | **+** rail (5 V) |
| **GND** | **−** rail |
| **RX** | **1 kΩ resistor** → UNO **A2** |
| **TX** | UNO **A1** |
| **SPK_1** and **SPK_2** | The two speaker wires (never to GND) |

Pins 0 and 1 stay free, because the USB cable uses them to talk to the Mac.

### Kids see

1. Write the robot's phrases in `phrases.json` (greetings, jokes, "Hi Kid 1!").
2. `python make_voice_files.py` turns every phrase into a sound file, using the Mac's own voice, in `sd_card/MP3/`.
3. Copy the `MP3` folder onto the SD card and put the card in the DFPlayer.
4. Unplug the robot from the Mac and power it from a power bank. Walk up: **it talks**, with no computer at all.

### Build requirements

- **`make_voice_files.py`:**
  - `say -v <voice> -o tmp.aiff "<text>"`
  - then `afconvert -f WAVE -d LEI16@22050 tmp.aiff tmp.wav`
  - then encode to MP3 with the **`lameenc`** Python package
  - named `sd_card/MP3/0001.mp3`, `0002.mp3` and so on.
  - It also writes `chapter-4-code/robot_bridge/phrases.h` with **numbers only** (`#define PHRASE_GREETING_FIRST 1` and so on). No names go in the sketch.
- **Arduino side:**
  - Use the **DFRobotDFPlayerMini** library (Library Manager, v1.0.6 tested) with `SoftwareSerial` on A1 (RX) and A2 (TX).
  - Call `begin(serial, true, true)`. If that fails, retry `begin(serial, false, true)`, because some clone chips don't answer acknowledgements.
  - `playMp3Folder(n)` plays `/MP3/000n.mp3`.
  - If no player is found, everything else still works and `PLAY` answers `ERR NO_PLAYER`.
- **Graceful fallback:**
  - If the Mac bridge sent any command in the last 60 seconds, the Arduino lets the Mac do the talking.
  - Otherwise, on `EVENT VISITOR` it plays a random greeting from the SD card by itself.
  - So: plugged into the bridge, no double greetings. Unplugged, it still talks.

### Grown-up corner

This is graceful degradation. When the cloud or the big brain is gone, the device keeps doing its core job locally.

### Acceptance

- On a power bank with no Mac, walking up plays a greeting within 1 second.
- Connected to the bridge, there's never a double greeting.
- With no DFPlayer attached, the sketch still works.

---

## Pin map

| UNO pin | Goes to |
|---|---|
| **9** / **10** | Sensor Trig / Echo (put it back if Chapter 2 removed it) |
| **8** | Passive buzzer |
| **7** | 220 Ω → LED |
| **12, 11, 5, 4, 3, 2** | LCD (same as Chapter 1) |
| **A1** | DFPlayer TX (Step 6 only) |
| **A2** | 1 kΩ → DFPlayer RX (Step 6 only) |
| **0, 1** | Leave empty: the USB link to the Mac |

---

## Code layout

```
chapter-4-code/
├── robot_bridge/
│   ├── robot_bridge.ino        Arduino: protocol, reflexes, LCD, buzzer, optional DFPlayer
│   └── phrases.h               generated by make_voice_files.py (numbers only)
├── say_it.py                   Step 1
├── robot_bridge.py             Steps 2 to 5 (--faces turns on the camera)
├── setup_cloud.py              Step 2, run once
├── enroll_face.py              Step 5
├── calibrate_faces.py          Step 5
├── forget_face.py              Step 5
├── make_voice_files.py         Step 6
├── bridge/                     small helper modules the scripts share
│   ├── protocol.py             build and parse protocol lines, LCD word-wrap, text cleaning
│   ├── arduino_link.py         find the port, connect, auto-reconnect, reader thread
│   ├── speech.py               speech queue around `say`
│   ├── cloud.py                ntfy subscribe and publish, retries, dedupe
│   ├── scheduler.py            schedule firing (clock passed in, so it's testable)
│   ├── faces.py                detector, embeddings, decision rule
│   └── rules.py                cooldowns, quiet hours, rate limit
├── config.example.json         committed: settings with no secrets
├── phrases.example.json        committed: phrases with "Kid 1" / "Kid 2" placeholders
├── requirements.txt            pinned versions
├── tests/                      pytest
│
├── config.json                 PRIVATE (gitignored)
├── people.json                 PRIVATE (gitignored)
├── phrases.json                PRIVATE (gitignored)
├── faces/                      PRIVATE (gitignored)
├── models/                     downloaded (gitignored)
├── sd_card/                    generated (gitignored)
└── .venv/                      (gitignored)
```

### Technical constraints

- **Python 3.12** in `chapter-4-code/.venv`, made with `uv venv --python 3.12` like Chapter 3.
- **Pinned versions** (tested together): `opencv-python` 5.0.x, `numpy`, `pyserial` 3.5, `lameenc` 1.8.4, `requests`. **No MediaPipe needed in this chapter.**
- **One serial owner.** The bridge runs a reader thread, a ntfy thread, a scheduler thread and a speech worker, all talking through `queue.Queue`. The camera loop runs on the **main thread**, because macOS requires OpenCV windows there. Ctrl+C or Q shuts everything down cleanly.
- **`--fake-arduino` flag:** a built-in simulator (pyserial `loop://` or an in-process fake) that answers `PONG`/`OK` and can emit fake `EVENT VISITOR` lines. Everything except real sound and LCD can then be tried without hardware.
- **Arduino sketch:**
  - Fixed 65-byte line buffer and no `String` class in the loop. Use `F("...")` for constant text (the UNO has only 2 KB of RAM).
  - Reads the sensor every ~100 ms without blocking serial input for long.
  - Prints `READY` at boot.

## Testing

**Python (pytest), no hardware needed:**

- protocol formatting and parsing, including bad and too-long lines
- LCD word-wrap and emoji cleaning
- the `say` call uses a list of arguments (mock `subprocess.run`), and the injection test from Step 1
- rate limit, queue overflow, quiet hours and cooldowns, with a fake clock
- scheduler firing once, on the right days, with a fake clock
- ntfy handler: a mocked stream with `open`, `keepalive`, `message` and duplicate ids, plus reconnect after an error
- face decision rule with synthetic 128-number vectors: clear match, brother too close (gives "friend"), stranger (gives "friend"), and the 3-of-5 frames rule
- an end-to-end run with `--fake-arduino` and a mocked ntfy: a phone message becomes `SHOW` plus speech, and `EVENT VISITOR` becomes a publish

**Arduino:** compile `robot_bridge.ino` for the UNO, with and without the DFPlayer code path. Use `arduino-cli` if it's installed. Otherwise give the guide a Serial Monitor test script that walks through every command in the protocol table.

**Real hardware** (the family does this, and the guide shows it as a checklist): each step's Acceptance list above.

---

## Privacy and secrets

Add to `.gitignore`:

```
chapter-4-code/config.json
chapter-4-code/people.json
chapter-4-code/phrases.json
chapter-4-code/faces/
chapter-4-code/models/
chapter-4-code/sd_card/
chapter-4-code/robot_bridge/phrases.h
**/.venv/
*.onnx
*.tflite
*.task
```

- **Secret topics** live only in `config.json`. If one ever leaks, run `setup_cloud.py --new-topics` and update the Shortcut.
- **Faces:** embeddings only, local only, deletable, and only for people who said yes.
- **The public page** uses "Kid 1" and "Kid 2". No real names, photos of faces, or topics.

---

## Grown-up corner: the same architecture you build at work

| This project | The cloud world |
|---|---|
| ntfy "to robot" topic | SNS topic / SQS queue |
| The bridge streaming from ntfy | A consumer long-polling: outbound only, no open ports |
| `robot_bridge.py` | A small service (or Lambda) that consumes, decides and produces |
| USB serial line | A private channel to a device |
| The Arduino | An IoT "thing" |
| `EVENT VISITOR` lines | Device telemetry |
| Schedule thread | EventBridge Scheduler / cron |
| Cooldowns and rate limits | Throttling and dedup |
| Retries with backoff | Retry policy |
| Arduino talks on its own when the Mac is gone | Graceful degradation |
| `faces/` and `config.json` | Sensitive data and secrets: never in the repo |

The production version of this pattern is AWS IoT Core: MQTT topics plus device shadows. An ESP32 could later replace the Mac as the bridge, with Wi-Fi built in.

---

## Facts checked (October 2026)

| Fact | Checked |
|---|---|
| OpenCV 5.0.0 has `FaceDetectorYN` and `FaceRecognizerSF`, and both model URLs above download and run with it. Embeddings are 128 numbers | Tested in a Python 3.12 environment |
| OpenCV's suggested threshold: same person if cosine ≥ 0.363 (or L2 ≤ 1.128) | [OpenCV DNN face tutorial](https://docs.opencv.org/5.0/tutorials/dnn/dnn_face/dnn_face.html) |
| `lameenc` 1.8.4 encodes MP3 from 16-bit PCM | Tested |
| pyserial `loop://` works for a fake Arduino | Tested |
| DFRobotDFPlayerMini 1.0.6: `begin(stream, isACK, doReset)`; `playMp3Folder(4)` plays `SD:/MP3/0004.mp3` | [Library source and example](https://github.com/DFRobot/DFRobotDFPlayerMini) |
| DFPlayer: 3.2 to 5 V, FAT16/FAT32 cards up to 32 GB, speakers under 3 W, 1 kΩ in series on RX | [DFRobot wiki](https://wiki.dfrobot.com/dfplayer_mini_sku_dfr0299) |
| ntfy: JSON stream at `<topic>/json` with `open`/`keepalive`/`message` events. Publishing as JSON goes to the root URL `https://ntfy.sh/`. "The topic is essentially a password", so pick unguessable names | [ntfy subscribe API](https://docs.ntfy.sh/subscribe/api/), [publishing](https://docs.ntfy.sh/publish/) |
| macOS `say` writes audio files with `-o` (AIFF by default) and supports embedded commands like `[[slnc 200]]` | [Command-line audio on a Mac](https://josh8.com/blog/commandline-audio-mac.html) |

Not checked on real hardware yet: actual speech timing, the Siri Shortcut on the family's iPhone, face recognition accuracy on the brothers, and the specific DFPlayer clone that gets bought.
