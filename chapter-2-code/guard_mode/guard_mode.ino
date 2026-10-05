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
