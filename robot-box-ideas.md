# 💡 Robot Box Ideas

**Bored of the current app? Pick the next one here.**

Every idea runs on the same box from Chapter 7: a Raspberry Pi, a camera, a touchscreen, a speaker and two buttons. Only the software changes. To start one, copy `robot-box/apps/_template/` and follow "Make a new app" in Chapter 7.

Add new ideas to the bottom whenever someone says "what if the box could...". That's how engineers keep a backlog.

**Difficulty:** ⭐ a Sunday morning · ⭐⭐ one or two Sundays · ⭐⭐⭐ a project

---

## The ideas

| # | App | What it does | AI it uses | Difficulty | Status |
|---|---|---|---|---|---|
| 1 | ✊ **Rock Paper Scissors** | Best of 5 against the robot, with a leaderboard | Hand gestures | ⭐⭐ | Built in Chapter 7 |
| 2 | ⚡ **Reaction Tester** | The screen turns green at a random moment; slap button A as fast as you can. Milliseconds and a family leaderboard | None | ⭐ | Built in Chapter 7 as the example app |
| 3 | 👀 **Staring Contest Judge** | Two players face the camera. The first one to blink loses, and the robot calls it | Face landmarks (blink detection) | ⭐⭐ | Idea |
| 4 | 🤸 **Weirdest Pose** | The robot draws your skeleton, and the strangest pose wins points. Or play "copy my pose" like Simon Says | Body pose | ⭐⭐ | Idea |
| 5 | 🐱 **Pet Detector** | Plays a sound and counts visits when the cat or dog walks past | Object detection | ⭐⭐ | Idea |
| 6 | 🔢 **People Counter** | Counts how many people walked past today, and shows a chart at bedtime | Person detection | ⭐⭐ | Idea |
| 7 | 🏆 **Scoreboard** | A touchscreen scoreboard for family games: board games, ping pong, basketball | None | ⭐ | Idea |
| 8 | 🛡️ **Room Guard** | When someone enters the room, it sends a message to a parent's phone | Person detection + phone messages (Chapter 4) | ⭐⭐ | Idea (privacy rules below) |
| 9 | 👋 **Name Greeter** | Greets each brother by name at the door with his catchphrase and tune | Face recognition (Chapter 4) | ⭐⭐⭐ | Idea (privacy rules below) |
| 10 | 🎯 **Follow-Me Head** | The box sits on a pan-tilt mount and turns to keep you in the middle of the picture. The first step toward the follow-me robot | Person detection on the AI Camera + 2 servos | ⭐⭐⭐ | Idea |

---

## How each one works

### 3. 👀 Staring Contest Judge

- **AI:** MediaPipe **Face Landmarker** with blendshapes turned on. It reports `eyeBlinkLeft` and `eyeBlinkRight` scores from 0 to 1 for each face.
- **Rule:** up to 2 faces. A blink is either eye score above about 0.5 for 2 or more frames in a row (tune it!).
- **Screen:** both faces with live "eyes open" meters, a timer, and a big "BLINK! Kid 2 loses" at the end.
- **New skill:** thresholds and debouncing on real, noisy numbers.

### 4. 🤸 Weirdest Pose

- **AI:** MediaPipe **Pose Landmarker** (33 body points), or the AI Camera's built-in PoseNet.
- **Weirdness score:** how far each joint is from a normal standing pose, averaged. Hold still for 2 seconds to lock it in.
- **Copy-my-pose mode:** the robot shows a stick figure, and you score points for matching it within 5 seconds.
- **New skill:** comparing shapes with math (distances between points).

### 5. 🐱 Pet Detector

- **AI:** MediaPipe **Object Detector** (it knows everyday things, including "cat" and "dog"), or the AI Camera's built-in object detector.
- **Rule:** the pet has to be seen for 1 second to count as a visit, and visits are counted at most once a minute.
- **New skill:** filtering out false alarms.

### 6. 🔢 People Counter

- **AI:** person detection. It's best on the AI Camera, where it runs on the camera chip and the Pi stays cool.
- **Rule:** count a person when they cross an imaginary line in the middle of the picture (left to right is "in", right to left is "out").
- **Screen:** today's count, plus a bar chart by hour.
- **New skill:** tracking something across frames, and drawing charts.

### 7. 🏆 Scoreboard

- **No AI.** Big + and − touch buttons for up to 4 players, sound effects, and "winner!" confetti.
- **New skill:** touchscreen interface design. A great app for the younger builder to build on his own.

### 8. 🛡️ Room Guard

- **AI:** person detection. Uses Chapter 4's phone messages (secret ntfy topic).
- **Rules (privacy first):**
  - Only for your **own** room, and only when you switch it on.
  - Everyone in the house knows it exists.
  - By default it sends **text only** ("Someone entered your room at 4:12 pm"), **no photos**.
  - If photos are added later, they stay on the box and are deleted after 24 hours.
- **New skill:** connecting the box to the internet safely.

### 9. 👋 Name Greeter

- **AI:** OpenCV's YuNet face finder and SFace face fingerprints, the same as Chapter 4, Step 5.
- **Rules (privacy first):**
  - Each person agrees before being added.
  - Only face "fingerprints" (128 numbers) are stored, never photos.
  - It stays on the box, and you can delete yourself any time.
  - If it's not sure, it says "Hello, friend!"
- **New skill:** the hardest app on the list. Reuse Chapter 4's code instead of starting from scratch.

### 10. 🎯 Follow-Me Head

- **AI:** person detection on the AI Camera, so the Pi gets the box position directly.
- **Hardware:** a pan-tilt bracket with 2 servos, driven by the Chapter 1 Arduino over USB. The Arduino is better at smooth servo control than the Pi's pins.
- **Rule:** the person's box should stay in the middle of the picture. If it's left of center, turn left a little, and the farther off it is, the bigger the turn. A small "dead zone" in the middle stops it from wobbling.
- **Know its limit:** it follows **a** person (the biggest one in view), not a specific kid. A bright hat or a printed marker can tell it who to follow.
- **New skill:** a control loop, the same idea as the follow-me robot car. Do this one before putting wheels on anything.

---

## Rules for every app

- **No photos saved** unless the app says so on screen and you switched it on.
- **Anything with faces or names** stays on the box, and only for people who agreed.
- **Real names never go in the public repo.** Use `config.json` (gitignored).
- **If an app could bother someone** (sounds at night, messages to phones), it gets an off switch and quiet hours.

## Ideas parking lot

*Add new ideas here as a one-line wish. Move them to the table when someone wants to build one.*

-
