<!--
Notes for turning this chapter into a page (for example with Claude Code):
- Match the look and features of door-greeter-build-guide.html: same colors, hero, mission map,
  step cards, badges, copy buttons on code, and checkmarks remembered in the browser.
- Each "## Step N" is one step card. "🎯 Kid challenge", "💡 Parent tip" and "⚠️" lines use the
  existing callout styles. <details> blocks are hidden answers: keep them collapsed.
- Nice interactive idea for "How the remote works": a clickable drawing of the remote that shows
  each button's number.
- The same code also lives in chapter-2-code/ as ready-to-open Arduino sketches.
-->

# 📡 Chapter 2: Guard Mode

The Door Greeter from Chapter 1 gets a remote control. From across the room you can switch the guard on and off, pick a mode (friendly greeter, loud alarm, or silent ninja), and change how far it looks. Before that, the remote turns the Arduino into a piano.

This is project #2 in the series. It builds on Chapter 1, so keep that build wired up.

## Who it's for

| | |
|---|---|
| **Builders** | Two kids, ages 13 (7th grade) and 10 (5th grade) |
| **Helper** | A parent, mostly asking "what do you think will happen?" |
| **Time** | About 1½ to 2 hours |
| **Before this** | Chapter 1 (Door Greeter Bot) finished and still wired |

Same two jobs as before, swap every step:

- 🔧 **Builder** plugs in the wires and tests the gadget.
- ⌨️ **Coder** reads the step out loud, uploads the code, and makes the code changes.

## The big idea: two inputs working together

In Chapter 1 the robot had **one input**: the ultrasonic sensor. Now it gets a **second input**: the remote. The code decides how they work together. The sensor sees someone, but the remote decides whether the robot cares.

That's a big robotics idea: **anything that can send a signal to a pin is an input.** A sensor, a button, a remote, even an AI (that's Chapter 3).

## How the remote works

The remote has a tiny light at its tip that blinks **infrared** light, a color human eyes can't see. Each button blinks a different pattern, like Morse code. The IR receiver (the little dark bulb) catches the blinks and turns the pattern into a **number**. Your code then decides what each number means.

🎯 **Kid challenge: see the invisible light.** Point the remote at a phone camera (try the selfie camera) and press a button. Many phone cameras can see infrared, so you'll spot the tip flashing on the screen.

⚠️ **Use the right remote.** Use the flat black remote from the ELEGOO Super Starter Kit. The purple 4-button remote from the RC car kit only talks to its own receiver board and won't work here.

## What you need

Everything comes from the **ELEGOO Super Starter Kit for UNO**:

- The finished Chapter 1 build (UNO, breadboard, sensor, LCD, buzzer, LED)
- IR receiver module (small board with a dark bulb and 3 pins)
- IR remote (pull out the clear plastic tab by the battery first!)
- 3 jumper wires

## The 5 steps

| Step | Name | What you do | Time | The win |
|---|---|---|---|---|
| 1 | 📚 Get the remote library | Install IRremote | 5 min | The library says INSTALLED |
| 2 | 🕵️ Button Spy | Wire the receiver | 20 min | Every button shows its secret number |
| 3 | 🎹 Remote Piano | Code only | 20 min | Play a song from across the room |
| 4 | 🛡️ Guard Mode | Code only | 30 min | Switch the guard on, off, and between modes |
| 5 | 🎨 Make it yours | Code only | 20 min | Your own modes, plus a secret code (boss challenge) |

## Step 1: 📚 Get the remote library

A **library** is code someone else wrote that you can borrow. This one knows how to read remote signals.

1. In the Arduino IDE, open the **Library Manager**: click the books icon on the left (or **Sketch → Include Library → Manage Libraries…**).
2. Search for **IRremote**.
3. Find **IRremote by shirriff, z3t0, ArminJo** and click **Install**. Use version 4 or newer.

⚠️ **Don't use the IRremote.zip from ELEGOO's download folder.** It's a much older version that uses different commands, and this guide's code won't work with it.

## Step 2: 🕵️ Button Spy

### Wire the IR receiver

Unplug USB first. Leave everything from Chapter 1 where it is and add the receiver. Push its 3 pins into three empty rows on the breadboard, with the dark bulb facing out.

| IR receiver pin | Connect to |
|---|---|
| **Y** (signal, sometimes marked **S**) | UNO pin **6** |
| **R** (power, sometimes marked **+**) | **+** rail |
| **G** (ground, sometimes marked **−**) | **−** rail |

### Upload Button Spy

```cpp
// Chapter 2, Step 2: Button Spy
// Press any button on the remote and see its secret number.
#include <IRremote.hpp>

const int IR_PIN = 6;

void setup() {
  Serial.begin(9600);
  IrReceiver.begin(IR_PIN, ENABLE_LED_FEEDBACK);   // the L light blinks when a signal arrives
  Serial.println("Button Spy ready. Point the remote and press a button!");
}

void loop() {
  if (IrReceiver.decode()) {                        // did a signal arrive?
    bool isRepeat = IrReceiver.decodedIRData.flags & IRDATA_FLAGS_IS_REPEAT;
    if (!isRepeat) {                                // ignore "still holding it" signals
      Serial.print("Button number: ");
      Serial.println(IrReceiver.decodedIRData.command);
    }
    IrReceiver.resume();                            // get ready for the next one
  }
}
```

Open the **Serial Monitor** at **9600 baud**. Point the remote at the receiver and press buttons. Each press prints a number, and the tiny **L** light near pin 13 blinks whenever a signal arrives.

On the ELEGOO remote you should see these numbers (laid out like the remote):

| | | |
|---|---|---|
| POWER **69** | VOL+ **70** | FUNC/STOP **71** |
| ⏮ **68** | ⏯ **64** | ⏭ **67** |
| ▼ **7** | VOL− **21** | ▲ **9** |
| 0 **22** | EQ **25** | ST/REPT **13** |
| 1 **12** | 2 **24** | 3 **94** |
| 4 **8** | 5 **28** | 6 **90** |
| 7 **66** | 8 **82** | 9 **74** |

🎯 **Kid challenge: crack the code.** Cover up the table. Press every button and write down its number yourself. Which button has the biggest number? Do the numbers follow any pattern? (Spoiler: they don't. They're just names the remote's maker picked.)

💡 **Parent tip:** if your numbers are different from the table, that's fine. Your remote is a different model. Write your numbers down and use them in the `BTN_` lines in Steps 3 and 4.

## Step 3: 🎹 Remote Piano

No new wires. Buttons **1 to 9** play notes, **0** plays a low note, and **POWER** turns the LED on and off.

```cpp
// Chapter 2, Step 3: Remote Piano
// Buttons 0 to 9 play notes. POWER turns the LED on and off.
#include <IRremote.hpp>

const int IR_PIN     = 6;
const int BUZZER_PIN = 8;
const int LED_PIN    = 7;

// Button numbers from Button Spy (ELEGOO remote)
const int BTN_POWER = 69;
const int BTN_0 = 22;
const int BTN_1 = 12;
const int BTN_2 = 24;
const int BTN_3 = 94;
const int BTN_4 = 8;
const int BTN_5 = 28;
const int BTN_6 = 90;
const int BTN_7 = 66;
const int BTN_8 = 82;
const int BTN_9 = 74;

bool lightOn = false;

void setup() {
  pinMode(BUZZER_PIN, OUTPUT);
  pinMode(LED_PIN, OUTPUT);
  Serial.begin(9600);
  IrReceiver.begin(IR_PIN, ENABLE_LED_FEEDBACK);
}

void loop() {
  if (IrReceiver.decode()) {
    bool isRepeat = IrReceiver.decodedIRData.flags & IRDATA_FLAGS_IS_REPEAT;
    int button = IrReceiver.decodedIRData.command;
    IrReceiver.resume();
    if (isRepeat) return;                  // ignore "still holding it" signals

    if (button == BTN_POWER) {
      lightOn = !lightOn;                  // flip: on becomes off, off becomes on
      digitalWrite(LED_PIN, lightOn);
    }
    else if (button == BTN_1) beep(523);   // C
    else if (button == BTN_2) beep(587);   // D
    else if (button == BTN_3) beep(659);   // E
    else if (button == BTN_4) beep(698);   // F
    else if (button == BTN_5) beep(784);   // G
    else if (button == BTN_6) beep(880);   // A
    else if (button == BTN_7) beep(988);   // B
    else if (button == BTN_8) beep(1047);  // high C
    else if (button == BTN_9) beep(1175);  // high D
    else if (button == BTN_0) beep(262);   // low C
  }
}

// The remote listener and the buzzer share one of the board's timers,
// so they take turns: pause the listener, beep, then start it again.
void beep(int pitch) {
  IrReceiver.stopTimer();
  tone(BUZZER_PIN, pitch, 250);
  delay(250);
  noTone(BUZZER_PIN);
  IrReceiver.restartTimer();
}
```

### Why do they take turns?

The UNO has a few built-in stopwatches called **timers**. The remote listener and the buzzer both need the **same** timer. If they both grab it, the remote stops working after the first beep. So the `beep()` helper makes them take turns: pause the listener, beep, start the listener again.

🎯 **Kid challenge: play a song from across the room.**

- *Twinkle Twinkle Little Star:* **1 1 5 5 6 6 5**
- *Mary Had a Little Lamb:* **3 2 1 2 3 3 3**

Then make up your own song and teach it to your brother.

🎯 **Kid challenge: the bounce test.** Aim the remote at the ceiling or a wall instead of the receiver. Does it still work? Infrared light bounces, just like a ball.

## Step 4: 🛡️ Guard Mode

Now the Door Greeter and the remote work together.

| Button | What it does |
|---|---|
| **POWER** | Guard on or off. High beep = on, low beep = off |
| **1** | 👋 Greeter mode: tune and a random greeting |
| **2** | 🚨 Alarm mode: siren and "!! INTRUDER !!" |
| **3** | 🥷 Ninja mode: silent, just counts visitors |
| **VOL+ / VOL−** | Look 10 cm farther / closer (20 to 200 cm) |
| **0** | Reset the visitor count |

```cpp
// Chapter 2: Guard Mode
// The Door Greeter from Chapter 1, now with a remote control.
//   POWER     = guard on / off
//   1, 2, 3   = Greeter, Alarm, or Ninja mode
//   VOL+ VOL- = see farther / closer
//   0         = reset the visitor count
#include <IRremote.hpp>
#include <LiquidCrystal.h>

LiquidCrystal lcd(12, 11, 5, 4, 3, 2);   // RS, E, D4, D5, D6, D7

const int TRIG_PIN   = 9;
const int ECHO_PIN   = 10;
const int BUZZER_PIN = 8;
const int LED_PIN    = 7;
const int IR_PIN     = 6;

// Remote button numbers (from Button Spy)
const int BTN_POWER    = 69;
const int BTN_VOL_UP   = 70;
const int BTN_VOL_DOWN = 21;
const int BTN_0 = 22;
const int BTN_1 = 12;
const int BTN_2 = 24;
const int BTN_3 = 94;

// The three modes
const int GREETER = 1;
const int ALARM   = 2;
const int NINJA   = 3;

bool armed = true;
int mode = GREETER;
int triggerCm = 60;          // how close before it reacts
int visitors = 0;
bool someoneHere = false;

// Change these! Max 16 characters each.
const char* greetings[] = {
  "Hello, human!",
  "Welcome back!",
  "Halt! Password?",
  "Robot says hi!",
  "Nice socks."
};
const int NUM_GREETINGS = sizeof(greetings) / sizeof(greetings[0]);

void setup() {
  pinMode(TRIG_PIN, OUTPUT);
  pinMode(ECHO_PIN, INPUT);
  pinMode(BUZZER_PIN, OUTPUT);
  pinMode(LED_PIN, OUTPUT);
  Serial.begin(9600);
  lcd.begin(16, 2);
  IrReceiver.begin(IR_PIN, ENABLE_LED_FEEDBACK);
  randomSeed(analogRead(A0));
  showStatus();
}

void loop() {
  checkRemote();

  if (armed) {
    long cm = readDistanceCm();

    // Someone walked up: react once
    if (cm < triggerCm && !someoneHere) {
      someoneHere = true;
      visitors++;
      react();
    }

    // They walked away: get ready for the next visitor
    if (cm > triggerCm + 20 && someoneHere) {
      someoneHere = false;
      digitalWrite(LED_PIN, LOW);
      showStatus();
    }
  }

  delay(50);
}

// ---------- The remote ----------
void checkRemote() {
  if (!IrReceiver.decode()) return;           // nothing pressed
  bool isRepeat = IrReceiver.decodedIRData.flags & IRDATA_FLAGS_IS_REPEAT;
  int button = IrReceiver.decodedIRData.command;
  IrReceiver.resume();
  if (isRepeat) return;                       // ignore "still holding it" signals

  Serial.print("Button: ");
  Serial.println(button);

  if (button == BTN_POWER) {
    armed = !armed;
    someoneHere = false;
    digitalWrite(LED_PIN, LOW);
    beep(armed ? 1047 : 262, 150);            // high beep = on, low beep = off
  }
  else if (button == BTN_1) { mode = GREETER; beep(523, 100); }
  else if (button == BTN_2) { mode = ALARM;   beep(523, 100); }
  else if (button == BTN_3) { mode = NINJA;   beep(523, 100); }
  else if (button == BTN_VOL_UP && triggerCm < 200)  { triggerCm += 10; beep(880, 60); }
  else if (button == BTN_VOL_DOWN && triggerCm > 20) { triggerCm -= 10; beep(440, 60); }
  else if (button == BTN_0) { visitors = 0; beep(659, 100); }
  else return;                                // any other button: change nothing

  showStatus();
}

// ---------- What happens when someone comes ----------
void react() {
  digitalWrite(LED_PIN, HIGH);
  lcd.clear();

  if (mode == GREETER) {
    lcd.print(greetings[random(NUM_GREETINGS)]);
  } else if (mode == ALARM) {
    lcd.print("!! INTRUDER !!");
  } else {
    lcd.print("...");                         // ninja: silent, just counts
  }
  lcd.setCursor(0, 1);                        // second line
  lcd.print("Visitor #");
  lcd.print(visitors);

  if (mode == GREETER) playHello();
  if (mode == ALARM)   playSiren();
}

void showStatus() {
  lcd.clear();
  if (!armed) {
    lcd.print("Guard: OFF  zzz");
    lcd.setCursor(0, 1);
    lcd.print("Visitors: ");
    lcd.print(visitors);
    return;
  }
  if (mode == GREETER) lcd.print("Mode: GREETER");
  if (mode == ALARM)   lcd.print("Mode: ALARM");
  if (mode == NINJA)   lcd.print("Mode: NINJA");
  lcd.setCursor(0, 1);
  lcd.print("Range:");
  lcd.print(triggerCm);
  lcd.print("cm V:");
  lcd.print(visitors);
}

// ---------- Sounds ----------
// The remote listener and the buzzer share one of the board's timers,
// so they take turns: pause the listener, make the sound, start it again.
void beep(int pitch, int ms) {
  IrReceiver.stopTimer();
  tone(BUZZER_PIN, pitch, ms);
  delay(ms);
  noTone(BUZZER_PIN);
  IrReceiver.restartTimer();
}

void playHello() {
  int notes[] = {523, 659, 784, 1047};       // C, E, G, high C
  IrReceiver.stopTimer();
  for (int i = 0; i < 4; i++) {
    tone(BUZZER_PIN, notes[i], 150);
    delay(180);
  }
  noTone(BUZZER_PIN);
  IrReceiver.restartTimer();
}

void playSiren() {
  IrReceiver.stopTimer();
  for (int i = 0; i < 3; i++) {
    for (int pitch = 600; pitch <= 1400; pitch += 20) { tone(BUZZER_PIN, pitch); delay(5); }
    for (int pitch = 1400; pitch >= 600; pitch -= 20) { tone(BUZZER_PIN, pitch); delay(5); }
  }
  noTone(BUZZER_PIN);
  IrReceiver.restartTimer();
}

// ---------- The eyes ----------
long readDistanceCm() {
  digitalWrite(TRIG_PIN, LOW);
  delayMicroseconds(2);
  digitalWrite(TRIG_PIN, HIGH);    // shout!
  delayMicroseconds(10);
  digitalWrite(TRIG_PIN, LOW);

  // pulseInLong (not pulseIn) keeps good time while the remote listener runs in the background
  long echoTime = pulseInLong(ECHO_PIN, HIGH, 30000);
  if (echoTime == 0) return 999;   // no echo = nothing nearby
  return echoTime / 58;            // 58 microseconds per cm, there and back
}
```

The screen shows the mode on the top line. The bottom line shows the range and the visitor count, like `Range:60cm V:3`.

### Test it like a pro

Testers check every feature one at a time and tick it off. Take turns: one person presses, the other walks up to the sensor.

| ✅ | Test | What should happen |
|---|---|---|
| ☐ | Walk up in Greeter mode | Tune, LED, random greeting, visitor number goes up |
| ☐ | Press **2**, walk up | Siren and "!! INTRUDER !!" |
| ☐ | Press **3**, walk up | No sound, but the visitor count still goes up |
| ☐ | Press **POWER** | Low beep, screen says `Guard: OFF  zzz` |
| ☐ | Walk up while the guard is off | Nothing happens |
| ☐ | Press **POWER** again | High beep, guard is back on |
| ☐ | Press **VOL−** three times | Range goes from 60 to 30 cm. Now you have to get closer |
| ☐ | Press **0** | Visitor count goes back to 0 |

💡 **Parent tip:** when a test fails, don't fix it for them. Ask "which line of code do you think handles that button?" Finding the line is the real skill.

## Step 5: 🎨 Make it yours

Upload after each change.

1. **Rename the modes.** Change `"Mode: NINJA"` to `"Mode: SPY"` or anything up to 16 characters.
2. **New greetings.** Edit the `greetings` list, same as Chapter 1.
3. **Scarier siren.** In `playSiren()`, change `i < 3` to `i < 6` for a longer siren, or `delay(5)` to `delay(2)` for a faster one.
4. **A fourth mode.** Copy how mode 3 works and add a 🪩 **Disco** mode on the **EQ** button that blinks the LED 10 times. (EQ's number is **25**. Buttons 4 to 9 are saved for the boss challenge.)

### 🏆 Boss challenge: the secret code

Right now anyone with the remote can turn the guard off. Make it so turning it **on** is easy, but turning it **off** needs a secret code: **7, then 4, then 9**. A wrong number makes an angry buzz and starts over.

Hint: you need a list that holds the code, and a counter that remembers how many numbers were right so far.

<details>
<summary>Show the answer</summary>

**1.** Add these lines near the top, right under `const int BTN_3 = 94;`:

```cpp
// Boss challenge: the secret code
const int BTN_4 = 8;
const int BTN_5 = 28;
const int BTN_6 = 90;
const int BTN_7 = 66;
const int BTN_8 = 82;
const int BTN_9 = 74;
int secretCode[] = {BTN_7, BTN_4, BTN_9};   // press 7, then 4, then 9
int codeStep = 0;                           // how many right so far
```

**2.** Replace the whole `checkRemote()` function with this one, and add `isCodeButton()` after it:

```cpp
void checkRemote() {
  if (!IrReceiver.decode()) return;
  bool isRepeat = IrReceiver.decodedIRData.flags & IRDATA_FLAGS_IS_REPEAT;
  int button = IrReceiver.decodedIRData.command;
  IrReceiver.resume();
  if (isRepeat) return;

  if (button == BTN_POWER) {
    if (!armed) {
      armed = true;                     // turning ON needs no code
      beep(1047, 150);
    } else {
      codeStep = 0;
      lcd.clear();
      lcd.print("Enter the code!");     // turning OFF does
      beep(200, 300);
      return;
    }
  }
  else if (armed && isCodeButton(button)) {
    if (button == secretCode[codeStep]) {
      codeStep++;
      beep(784, 60);
      if (codeStep < 3) return;         // keep going...
      armed = false;                    // all 3 right!
      codeStep = 0;
      someoneHere = false;
      digitalWrite(LED_PIN, LOW);
      beep(262, 150);
    } else {
      codeStep = 0;                     // wrong! start over
      beep(150, 400);
      return;
    }
  }
  else if (button == BTN_1) { mode = GREETER; beep(523, 100); }
  else if (button == BTN_2) { mode = ALARM;   beep(523, 100); }
  else if (button == BTN_3) { mode = NINJA;   beep(523, 100); }
  else if (button == BTN_VOL_UP && triggerCm < 200)  { triggerCm += 10; beep(880, 60); }
  else if (button == BTN_VOL_DOWN && triggerCm > 20) { triggerCm -= 10; beep(440, 60); }
  else if (button == BTN_0) { visitors = 0; beep(659, 100); }
  else return;

  showStatus();
}

bool isCodeButton(int button) {
  return button == BTN_4 || button == BTN_5 || button == BTN_6 ||
         button == BTN_7 || button == BTN_8 || button == BTN_9;
}
```

Now **POWER** shows "Enter the code!". Press **7, 4, 9** to turn the guard off.

</details>

## Mount it at the door

Same as Chapter 1, with one extra hole: the receiver's dark bulb has to **see** the remote. Poke it out through the box next to the sensor's eyes.

## Pin map

Chapter 1's wiring, plus one new pin.

| UNO pin | Goes to |
|---|---|
| **5V** | Breadboard **+** rail (red wire) |
| **GND** | Breadboard **−** rail (black wire) |
| **9** | Sensor **Trig** |
| **10** | Sensor **Echo** |
| **8** | Passive buzzer **+** leg |
| **7** | 220 Ω resistor → LED long leg |
| **6** | IR receiver **Y** (signal) ⭐ new |
| **12, 11, 5, 4, 3, 2** | LCD (same as Chapter 1) |

IR receiver **R** → **+** rail, **G** → **−** rail. The built-in **L** light (pin 13) blinks when a remote signal arrives.

## Troubleshooting

**"IRremote.hpp: No such file or directory"**
The library isn't installed. Do Step 1.

**Lots of errors mentioning IRremote, or "Multiple libraries were found"**
An old IRremote is in the way (maybe ELEGOO's zip). In Finder, open **Documents → Arduino → libraries**, move any old IRremote folder to the Trash, then reinstall it from the Library Manager.

**Nothing shows up when you press buttons**
Did you pull the plastic tab out of the remote? Is **Y** going to pin **6**? Is the Serial Monitor set to **9600**? Does the **L** light blink when you press? If it doesn't, check the receiver's 3 wires.

**Your numbers don't match the table**
Your remote is a different model. Use your own numbers in the `BTN_` lines.

**The remote works once, then stops after the first beep**
Something is calling `tone()` without pausing the listener. Always make sounds through `beep()`, `playHello()`, or `playSiren()`, which take turns properly.

**The guard keeps reacting to the wall**
Press **VOL−** to shrink the range until it's shorter than the distance to the wall.

**Distance numbers jump around a lot**
Make sure `readDistanceCm()` uses `pulseInLong`, not `pulseIn`. The plain version gets confused while the remote listener runs in the background.

## What's in this chapter

```
Door Greeter Bot/
├── chapter-2-remote-control.md   ← you are here
└── chapter-2-code/               ← the same sketches, ready to open in the Arduino IDE
    ├── button_spy/button_spy.ino
    ├── remote_piano/remote_piano.ino
    └── guard_mode/guard_mode.ino
```

ELEGOO's lesson for this part is **2.12 IR Receiver**, in `available-parts/ELEGOO-Super-Starter-Kit-for-UNO/English/Part 2/`. It uses different pins and an older way of reading the remote, so follow this guide.

Tested with: Arduino UNO R3, IRremote library 4.7.1, LiquidCrystal 1.0.7. All three sketches compile for the UNO.

## Next chapter

**Chapter 3: Robot Eyes.** The MacBook's camera and an AI become a third input. The robot greets faces, counts fingers, and plays Rock Paper Scissors against you.
