# 🤖 Door Greeter Bot

A gadget that sits by the bedroom door, spots you walking up, plays a tune, lights an LED, and shows a greeting on a little screen. Built with an Arduino UNO in one afternoon.

This is project #1 in a series of hands-on builds for two brothers.

## Chapters

| Chapter | Gadget | Open this file | Input | Status |
|---|---|---|---|---|
| 1 | 🤖 Door Greeter Bot | `door-greeter-build-guide.html` | Ultrasonic sensor | Built and working |
| 2 | 🔐 Secret Code Bot | `chapter-2-secret-code-bot.html` | IR remote | Built and working |
| 3 | 👀 Robot Eyes | `chapter-3-robot-eyes.html` | The Mac's camera + AI (Python) | Ready to build |
| 4 | 🗣️ The Talking Robot | `chapter-4-talking-robot.html` + `chapter-4-code/` | A phone, the clock and the camera, through the Mac | Ready to build |
| 6 | 🦖 Dino Bot | `chapter-6-dino-bot.html` + `chapter-6-code/` | Light sensors watching the screen | Ready to build |
| 7 | 📦 The Robot Box | `chapter-7-robot-box.html` + `robot-box/` | A Raspberry Pi with a camera, in its own box (also runs on the Mac) | Ready to build; Pi parts not tested on a real Pi yet |
| Bonus | 🔬 Inside the Robot | `inside-the-robot.html` | Nothing to build: tap, drag and slide | Play any time after Chapter 1 |
| Bonus | 📱 The Phone Robot | `phone-robot.html` + `phone-robot/` | An iPhone's camera, with the AI running in Safari | Ready to play; tested in a Mac browser, not on an iPhone yet |

Each chapter keeps the screen and buzzer wired the same way and swaps only the input. The rest of this README describes Chapter 1; Chapter 2's differences are below.

### Chapter 2: Secret Code Bot

Type a secret code on the kit's remote. The screen shows stars, the right code plays a victory tune, and three wrong guesses set off an alarm with a countdown.

- **New parts**: IR receiver module and IR remote (ELEGOO lesson 2.12, IR Receiver).
- **Comes out**: the ultrasonic sensor and its 4 wires. Pins 9 and 10 are free again.
- **New wiring**: receiver **G** → − rail, **R** → + rail, **Y** → UNO pin **7**.
- **Unchanged**: LCD on 12, 11, 5, 4, 3, 2 and the buzzer on pin 8.
- **No library to install**: the code reads the remote by timing its flashes, the same way ELEGOO's lesson does. That also keeps it from clashing with the buzzer.
- **Steps**: 👂 swap eyes for ears, 🎹 remote piano, 🔐 the secret code, 🚨 make it fight back, 🎨 make it yours, 📦 build the vault.

## Who it's for

| | |
|---|---|
| **Builders** | Two kids |
| **Helper** | A parent, mostly asking "what do you think will happen?" |
| **Time** | About 2 to 2½ hours, snack breaks included |
| **Experience needed** | None |

## Goals

1. **Fun first.** If it stops being fun, take a break.
2. **A win at every step.** Each step ends with something that works, so you can stop anywhere.
3. **Kids change the code.** Every step has a challenge where the kids edit a number or a word and see what happens.
4. **Two jobs, swap every step.**
   - 🔧 **Builder** plugs in the wires and tests the gadget.
   - ⌨️ **Coder** reads the step out loud, uploads the code, and makes the code changes.

## How to use it

Open **`door-greeter-build-guide.html`** in a browser (double-click it) and follow along. It has the wiring pictures, the code with copy buttons, and checkmarks that remember how far you got. It works offline.

You also need the **Arduino IDE** on the Mac: <https://www.arduino.cc/en/software>

## What you need

Everything comes from the **ELEGOO Super Starter Kit for UNO**:

- UNO R3 board + USB cable
- Breadboard (the big white one)
- Ultrasonic sensor (HC-SR04)
- LCD screen (1602) + potentiometer (the knob)
- Passive buzzer (green circuit board underneath)
- 1 LED and 2 resistors of 220 Ω
- About 25 male-to-male jumper wires
- For mounting: a small box, tape, and a USB phone charger or power bank

## The 6 steps

| Step | Name | Part you add | Time | The win |
|---|---|---|---|---|
| 1 | 💻 Set up the computer | UNO + USB | 15 min | The **L** light blinks at your speed |
| 2 | 👀 Give it eyes | Ultrasonic sensor | 20 min | Distance numbers change when you move your hand |
| 3 | 🔊 Give it a voice | Passive buzzer | 20 min | Parking-sensor beeps that speed up as you get close |
| 4 | 🖥️ Give it a face | LCD screen + knob | 45 min | Tune, light, and a random greeting with a visitor count |
| 5 | 🎨 Make it yours | Code only | 15 min | Your own greetings, distance, and tune |
| 6 | 🚪 Mount it at the door | Box + power bank | 20 min | It guards the bedroom door |

## Pin map

Every wire on the UNO, matching the code in the guide.

| UNO pin | Goes to |
|---|---|
| **5V** | Breadboard **+** rail (red wire) |
| **GND** | Breadboard **−** rail (black wire) |
| **9** | Sensor **Trig** |
| **10** | Sensor **Echo** |
| **8** | Passive buzzer **+** leg |
| **7** | 220 Ω resistor → LED long leg |
| **12** | LCD pin 4 (**RS**) |
| **11** | LCD pin 6 (**E**) |
| **5** | LCD pin 11 (**D4**) |
| **4** | LCD pin 12 (**D5**) |
| **3** | LCD pin 13 (**D6**) |
| **2** | LCD pin 14 (**D7**) |

LCD power pins: 1 → −, 2 → +, 3 → knob middle leg, 5 → −, 15 → 220 Ω → +, 16 → −. Pins 7 to 10 stay empty.

## What's in this folder

```
Door Greeter Bot/
├── README.md                       ← you are here
├── door-greeter-build-guide.html   ← Chapter 1 guide
├── chapter-2-secret-code-bot.html  ← Chapter 2 guide
└── available-parts/                ← ELEGOO's downloads for the kits we own
    ├── ELEGOO-Super-Starter-Kit-for-UNO/         (used for this project)
    └── ELEGOO Smart Robot Car Kit V4.0 .../      (saved for a later project)
```

ELEGOO lessons that match this build, in `available-parts/ELEGOO-Super-Starter-Kit-for-UNO/English/Part 2/`:

| Part | Lesson PDF |
|---|---|
| LED | 2.1 LED |
| Passive buzzer | 2.6 Passive buzzer |
| Ultrasonic sensor | 2.9 Ultrasonic Sensor |
| LCD screen | 2.13 LCD 1602 |

The guide's code needs no extra library downloads: `LiquidCrystal` comes with the Arduino IDE, and the sensor is read with a few lines of plain code. Note that the guide uses its own pin numbers, which differ from the ELEGOO lesson PDFs. Follow the guide.

## Round 2 ideas

All with parts already in the Super Starter Kit:

- **Remote-control modes** (lesson 2.12, IR receiver): button 1 = greeter, button 2 = "Do not disturb", button 3 = alarm siren.
- **A waving hand** (lesson 2.8, servo): tape a cardboard hand to the servo so it waves hello.
- **Room weather** (lesson 2.10, DHT11): show temperature and humidity on the idle screen.
- **Secret handshake**: it stays quiet only if you wave twice quickly in front of it.

## Next projects

The **ELEGOO Smart Robot Car Kit V4.0** is waiting in `available-parts/` for a later project.
