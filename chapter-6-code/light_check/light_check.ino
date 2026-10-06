// Chapter 6, Step 3: Light Check - see what the robot's eyes see
//
// Open Tools -> Serial Plotter and set it to 115200 baud.
// Every cactus that passes an eye makes a dip in its line.
// (Eyes that aren't plugged in yet draw wobbly nonsense. Ignore them.)
#include <LiquidCrystal.h>

LiquidCrystal lcd(12, 11, 5, 4, 3, 2);   // RS, E, D4, D5, D6, D7 (same as Chapter 1)

const int LOW_EYE_PIN  = A0;      // cactus height, near the dino
const int FAR_EYE_PIN  = A1;      // cactus height, farther ahead (Step 6)
const int HEAD_EYE_PIN = A2;      // head height (Step 7)

const unsigned long SAMPLE_MS = 5;       // one line every 5 ms = 200 lines a second
const unsigned long LCD_MS    = 200;     // the screen updates 5 times a second

unsigned long nextSampleAt = 0;
unsigned long lastLcdAt = 0;
int lowest = 1023;       // the darkest and brightest A0 has seen so far
int highest = 0;

void setup() {
  // 200 lines a second is too much for 9600 baud, so this sketch talks faster.
  Serial.begin(115200);
  lcd.begin(16, 2);
  lcd.print("A0 light:");
  lcd.setCursor(0, 1);
  lcd.print("lo:     hi:");
}

void loop() {
  unsigned long now = millis();

  if (now >= nextSampleAt) {
    nextSampleAt += SAMPLE_MS;
    if (nextSampleAt < now) nextSampleAt = now + SAMPLE_MS;   // fell behind: catch up

    int a0 = analogRead(LOW_EYE_PIN);
    int a1 = analogRead(FAR_EYE_PIN);
    int a2 = analogRead(HEAD_EYE_PIN);
    if (a0 < lowest) lowest = a0;
    if (a0 > highest) highest = a0;

    // "name:number" pairs with commas between them is what the Serial Plotter likes.
    Serial.print("A0:");
    Serial.print(a0);
    Serial.print(",A1:");
    Serial.print(a1);
    Serial.print(",A2:");
    Serial.println(a2);
  }

  if (now - lastLcdAt >= LCD_MS) {
    lastLcdAt = now;
    printPadded(10, 0, analogRead(LOW_EYE_PIN));
    printPadded(3, 1, lowest);
    printPadded(11, 1, highest);
  }
}

// Print a number in a 4-character space, so old digits get wiped.
void printPadded(int col, int row, int value) {
  lcd.setCursor(col, row);
  if (value < 1000) lcd.print(' ');
  if (value < 100) lcd.print(' ');
  if (value < 10) lcd.print(' ');
  lcd.print(value);
}
