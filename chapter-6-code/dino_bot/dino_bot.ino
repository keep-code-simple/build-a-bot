// Chapter 6: Dino Bot
// A robot that plays the Chrome dinosaur game like a person:
// it watches the screen with light-sensor eyes and presses the space bar
// with a servo finger.
//
// This sketch has TWO tabs: this one, and dino_logic.h (the brain).
// Both must be in the same sketch folder.
#include <LiquidCrystal.h>
#include <Servo.h>
#include "dino_logic.h"

// ====================== SETTINGS: change these! ======================

// Which brain? Change this ONE number and upload again to upgrade the robot.
//   1 = jump when it's dark            (Step 4)
//   2 = night vision                   (Step 5)
//   3 = speed trap, needs eye A1       (Step 6)
//   4 = birds, needs eye A2 + a duck finger (Step 7)
#define LEVEL 1

// The jump finger. Copy these two numbers from servo_calibrate (Step 2).
const int REST_ANGLE  = 90;       // finger just above the space bar
const int PRESS_ANGLE = 70;       // space bar pressed (not crushed!)

// The duck finger, over the down-arrow key (Level 4 only).
const int DUCK_REST_ANGLE  = 90;
const int DUCK_PRESS_ANGLE = 70;

const int PRESS_MS = 80;          // how long the finger holds the key. Longer = higher jump

// Level 1: light BELOW this number means "cactus!".
// Use the number halfway between "white screen" and "cactus" on your plotter.
const int THRESHOLD = 500;

// Level 2 and up: how far from normal the light must move to count as "something".
// About half the depth of a cactus dip on your plotter.
const int BIG_CHANGE = 100;

const int COOLDOWN_MS = 300;      // after a jump, ignore the eye this long (one cactus = one jump)

// Level 3 and up: the speed trap. Measure these on your screen with a ruler.
const int SENSOR_GAP_MM  = 40;    // millimeters from eye A1 to eye A0
const int EYE_TO_DINO_MM = 30;    // millimeters from eye A0 to the dino's nose
const int ROBOT_DELAY_MS = 100;   // your robot's own delay (the Step 6 challenge measures it)
const int HEAD_START_MS  = 150;   // start jumping this long before the cactus arrives. Tune it!

const bool BEEP_ON_JUMP = true;   // a tiny beep on every jump. false = quiet
const bool DEBUG_TIMES  = false;  // true = print "SAW" and "PRESS" times to the Serial Monitor

const int MAX_RUN_MINUTES = 30;   // safety stop: the fingers rest after this many minutes

// ====================== PINS ======================
LiquidCrystal lcd(12, 11, 5, 4, 3, 2);   // RS, E, D4, D5, D6, D7 (same as Chapter 1)
const int BUZZER_PIN     = 8;            // same as Chapter 1
const int JUMP_SERVO_PIN = 9;
const int DUCK_SERVO_PIN = 10;
const int SAW_LED_PIN    = 13;           // the UNO's own little light: ON while the low eye sees something
const int LOW_EYE_PIN    = A0;           // cactus height, near the dino
const int FAR_EYE_PIN    = A1;           // cactus height, farther ahead (Level 3)
const int HEAD_EYE_PIN   = A2;           // head height, above A1 (Level 4)

// ====================== THE ROBOT ======================
const unsigned long BRAIN_MS = 2;        // the brain thinks 500 times a second
const unsigned long LCD_MS   = 200;      // the screen updates 5 times a second, so it never slows the loop

Servo jumpFinger;
#if LEVEL >= 4
Servo duckFinger;
#endif

DinoBrain brain;
DinoSettings settings;

unsigned long lastBrainAt = 0;
unsigned long lastLcdAt = 0;
bool jumpWasDown = false;
bool duckWasDown = false;
bool sawWas = false;
bool napShown = false;
bool lcdTurn = false;
int lightNow = 0;

void setup() {
  settings.level = LEVEL;
  settings.threshold = THRESHOLD;
  settings.bigChange = BIG_CHANGE;
  settings.pressMs = PRESS_MS;
  settings.cooldownMs = COOLDOWN_MS;
  settings.sensorGapMm = SENSOR_GAP_MM;
  settings.eyeToDinoMm = EYE_TO_DINO_MM;
  settings.headStartMs = HEAD_START_MS;
  settings.robotDelayMs = ROBOT_DELAY_MS;
  settings.maxRunMs = (int32_t)MAX_RUN_MINUTES * 60000L;
  dinoBrainReset(brain);

  pinMode(BUZZER_PIN, OUTPUT);
  pinMode(SAW_LED_PIN, OUTPUT);

  jumpFinger.write(REST_ANGLE);          // set the angle first, so the finger doesn't twitch
  jumpFinger.attach(JUMP_SERVO_PIN);
#if LEVEL >= 4
  duckFinger.write(DUCK_REST_ANGLE);
  duckFinger.attach(DUCK_SERVO_PIN);
#endif

  Serial.begin(115200);
  lcd.begin(16, 2);
  lcd.print("Dino Bot Level ");
  lcd.print(LEVEL);
  lcd.setCursor(0, 1);
  lcd.print("Jumps:0   L:");
}

void loop() {
  unsigned long now = millis();

  // No delay() anywhere in here: the eyes must never go blind while waiting.
  if (now - lastBrainAt >= BRAIN_MS) {
    lastBrainAt = now;

    // SENSE
    lightNow = analogRead(LOW_EYE_PIN);
    int farLight = 0;
    int headLight = 0;
#if LEVEL >= 3
    farLight = analogRead(FAR_EYE_PIN);
#endif
#if LEVEL >= 4
    headLight = analogRead(HEAD_EYE_PIN);
#endif

    // THINK (all of it happens in dino_logic.h)
    DinoKeys keys = dinoStep(brain, settings, (int32_t)now, lightNow, farLight, headLight);

    // ACT: only talk to a servo when its key changes
    if (keys.jump != jumpWasDown) {
      jumpFinger.write(keys.jump ? PRESS_ANGLE : REST_ANGLE);
      jumpWasDown = keys.jump;
    }
#if LEVEL >= 4
    if (keys.duck != duckWasDown) {
      duckFinger.write(keys.duck ? DUCK_PRESS_ANGLE : DUCK_REST_ANGLE);
      duckWasDown = keys.duck;
    }
#endif
    if (keys.jumpStarted && BEEP_ON_JUMP) tone(BUZZER_PIN, 1200, 20);

    // The little light on the UNO shows the moment the eye sees something.
    // Film it in slow motion next to the dino to measure your robot's delay.
    if (keys.lowSees != sawWas) {
      digitalWrite(SAW_LED_PIN, keys.lowSees ? HIGH : LOW);
      if (DEBUG_TIMES && keys.lowSees) { Serial.print("SAW   "); Serial.println(now); }
      sawWas = keys.lowSees;
    }
    if (DEBUG_TIMES && keys.jumpStarted) { Serial.print("PRESS "); Serial.println(now); }
  }

  if (now - lastLcdAt >= LCD_MS) {
    lastLcdAt = now;
    updateScreen();
  }
}

// Only a few characters are written each time, so this takes about a millisecond.
void updateScreen() {
  if (brain.stopped) {
    if (!napShown) {
      napShown = true;
      lcd.clear();
      lcd.print("Nap time! Zzz");
      lcd.setCursor(0, 1);
      lcd.print("Press RESET");
    }
    return;
  }
  lcdTurn = !lcdTurn;
  if (lcdTurn) {
    lcd.setCursor(6, 1);                 // after "Jumps:"
    lcd.print(brain.jumpCount);
  } else {
    lcd.setCursor(12, 1);                // after "L:"
    if (lightNow < 1000) lcd.print(' ');
    if (lightNow < 100) lcd.print(' ');
    if (lightNow < 10) lcd.print(' ');
    lcd.print(lightNow);
  }
}
