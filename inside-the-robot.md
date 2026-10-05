# 🔬 Inside the Robot

**How boards, chips, code, power and silicon actually work, shown as things you can poke, drag and switch.**

This is a companion to the chapters. The chapters are about *building*. This page is about *understanding*: what's really happening inside the Door Greeter when someone walks up.

| | |
|---|---|
| **For** | Two kids, ages 13 and 10, plus a parent |
| **Time** | 30 to 45 minutes, or one level at a time |
| **Best moment to use it** | After Chapter 1 works, while the real greeter sits on the table next to the screen |

---

## Notes for the builder (Claude Code)

Turn this file into **one self-contained interactive HTML page**, `inside-the-robot.html`, in this folder.

- **Match the look** of `door-greeter-build-guide.html`: same colors, rounded font, hero, sticky mission map, cards, badges, dark mode, and progress saved in the browser (wrapped in try/catch, like the existing page).
- **Reactive, not reading.** Every level has something to drag, tap, toggle or slide. Text stays short; the drawing does the explaining. If a level is just paragraphs, it's not done.
- **Touch first.** The boys live on iPads. Everything must work by tapping and dragging on an iPad, with big targets (44 px or more) and no hover-only features.
- **Offline, no libraries.** Hand-drawn inline SVG and plain JavaScript. No external scripts, fonts or images.
- **Two depths.** A toggle at the top: 🐣 **Simple** (for the 10-year-old) and 🦉 **Deeper** (for the 13-year-old). Deeper mode reveals the extra lines marked **Deeper:** below. Simple mode hides them. Remember the choice.
- **Motion with care.** Animate signals, electricity and bits as moving dots. Respect `prefers-reduced-motion`: show the end state instead of animating.
- **Use the facts in "Facts to keep right"** at the bottom. Don't invent numbers.
- **Mission map:** 5 levels plus the boss level. Each level ends with a "🏅 Badge earned" moment when its interaction is completed.

---

## The story in one picture

Every level zooms in one step closer:

```
 Level 1  The robot loop        sense → think → act
 Level 2  The board             the city: roads, power, doors
 Level 3  The brain chip        memory, the worker, the heartbeat, uploading
 Level 4  Sand that thinks      silicon, the transistor, switches that decide
 Level 5  Small chips, giant chips   Uno, Nano, ESP32, MacBook, AI chips
 Boss     Explain it back       the kids teach it to you
```

The big idea to repeat everywhere: **Input → Brain → Output.** Everything is just signals going in, a decision, and signals going out.

---

## Level 1: 🔁 The robot loop

**Kids see:** three big boxes in a row: **SENSE** (eyes and ears) → **THINK** (brain) → **ACT** (voice, light, screen). Under them, a live copy of the Door Greeter.

**Try it:**
- A slider: "Move your hand" from 300 cm to 5 cm (reuse the echo demo idea from Chapter 1).
- As the hand moves, a dot travels from SENSE to THINK carrying the number, like `cm = 45`.
- THINK shows the real line of code and lights it **green** when true or **grey** when false: `if (cm < 60 && !someoneHere)`.
- When it's true, a dot races to ACT: the buzzer icon wiggles, the LED glows, and a mini LCD shows "Hello, human!".
- Swap the input: three tabs above SENSE: 🦇 **Sensor**, 📡 **Remote button**, 🤖 **AI camera**. THINK and ACT stay exactly the same. Only the input box changes.

**Say it simply:** "Every robot does three things, over and over: notice something, decide, do something. The brain doesn't care *where* a signal came from. A sensor, a remote, or an AI are all just inputs."

**Deeper:** the `loop()` function runs again and again. With `delay(100)` in the greeter, it runs about 10 times a second. Without the delay, it would loop thousands of times a second.

**Try it for real:** walk up to the real greeter and say out loud which box is happening: "sense... think... act!"

**Badge:** 🔁 *Loop Master*, earned by triggering a greeting with all three input types.

---

## Level 2: 🏙️ The board: a tiny city

### 2a. Tour the city

**Kids see:** a big, simple top-down drawing of the UNO board. Glowing dots mark the parts to tap. Tapping one zooms in a little and opens a short card.

| Hotspot | Card says (Simple) | Deeper |
|---|---|---|
| **USB port** (silver box) | "The door for code and power from the computer." | Carries 5 V power and data. |
| **Round power jack** | "A second power door, for a battery." | Recommended 7 to 12 V. The kit's 9 V battery fits here. |
| **Big black chip with 28 legs** | "THE BRAIN. Everything that thinks happens in here." | ATmega328P microcontroller. |
| **Small square chip near the USB port** | "The translator. It turns USB from the computer into words the brain understands." | A second, smaller microcontroller (ATmega16U2 on the official UNO) acting as a USB-to-serial bridge. |
| **Silver oval marked 16.000** | "A clock that ticks 16 million times a second." | A 16 MHz crystal. The brain gets its own 16 MHz beat from a tiny part right next to it. |
| **Two round cans (capacitors)** | "Tiny water tanks for electricity. They smooth out bumps in the power." | Electrolytic capacitors that filter the supply. |
| **Black part next to the power jack** | "The calmer. It takes a 9 V battery and calms it down to a steady 5 V." | A voltage regulator. |
| **Rows of black sockets with numbers** | "The doors where wires plug in. Each one has a number." | 14 digital pins (0 to 13) and 6 analog inputs (A0 to A5). |
| **Tiny lights: ON, L, TX, RX** | "ON = power. L = the light you blinked in Step 1. TX and RX flash when data travels." | L is wired to pin 13. TX/RX show serial traffic. |
| **Red button** | "Restart. The brain starts its code from the top." | Reset. |

**Try it:** a toggle **"Show the roads"** highlights the thin copper lines printed on the board. A dot runs along one road from the USB port to the brain.

**Say it simply:** "The green board doesn't think. It's a city map. The thin lines are roads made of copper, and electricity drives along them. Only one building in the city does the thinking: the big black chip."

**Try it for real:** find each part on your real board. Count the legs on the big chip (28). Find the silver oval and read the number on it.

### 2b. Follow the power

**Kids see:** the board drawing again, now dark, "asleep".

**Try it:** two buttons: 🔌 **Plug in USB** and 🔋 **Plug in battery**.
- USB: glowing dots flow from the USB port straight to the 5 V lines, into the brain, and out to the pins. The ON light turns green.
- Battery: dots enter at the round jack as "9 V", pass through the **calmer** (regulator) and come out as "5 V", then go everywhere else.
- **Unplug:** everything goes dark again.

**Say it simply:** "A brain without power is asleep. Power comes in through one of two doors, and the calmer makes sure the brain always gets a steady 5 volts, never too much."

### 2c. Pins: the brain's doors

**Kids see:** pin **7** with the LED, and pin **10** with the sensor's echo wire.

**Try it:**
- A big switch for pin 7: **HIGH** or **LOW**. HIGH shows "5 V", dots flow, and the LED lights. LOW shows "0 V" and the LED goes dark. The matching code line updates live: `digitalWrite(7, HIGH);`
- A tap target "echo arrives" on pin 10: the pin flips to HIGH for a moment, and the brain reads it: `pulseIn(ECHO_PIN, HIGH)`.

**Say it simply:** "A pin is a door. For an **output**, the brain opens the door and pushes electricity out: LED on. For an **input**, the brain listens at the door: did something arrive?"

**Deeper:** HIGH means about 5 V and LOW means 0 V. That's how all the robot's 1s and 0s look in real life. A pin can safely give only a small amount of current, about enough for an LED, which is why bigger things like motors need a helper (a driver chip or a transistor).

**Badge:** 🏙️ *City Explorer*, earned after tapping every hotspot and powering up the board.

---

## Level 3: 🧠 Inside the brain chip

### 3a. The rooms inside the chip

**Kids see:** the black chip "opens up" into a cartoon floor plan with four rooms:

| Room | Picture | Simple | Deeper |
|---|---|---|---|
| **Flash memory** | 📘 a book | "The instruction book. Your code lives here, and it stays even with the power off." | 32 KB |
| **RAM** | 🧽 a whiteboard | "Scratch paper. Numbers that change, like the visitor count. It's wiped clean when the power goes off." | 2 KB, about 2,000 letters' worth |
| **The worker** | 👷 a little figure | "Reads the book one line at a time and does exactly what it says." | The CPU |
| **The heartbeat** | 💓 a pulsing dot | "Every tick, the worker takes one tiny step." | 16 million ticks per second (16 MHz) |

**Try it:** the worker walks through the real greeter code in **slow motion**. The current line is highlighted, and when it reaches `visitors++` the number on the whiteboard goes up. A speed slider goes from 🐢 *one line per second* to 🚀 *real speed* (a blur).

### 3b. The unplug test

**Try it:** a big 🔌 **Unplug** button.
- The whiteboard (RAM) is wiped: visitors becomes 0.
- The book (flash) stays exactly the same.
- **Plug back in:** the worker starts again at the top of the book, and the greeter works, with the count starting from 0.

**Say it simply:** "The code is safe in the book, but the scratch paper forgets. That's why the visitor count goes back to 0."

**Try it for real (the best moment on this page):** unplug the real greeter, plug it back in, and check the visitor count on the real screen. It's back to 0. Then press the red reset button with a few visitors counted. What happens?

**Deeper challenge:** the chip also has a tiny third memory called EEPROM (1 KB) that survives unplugging. Could you save the visitor count there so it never forgets?

### 3c. How code gets into the chip (uploading)

**Kids see:** the MacBook on the left, the USB cable, the translator chip, and the brain's book on the right.

**Try it:** press **Upload**.
1. A line of code on the Mac breaks into **0s and 1s**, shown as glowing dots.
2. The dots travel down the cable to the **translator** chip.
3. The **TX/RX lights blink** while the dots stream across.
4. The brain restarts, and a tiny "doorman" program that's always in the chip catches the dots and writes them into the book.
5. "Done uploading". The worker starts reading the new book.

**Say it simply:** "Uploading is writing a new instruction book into the chip. After that, the computer isn't needed anymore. The robot runs on its own, even on a battery."

**Deeper:** the doorman is called the **bootloader**. Opening a USB connection restarts the UNO so the bootloader can listen for new code. That's also why the board restarts when the Python programs in Chapter 3 connect to it.

**Try it for real:** upload any sketch and watch the real TX and RX lights flicker.

**Badge:** 🧠 *Brain Surgeon*, earned by passing the unplug test and finishing an upload.

---

## Level 4: 🏖️ Sand that thinks

### 4a. Three kinds of stuff

**Kids see:** a little circuit: battery, a gap, and a light bulb. Three materials to drag into the gap:

| Material | What happens |
|---|---|
| 🟧 **Copper** (a conductor) | Light always on. "Electricity flows freely." |
| ⚫ **Rubber** (an insulator) | Light always off. "Electricity is blocked." |
| 💎 **Silicon** (a semiconductor) | Light is off, **until you press a control button**. Then it's on. "We decide when it flows!" |

**Say it simply:** "Copper always lets electricity through. Rubber never does. Silicon is special: it lets electricity through **only when we tell it to**. That's what 'semiconductor' means."

**Deeper:** pure silicon is made from sand (sand is mostly silicon and oxygen). Adding a tiny pinch of other atoms, like phosphorus or boron, is called **doping**. It's what makes silicon controllable.

### 4b. The transistor: a switch that electricity controls

**Kids see:** a big cartoon transistor drawn like a water pipe with a tap on top.

**Try it:** press and hold the **tap** (the gate).
- Held: water/electricity dots flow through the pipe, a lamp lights, and a big **1** appears.
- Released: the flow stops, the lamp goes off, and a **0** appears.

**Say it simply:** "A transistor is a switch with no fingers. Instead of you flipping it, a little bit of electricity flips it. On = 1, off = 0. That's the whole language of computers."

**Deeper:** the three parts are called **source**, **drain** and **gate**. Voltage on the gate opens a path between source and drain.

### 4c. Switches make decisions

**Kids see:** two transistor switches wired to one lamp labeled **"Say hello!"** and two toggles:

- Switch A: **Someone is close** (`cm < 60`)
- Switch B: **Not greeted yet** (`!someoneHere`)

**Try it:**
- **AND mode** (switches in a row): the lamp lights only when **both** are on. The code line lights up: `if (cm < 60 && !someoneHere)`. Point at `&&` and show "AND".
- **OR mode** (switches side by side): the lamp lights when **either** is on.
- **NOT:** a third control that flips a signal: ON becomes OFF. Point at `!` and show "NOT".

**Say it simply:** "Put switches in a row and you get AND. Put them side by side and you get OR. The `&&` in YOUR greeter code is exactly this. Billions of these tiny decisions, stacked together, make a brain."

**Try it for real:** open the greeter code and find every `&&` and `!`. Each one is a little AND or NOT gate.

**Badge:** 🏖️ *Sand Wizard*, earned by lighting the lamp in AND mode and in OR mode.

---

## Level 5: 🔭 Small chips, giant chips

### 5a. How many switches?

**Kids see:** a zoom-out journey (a slider or "Zoom out" button, on a log scale) from one switch to hundreds of billions:

| Stop | Switches (transistors) |
|---|---|
| 💡 A light switch in your room | 1 |
| 🕰️ The first computer-on-a-chip (Intel 4004, 1971) | 2,300 |
| 💻 Apple M4 chip (in recent Macs and iPads) | 28 billion |
| 🏭 Nvidia Rubin AI chip (2026) | 336 billion |

Each stop shows a dot grid that gets denser, then turns into a "fog" too dense to see. Fun fact card: "Modern transistors are so small that more than a thousand fit side by side across one human hair."

**Say it simply:** "Same idea as the 4004, the M4 and the giant AI chips: tiny switches made of silicon. The difference is how many, and how fast."

### 5b. Who holds the plan?

**Kids see:** three cards with a 📘 book (the plan) and a 💪 muscle icon:

| Chip | Holds its own plan? | What it's best at |
|---|---|---|
| **UNO / Nano / ESP32** (microcontrollers) | 📘 Yes. The code lives inside | Running one job forever on a little battery |
| **MacBook chip** | 📘 Yes, and runs many programs at once | Everything: apps, video, AI |
| **Big AI chip** (like Nvidia's) | 💪 No. A computer next to it feeds it work | Doing trillions of AI math steps |

**Try it:** drag the 📘 plan onto each chip and see what it says. On the AI chip, a little "boss computer" appears and keeps passing it work.

**Say it simply:** "Your Arduino is a brain **and** hands in one. A giant AI chip is pure muscle. It needs a boss computer to tell it what to crunch. In Chapter 3 you build the same team: the MacBook is the AI brain, and the Arduino is the hands."

### 5c. From workbench to product

**Kids see:** three boards side by side, drawn to scale: **UNO**, **Nano**, **ESP32**.

| Board | Card |
|---|---|
| **UNO** | "The workbench. Easy to plug wires into. Perfect for trying ideas." |
| **Nano** | "Same brain as the UNO (same chip!), shrunk to the size of a stick of gum. Same code runs as-is." |
| **ESP32** | "A different, faster brain with Wi-Fi and Bluetooth built in. Code needs small changes." |

**Try it:** drag the greeter's 📘 code onto each board. UNO and Nano: ✅ "Runs!" ESP32: 🔧 "Runs with small changes, and now it can talk to your phone!"

**Deeper:** UNO and Nano both use the ATmega328P at 16 MHz with 2 KB of RAM. The ESP32 runs at up to 240 MHz with 520 KB of RAM, so it's much faster with much more scratch paper.

**Badge:** 🔭 *Chip Scout*, earned by zooming all the way out and moving the code to all three boards.

---

## 🏆 Boss level: Explain it back

The best way to know you understand something is to teach it.

### Quick quiz

Tap the answer. Give a short "why" after each one, with friendly, never mocking wrong-answer messages.

1. **Where does your code live when the Arduino is unplugged?**
   ✅ In the flash memory inside the chip · ❌ In the USB cable · ❌ On the MacBook only
2. **Why does the visitor count go back to 0 when you unplug?**
   ✅ RAM forgets without power · ❌ The code gets deleted · ❌ The sensor resets it
3. **What does the silver oval marked 16.000 do?**
   ✅ It's a clock that ticks 16 million times a second · ❌ It stores the code · ❌ It's the battery
4. **A transistor is...**
   ✅ A switch that electricity flips · ❌ A tiny battery · ❌ A kind of wire
5. **In `if (cm < 60 && !someoneHere)`, what does `&&` mean?**
   ✅ AND: both must be true · ❌ OR: either one · ❌ Add the numbers
6. **Why can't the UNO find faces by itself in Chapter 3?**
   ✅ It's too small and slow for AI, so the MacBook does the seeing and sends a letter · ❌ It has no camera port · ❌ Faces are against the rules
7. **Same brain as the UNO, size of a stick of gum?**
   ✅ Nano · ❌ ESP32 · ❌ M4

### Teach-back card

A big card for each kid with three words: **INPUT · BRAIN · OUTPUT**. "Explain how the Door Greeter works to a parent using only these three words plus your hands. Then explain what a transistor is without saying 'transistor'."

**Final badge:** 🎓 *Robot Professor*, then confetti, and the whole mission map lights up.

---

## Facts to keep right

Use these exact facts. Don't add numbers that aren't here.

| Fact | Value |
|---|---|
| UNO main chip | ATmega328P |
| UNO operating voltage | 5 V |
| UNO recommended input on the round jack | 7 to 12 V (the kit's 9 V battery fits) |
| UNO clock | 16 MHz (16 million ticks per second) |
| UNO memory | Flash 32 KB, RAM (SRAM) 2 KB, EEPROM 1 KB |
| UNO pins | 14 digital (0 to 13), 6 analog inputs (A0 to A5) |
| UNO USB helper chip | ATmega16U2 (on the official UNO R3) |
| Max current per pin | 40 mA absolute maximum. Treat about 20 mA as the safe everyday limit |
| Big chip legs | 28 (the through-hole ATmega328P on this kit's board) |
| ESP32 | Up to 240 MHz, 520 KB RAM, Wi-Fi and Bluetooth built in |
| Intel 4004 (1971) | 2,300 transistors |
| Apple M4 | 28 billion transistors |
| Nvidia Rubin GPU (2026) | 336 billion transistors (two dies in one package) |
| Silicon | Made from sand (silicon dioxide), purified, then "doped" with tiny amounts of other atoms |
| HIGH / LOW on the UNO | About 5 V / 0 V |
| Greeter code facts | `loop()` repeats forever. With `delay(100)` it runs about 10 times a second. `visitors` lives in RAM and starts at 0 on every power-up |

Not stated anywhere official, so don't give a number: how many transistors are in the ATmega328P or the ESP32.

### Sources for the facts

- [Arduino UNO R3 technical specs](https://docs.arduino.cc/hardware/uno-rev3/)
- [ESP32-WROOM-32 datasheet (Espressif)](https://documentation.espressif.com/esp32-wroom-32_datasheet_en.html)
- [Intel 4004](https://en.wikipedia.org/wiki/Intel_4004)
- [Apple introduces M4 chip (Apple Newsroom)](https://www.apple.com/newsroom/2024/05/apple-introduces-m4-chip/)
- [Nvidia launches Rubin at CES 2026 (ServeTheHome)](https://www.servethehome.com/nvidia-launches-next-generation-rubin-ai-compute-platform-at-ces-2026/)
