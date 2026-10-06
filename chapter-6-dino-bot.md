# 🦖 Chapter 6: Dino Bot

A robot that plays a video game, **like a person**: it watches the screen with a light-sensing eye and presses the space bar with a servo finger. The Chrome dinosaur jumps over cacti on its own, and then the boys upgrade the robot's brain until it survives night mode, the speed-ups, and the birds.

The robot doesn't hack the game. It sees and presses, exactly like you do.

| | |
|---|---|
| **Builders** | Two kids, ages 13 (7th grade) and 10 (5th grade), plus a parent |
| **Time** | About 2½ to 3 hours. Two Sundays: Steps 1 to 4 (first autopilot), then Steps 5 to 8 (make it unbeatable) |
| **Before this** | Chapter 1 (LCD and buzzer wiring). Independent of Chapters 3 to 5 |
| **Computer** | Any computer with Chrome. The game runs at `chrome://dino`, no need to unplug the internet |

---

## Notes for the builder (Claude Code)

This file is the chapter content and the build spec. Please create:

1. **`chapter-6-code/`**, as listed in [Code layout](#code-layout).
2. **`chapter-6-dino-bot.html`**, the kid guide, matching the style of the other chapter pages: mission map, step cards, badges, copy buttons, saved checkmarks, dark mode. Link it from `index.html`, and add Chapter 6 rows to the README chapter table and `roadmap.md`.
3. **An interactive "Dino Lab" simulator** on the page ([details below](#dino-lab-the-interactive-simulator)). Kids tune the robot's brain on screen before touching hardware.

Ground rules:

- **Each step ends with a win**, like the earlier chapters.
- **One sketch, four brains.** `dino_bot.ino` has `#define LEVEL 1` at the top. Kids upgrade the robot by changing one number and re-uploading. The decision logic lives in `dino_logic.h` (pure functions, no Arduino calls), so it can be tested on the computer.
- **Wiring baseline:** the LCD (12, 11, 5, 4, 3, 2) and buzzer (8) from Chapter 1 stay. The ultrasonic sensor is **not used**; remove it to free pins 9 and 10. (Chapter 2's Secret Code Bot already removes it.)
- **Test the logic without hardware** using recorded and synthetic light traces ([Testing](#testing)), and say honestly in the guide what was and wasn't tested on a real screen.

---

## The big idea: a robot that uses a computer like a person

```
 🖥️ Screen shows a cactus ──light──► 👁️ light sensor ──► 🧠 Arduino ──► 🦾 servo ──press──► ⌨️ space bar ──► 🖥️ dino jumps
          ▲                                                                                          │
          └──────────────────────────────────────── the game reacts ◄────────────────────────────────┘
```

Same loop as every chapter: **sense → think → act.** But this time the robot sits **outside** the computer. It can only see the screen and press keys, like a person.

- Kids' version: *"The robot has one eye glued to the screen and one finger over the space bar. When the eye sees something dark coming, the finger presses."*
- Grown-up version: this is a closed control loop through a physical interface. Any delay in the eye, the brain or the finger becomes **latency**, and the game gets faster every second. The whole chapter is a lesson in beating latency.

---

## Know your enemy: game facts

| Fact | Value |
|---|---|
| Open the game | `chrome://dino` in Chrome. Press **Space** to start |
| Controls | **Space** or **↑** = jump (hold for a higher jump, tap for a short hop). **↓** = duck |
| Speed | Starts at 6 pixels per frame and slowly speeds up to a max of 13. More than twice as fast by the end |
| Night mode | Around every **700 points**, the colors flip: dark background, light cacti. Then it flips back |
| Birds | Only appear once the game is fast enough. They fly at **three heights**: low (jump over it), middle (duck under it), and high (do nothing, because jumping into it is a crash) |
| Colors | Dark grey shapes on a near-white background (by day) |

---

## What you need

| Part | Where from |
|---|---|
| UNO, breadboard, LCD, buzzer (Chapter 1 wiring) | Kit |
| **Servo** (the kit's **SG90**, or a **Tower Pro MG90S**) | Kit, or the MG90S you have |
| **2 photoresistors** (light sensors) + **2 × 10 kΩ resistors** | Kit |
| **Breadboard power supply module** + **9 V battery** (power for the servo) | Kit |
| **An external keyboard** (strongly recommended) | Any old USB or Bluetooth keyboard |
| Painter's tape, a black straw or black tape (light shield), a pencil eraser (soft fingertip), and something to hold the servo up (Lego, a book stack, cardboard) | Around the house |
| Boss level only: **1 more photoresistor** and **1 more servo** | A cheap pack of photoresistors and an SG90 |

**SG90 or MG90S?** Both have the same 3 wires: **brown** = ground, **red** = 5 V, **orange** = signal. The MG90S has metal gears and is a bit stronger (about 1.8 kg·cm at 4.8 V) and fast (0.1 s per 60°). Either one easily presses a key. Use the MG90S for the space bar if you have it.

⚠️ **Protect the MacBook.** Point the servo finger at an **external keyboard**, not the laptop's own keys. If you must use the laptop keyboard, put a soft eraser on the servo arm and calibrate gently (Step 2). Tape sensors to the screen with **painter's tape only**, never glue.

---

## The 8 steps

| Step | Name | Time | The win |
|---|---|---|---|
| 1 | 🦖 Study the enemy | 15 min | A list of every danger the robot must handle |
| 2 | 🦾 Build the finger | 25 min | The servo taps the space bar on command and the dino jumps |
| 3 | 👁️ Build the eye | 25 min | You **see** each cactus as a dip on the Serial Plotter graph |
| 4 | 🤖 Autopilot, Level 1 | 20 min | The dino jumps cacti by itself. Write down the high score |
| 5 | 🌗 Level 2: night vision | 20 min | It survives night mode |
| 6 | ⚡ Level 3: speed trap | 30 min | It measures the game's speed and times each jump, so it keeps going as things speed up |
| 7 | 🐦 Boss level: the birds | 30 min | A second eye and finger: jump low birds, duck middle birds, ignore high ones |
| 8 | 🏁 Human vs robot | 15 min | The family tournament: who gets the highest score? |

---

## Step 1: 🦖 Study the enemy

### Kids see

Each brother plays a few rounds and writes down **everything that can kill the dino**: small cactus, big cactus, groups of cacti, birds at different heights, night mode, the speed-up.

This list is the robot's **test plan**. Every later level beats one more item on it.

💡 **Parent tip:** this is exactly how engineers start: write down what "working" means *before* building. Keep the list on the fridge and tick items off as each robot level beats them.

---

## Step 2: 🦾 Build the finger

### Wiring

| Wire | Goes to |
|---|---|
| Servo **orange** (signal) | UNO pin **9** |
| Servo **red** (5 V) | **Power module's 5 V** rail, **not** the UNO's 5 V |
| Servo **brown** (ground) | Power module **GND**, **and** a wire from that GND to the UNO's GND (shared ground is a must) |
| Power module | Set its jumpers to **5 V**. Power it from the kit's 9 V battery |

**Why a separate power supply?** When a servo pushes hard, it gulps current. Powered from the UNO, it can make the UNO's voltage dip and restart it in the middle of a game.

### Calibrate

1. Upload `servo_calibrate`. In the Serial Monitor (9600 baud), type an angle like `90` and press Return. The servo moves there.
2. Find **REST** (finger just above the key) and **PRESS** (key pressed, not crushed). The two are usually 15 to 25 degrees apart.
3. Type `t` for a test tap: the finger goes REST → PRESS → REST.
4. Mount the servo over the space bar (Lego, books, tape) and tap. In `chrome://dino`, the dino jumps.

### Build requirements

`servo_calibrate`:
- Accepts angles from 0 to 180, `t` (tap), and `h` (hold for 300 ms).
- Prints the current angle.
- Moves in small steps so it never slams.
- The guide tells kids to copy the REST and PRESS numbers into `dino_bot.ino`.

### Kid challenge

Measure the finger: how many taps per second can it do before it misses? (That's one of the speed limits of your robot.)

---

## Step 3: 👁️ Build the eye

### Wiring (for each light sensor)

```
5V ──── photoresistor ────┬──── A0   (second sensor on A1, third on A2)
                          │
                       10 kΩ
                          │
GND ──────────────────────┘
```

More light means a **higher** number (0 to 1023).

### Mounting the eye on the screen

1. Open `chrome://dino` and **zoom in** with **⌘ +** a few times, so the game is big and the cacti are wider than the sensor.
2. Screen **brightness to max**. Turn off auto-brightness, True Tone and Night Shift, so the screen doesn't change brightness on its own.
3. Slide the sensor into a short piece of **black straw** (or wrap it in black tape) so room light can't sneak in. Only screen light should reach it.
4. Tape it flat against the screen **at cactus height**, a little **ahead** (to the right) of the dino. A starting point is about one dino-length ahead. You'll tune this in Step 4.

### See it

Upload `light_check` and open **Tools → Serial Plotter**. Start the game. Every cactus that passes the eye makes a **dip in the line**. That dip is the robot "seeing" a cactus.

### Build requirements

`light_check`:
- Prints `A0`, `A1` and `A2` in Serial Plotter format about 200 times a second.
- Also shows the A0 value on the LCD.

### Kid challenge

How deep is the dip for a small cactus compared to a big one? What happens to the line when night mode starts? (Spoiler: it flips upside down.)

---

## Step 4: 🤖 Autopilot, Level 1

### Kids see

1. In `dino_bot.ino`, set `LEVEL 1`, fill in REST, PRESS and the light threshold (halfway between the "white" number and the "cactus" number from the plotter), then upload.
2. Start the game and take your hands off. 🎉 **The dino plays itself.**
3. The LCD shows the level, the jump count and the live light value. A tiny beep plays on each jump (`BEEP_ON_JUMP` can be set to `false`).
4. When it crashes, write down the score. **Why did it crash?** Usually it's one of:
   - jumping too early or too late, so move the eye closer or farther,
   - night mode,
   - the game got too fast.

### Level 1 brain

- If the light is **below** the threshold, tap the space bar.
- After each tap, ignore the eye for a short **cooldown** (about 300 ms), so one cactus means one jump.

### Kid challenge

Tune `PRESS_MS` (how long the finger holds the key: a longer hold means a higher jump) and the eye's position for the best score. Record every attempt in a table: position, hold time, score. That's a real experiment log.

---

## Step 5: 🌗 Level 2: night vision

### The problem

At night the screen flips: the background goes dark, so Level 1 thinks "cactus!" forever and jumps non-stop.

### Level 2 brain

- **Adaptive baseline:** the robot keeps a slowly-updating average of "normal" light, and doesn't update it while an obstacle is passing.
- **Trigger on a big change in either direction**, not just "dark". By day a cactus makes the light drop. At night it makes the light rise. Either way, it's different from normal.
- During the fade between day and night the average catches up within about a second. Ignore triggers while the baseline is changing fast.

### Kid explanation

*"Instead of 'jump when it's dark', the robot learns what normal looks like and jumps when something is different."* Your eyes do this too when you walk into a dark room.

---

## Step 6: ⚡ Level 3: speed trap

### The problem

As the game speeds up, cacti reach the dino sooner. The finger always needs the same time to press, so the jump comes too late.

### Level 3 brain

1. Put the **second sensor** (A1) a little **farther ahead** of the first, at the same height. Measure the gap between them in millimeters and type it into `SENSOR_GAP_MM`.
2. When a cactus passes sensor 2 and then sensor 1, the time between them gives the **speed**, just like a police speed trap or a race's timing gates.
3. The robot **predicts** when the cactus will reach the dino and starts the press early enough to cover its own delay (`ROBOT_DELAY_MS`, measured in the challenge below).
4. Schedule presses with `millis()`. **Never use `delay()`** in the game loop, or the eyes go blind while waiting.

### Kid challenge: measure the robot's own delay

Add a debug mode that records when the eye saw something and when the dino started to rise (watch with a slow-motion phone video at 240 fps). The difference is your robot's **latency**. Put it in `ROBOT_DELAY_MS`.

### Grown-up corner

Level 1 is a purely reactive controller. Level 3 adds **feed-forward prediction** that compensates for known actuator latency: measure the input's velocity and act ahead of time.

---

## Step 7: 🐦 Boss level: the birds

Needs one more photoresistor and one more servo.

### Setup

- **Head-height eye** on **A2**: at the height of the dino's head, a little ahead.
- **Duck finger** on pin **10**: a second servo over the **↓** key (same power module and shared ground).

### Level 4 brain

| Low eye (A0) | Head eye (A2) | Action |
|---|---|---|
| sees something | anything | **Jump** (cactus or low bird) |
| clear | sees something | **Duck**: hold ↓ until the head eye is clear again (middle bird) |
| clear | clear | Nothing (that includes high birds, which pass above both eyes) |

Ducking and jumping must never happen at the same time: jumping wins, and the duck is released first.

### Kid challenge

Why must the robot **not** jump at a high bird? (Draw it: the dino jumps right into it.)

---

## Step 8: 🏁 Human vs robot

- **Family tournament:** each brother's best human score against the robot's best at each level. Make a scoreboard.
- **Make it yours:** a victory tune at every 1,000 points (the robot can't read the score, so count jumps instead), a funny LCD message for each level, an "ARE YOU WATCHING?" message during long runs.
- **Talk about it:** is the robot cheating? It only sees and presses like a human. Then why does it beat us? (No blinking, no getting tired, perfect timing.) Where else do robots press buttons for people? (Factory testing machines that tap phone screens thousands of times.)
- **Safety stop:** the sketch stops pressing after 30 minutes (`MAX_RUN_MINUTES`). Servos and keyboards wear out, and robots shouldn't run unattended forever.

---

## Pin map

| UNO pin | Goes to |
|---|---|
| **12, 11, 5, 4, 3, 2** | LCD (Chapter 1) |
| **8** | Buzzer (Chapter 1) |
| **9** | Jump servo signal (orange) |
| **10** | Duck servo signal (Step 7) |
| **A0** | Low eye (cactus height, near the dino) |
| **A1** | Speed-trap eye (same height, farther ahead) (Step 6) |
| **A2** | Head-height eye (Step 7) |
| **GND** | Shared with the power module's GND |

Servo red wires go to the **power module's 5 V**, never to the UNO's 5 V. The Servo library uses the UNO's Timer1, and `tone()` uses Timer2, so the servo and buzzer don't clash.

---

## Code layout

```
chapter-6-code/
├── servo_calibrate/servo_calibrate.ino   Step 2
├── light_check/light_check.ino           Step 3 (Serial Plotter + LCD)
├── dino_bot/
│   ├── dino_bot.ino                      Steps 4 to 8: #define LEVEL 1, 2, 3 or 4, plus settings at the top
│   └── dino_logic.h                      pure decision logic: thresholds, baseline, speed trap, jump/duck rules
├── record_trace.py                       saves live sensor values to a CSV (for replay tests)
└── tests/
    ├── replay_test.cpp                   compiles dino_logic.h on the computer and replays traces
    ├── make_traces.py                    generates synthetic traces
    └── traces/                           day.csv, night_flip.csv, speeding_up.csv, birds.csv (+ real recordings later)
```

### Technical constraints

- `dino_logic.h` has **no Arduino calls**. Time and sensor values are passed in as arguments, so the same code runs on the UNO and in desktop tests.
- The main loop never uses `delay()`. Servo moves are scheduled with `millis()` (press start, release time, cooldown).
- Settings at the top of `dino_bot.ino`, with kid-friendly comments: `LEVEL`, `REST_ANGLE`, `PRESS_ANGLE`, `DUCK_REST_ANGLE`, `DUCK_PRESS_ANGLE`, `PRESS_MS`, `THRESHOLD`, `COOLDOWN_MS`, `SENSOR_GAP_MM`, `ROBOT_DELAY_MS`, `BEEP_ON_JUMP`, `MAX_RUN_MINUTES`.
- The LCD updates at most 5 times a second, so it doesn't slow the loop.

## Testing

**Desktop (no hardware):** `tests/replay_test.cpp` built with `g++` against `dino_logic.h`.

- **Day trace:** one jump per cactus, never two, and no jumps when the screen is clear.
- **Night flip trace:** Level 1 fails (jumps non-stop, which is expected and shown as the lesson). Level 2 makes exactly one jump per obstacle across the flip.
- **Speeding-up trace:** Level 3's press start moves earlier as obstacles get faster. Its predicted arrival is within ±15% of the true arrival in the synthetic data.
- **Birds trace:** low bird → jump, middle bird → duck, high bird → nothing. Jump and duck never overlap.
- `record_trace.py` lets the family record real traces (`python record_trace.py > tests/traces/my_screen.csv`), which then become new replay tests. Record once, test forever.

**Arduino:** all three sketches compile for the UNO at every `LEVEL` (1 to 4). Use `arduino-cli` if available.

**Real hardware (the family's checklist on the page):**

- Level 1 jumps the first cacti.
- Level 2 makes it through the first night mode.
- Level 3 keeps timing right after the speed-up.
- Level 4 handles at least one bird of each height.

Scores depend on the screen, so the page records them instead of promising numbers.

---

## Dino Lab: the interactive simulator

A section of `chapter-6-dino-bot.html` that runs entirely in the browser (plain JavaScript and canvas, offline):

- A simple scrolling game strip (rectangles are fine: a dino, cacti, birds at three heights) that speeds up over time and flips to night mode.
- A **live sensor graph** under it, like the Serial Plotter, showing what eyes A0, A1 and A2 would read.
- **Controls:**
  - a robot level picker (1 to 4)
  - a threshold slider
  - an eye-position slider
  - a robot delay slider
  - a game speed boost button
  - a night mode button
- The simulated dino uses the **same rules** as `dino_logic.h`. The simulator is ported from it, and the docs say so.
- **Win and lose feedback:** score counter, "crashed because: too late / night mode / bird", and a best-score table per level.
- Lets kids discover each level's weakness on screen before the real build, for example "Level 1 dies at night".

---

## Grown-up corner: why this is a serious engineering lesson

| In this chapter | In the real world |
|---|---|
| Robot presses keys on a computer it can't control from inside | Device-testing robots that tap phone screens; UI automation bots that click through apps |
| Eye → brain → finger delay | The latency budget in any control loop |
| Level 2 adaptive baseline | Auto-calibration and drift handling in sensors |
| Level 3 speed trap | Feed-forward control: predict instead of only react |
| Record traces, replay them in tests | Fixtures and record/replay integration tests |
| `MAX_RUN_MINUTES` | A watchdog or kill switch for unattended automation |
| Flaky readings when room light changes | Flaky tests caused by uncontrolled environments |

**Level-up idea:** an Arduino **Leonardo** or **Pro Micro** can pretend to be a USB keyboard and "press" keys electronically, with no servo at all. The UNO can't. Is that version more or less fun? (The servo is the fun part.)

---

## Facts checked (October 2026)

| Fact | Source |
|---|---|
| Game speed from 6 to a max of 13, night mode at 700 points, birds once speed reaches 8.5, Space to jump, ↓ to duck, hold for a higher jump | [How the Chrome Dino game works (freeCodeCamp tour of Chromium's source)](https://www.freecodecamp.org/news/how-the-chrome-dino-game-works/) |
| MG90S: 4.8 to 6 V, about 1.8 kg·cm at 4.8 V, 0.1 s per 60°, metal gears; brown/red/orange wires | [Components101: MG90S](https://components101.com/motors/mg90s-metal-gear-servo-motor) |
| The kit has an SG90 servo, 2 photoresistors, a power supply module and a 9 V battery | [ELEGOO UNO R3 Super Starter Kit contents](https://www.keystoneenterprises.com/maker-electronics/elegoo-uno-r3-project-super-starter-kit.html) |
| Common versions use one LDR + 10 kΩ divider, mounted ahead of the dino; they fail as the game speeds up and need re-calibrating for screen brightness | [Arduino-dino-bot](https://github.com/MichaelBukatin/Arduino-dino-bot), [ESP32 servo Chrome dino](https://github.com/Mr-soumik/ESP32-Servo-Motor-Automated-Chrome-Dino) |

**Not verified:** the exact bird heights in pixels (the three-height rule above is what matters), and how the game looks on this family's screen. That's what Step 3 measures.
