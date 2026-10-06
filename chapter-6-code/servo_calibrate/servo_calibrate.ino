// Chapter 6, Step 2: Servo Calibrate - teach the finger where the key is
//
// Open the Serial Monitor at 9600 baud, type a command, press Return:
//   90      move slowly to 90 degrees (any number from 0 to 180)
//   r       remember this angle as REST  (finger just above the key)
//   p       remember this angle as PRESS (key pressed, not crushed)
//   t       test tap: REST -> PRESS -> REST
//   h       hold: press for 300 ms, then let go
//   x       10 taps in a row (how fast can your finger go?)
//   + or -  make the taps faster or slower
//   j or d  switch to the jump finger (pin 9) or the duck finger (pin 10)
#include <Servo.h>

const int JUMP_SERVO_PIN = 9;
const int DUCK_SERVO_PIN = 10;
const int STEP_DELAY_MS  = 15;    // wait between 1-degree steps, so it never slams

Servo finger;
int fingerPin = JUMP_SERVO_PIN;
int angle = 90;          // where the finger is now
int restAngle = 90;
int pressAngle = 70;
int tapMs = 80;          // how long a tap holds the key

void setup() {
  Serial.begin(9600);
  finger.write(angle);             // set the angle first, so the finger doesn't twitch
  finger.attach(fingerPin);
  Serial.println("Servo Calibrate is ready.");
  Serial.println("Type an angle (0 to 180), or r, p, t, h, x, +, -, j, d");
  report();
}

void loop() {
  if (Serial.available() == 0) return;

  char c = Serial.peek();
  if (c >= '0' && c <= '9') {
    int wanted = Serial.parseInt();
    if (wanted > 180) {
      Serial.println("Angles only go from 0 to 180.");
    } else {
      moveSlowly(wanted);
      report();
    }
    return;
  }

  Serial.read();                   // take the letter out of the queue
  if (c == 'r') {
    restAngle = angle;
    Serial.print("REST is now ");
    Serial.println(restAngle);
    printCopyLines();
  } else if (c == 'p') {
    pressAngle = angle;
    Serial.print("PRESS is now ");
    Serial.println(pressAngle);
    printCopyLines();
  } else if (c == 't') {
    tap(tapMs);
    Serial.println("Tap!");
  } else if (c == 'h') {
    tap(300);
    Serial.println("Held for 300 ms.");
  } else if (c == 'x') {
    for (int i = 0; i < 10; i++) {
      tap(tapMs);
      delay(tapMs);
    }
    Serial.print("10 taps, ");
    Serial.print(tapMs);
    Serial.print(" ms down and ");
    Serial.print(tapMs);
    Serial.print(" ms up each. That is ");
    Serial.print(1000 / (tapMs * 2));
    Serial.println(" taps per second. Did the game see all 10?");
  } else if (c == '+') {
    if (tapMs > 20) tapMs -= 10;
    Serial.print("Faster: taps are now ");
    Serial.print(tapMs);
    Serial.println(" ms.");
  } else if (c == '-') {
    if (tapMs < 300) tapMs += 10;
    Serial.print("Slower: taps are now ");
    Serial.print(tapMs);
    Serial.println(" ms.");
  } else if (c == 'j' || c == 'd') {
    finger.detach();
    fingerPin = (c == 'j') ? JUMP_SERVO_PIN : DUCK_SERVO_PIN;
    finger.write(angle);
    finger.attach(fingerPin);
    Serial.println(c == 'j' ? "Now moving the JUMP finger (pin 9)." : "Now moving the DUCK finger (pin 10).");
  }
  // anything else (like the Return key) is ignored
}

// Go to an angle one degree at a time.
void moveSlowly(int wanted) {
  while (angle != wanted) {
    if (angle < wanted) angle++;
    else angle--;
    finger.write(angle);
    delay(STEP_DELAY_MS);
  }
}

// A tap goes straight to PRESS and back, like the real game.
void tap(int holdMs) {
  moveSlowly(restAngle);
  finger.write(pressAngle);
  delay(holdMs);
  finger.write(restAngle);
  angle = restAngle;
}

void report() {
  Serial.print("Angle: ");
  Serial.println(angle);
}

void printCopyLines() {
  bool duck = (fingerPin == DUCK_SERVO_PIN);
  Serial.println("Copy these into dino_bot.ino:");
  Serial.print(duck ? "const int DUCK_REST_ANGLE  = " : "const int REST_ANGLE  = ");
  Serial.print(restAngle);
  Serial.println(";");
  Serial.print(duck ? "const int DUCK_PRESS_ANGLE = " : "const int PRESS_ANGLE = ");
  Serial.print(pressAngle);
  Serial.println(";");
}
