// Chapter 3: Robot Brain
// The Arduino listens to the MacBook over the USB cable.
// The MacBook does the seeing. The Arduino does the beeping, blinking, and talking.
//
// Messages it understands (one letter each):
//   F = I see a face          N = nobody there
//   0 to 5 = number of fingers
//   r = rock    p = paper    s = scissors
//   Gestures: V = peace   U = thumbs up   D = thumbs down   H = open hand
//             B = fist    O = pointing up   L = I love you
//   Faces:    S = smile   W = mouth open   K = wink   E = eyebrows up
#include <LiquidCrystal.h>

LiquidCrystal lcd(12, 11, 5, 4, 3, 2);   // RS, E, D4, D5, D6, D7

const int BUZZER_PIN = 8;
const int LED_PIN    = 7;

// Change these! Max 16 characters each.
const char* greetings[] = {
  "Hello, human!",
  "Nice face!",
  "Welcome back!",
  "Robot says hi!",
  "Looking sharp!"
};
const int NUM_GREETINGS = sizeof(greetings) / sizeof(greetings[0]);

const char* MOVES[] = {"ROCK", "PAPER", "SCISSORS"};
int yourScore = 0;
int robotScore = 0;

void setup() {
  pinMode(BUZZER_PIN, OUTPUT);
  pinMode(LED_PIN, OUTPUT);
  Serial.begin(9600);
  lcd.begin(16, 2);
  randomSeed(analogRead(A0));
  showIdle();
  Serial.println("Robot brain ready! Type F, N, 0-5, r, p, s, or a gesture or face letter.");
}

void loop() {
  if (Serial.available() > 0) {          // did a message arrive?
    char message = Serial.read();

    if (message == 'F') sawFace();
    else if (message == 'N') showIdle();
    else if (message >= '0' && message <= '5') showFingers(message - '0');
    else if (message == 'r') playRound(0);
    else if (message == 'p') playRound(1);
    else if (message == 's') playRound(2);
    // Gestures: what you did, what the robot says back (max 16 characters each), and a sound
    else if (message == 'V') showGesture("PEACE!",       "Peace, human!",  playWin);
    else if (message == 'U') showGesture("THUMBS UP!",   "Awesome!",       playWin);
    else if (message == 'D') showGesture("THUMBS DOWN!", "Oh no...",       playLose);
    else if (message == 'H') showGesture("OPEN HAND!",   "High five!",     playHello);
    else if (message == 'B') showGesture("FIST!",        "Fist bump!",     playTie);
    else if (message == 'O') showGesture("POINTING UP!", "You are no. 1!", playHello);
    else if (message == 'L') showGesture("I LOVE YOU!",  "Love you too!",  playWin);
    // Faces you make
    else if (message == 'S') showGesture("YOU SMILED!",  "Nice smile!",    playWin);
    else if (message == 'W') showGesture("MOUTH OPEN!",  "Wow!",           playHello);
    else if (message == 'K') showGesture("YOU WINKED!",  "I saw that!",    playTie);
    else if (message == 'E') showGesture("EYEBROWS UP!", "Surprised?",     playHello);
    // anything else (like the Enter key) is ignored
  }
}

void showIdle() {
  digitalWrite(LED_PIN, LOW);
  lcd.clear();
  lcd.print("Robot eyes: ON");
  lcd.setCursor(0, 1);
  lcd.print("Waiting...");
}

void sawFace() {
  Serial.println("Got F: I see a face!");
  digitalWrite(LED_PIN, HIGH);
  lcd.clear();
  lcd.print("I SEE YOU!");
  lcd.setCursor(0, 1);
  lcd.print(greetings[random(NUM_GREETINGS)]);
  playHello();
}

void showFingers(int count) {
  Serial.print("Got fingers: ");
  Serial.println(count);
  digitalWrite(LED_PIN, HIGH);
  lcd.clear();
  lcd.print("Fingers: ");
  lcd.print(count);
  lcd.setCursor(0, 1);
  for (int i = 0; i < count; i++) {
    lcd.print("| ");                     // one bar per finger
  }
  for (int i = 0; i < count; i++) {      // one beep per finger
    tone(BUZZER_PIN, 880, 80);
    delay(150);
  }
}

void showGesture(const char* youDid, const char* robotSays, void (*playSound)()) {
  Serial.print("Got gesture: ");
  Serial.println(youDid);
  digitalWrite(LED_PIN, HIGH);
  lcd.clear();
  lcd.print(youDid);
  lcd.setCursor(0, 1);
  lcd.print(robotSays);
  playSound();
}

// Rock = 0, Paper = 1, Scissors = 2
void playRound(int yourMove) {
  int robotMove = random(3);             // the robot picks at random. Or does it?

  Serial.print("You: ");
  Serial.print(MOVES[yourMove]);
  Serial.print("   Robot: ");
  Serial.println(MOVES[robotMove]);

  // Dramatic countdown
  lcd.clear(); lcd.print("Rock...");     tone(BUZZER_PIN, 523, 150);  delay(350);
  lcd.clear(); lcd.print("Paper...");    tone(BUZZER_PIN, 587, 150);  delay(350);
  lcd.clear(); lcd.print("Scissors...");  tone(BUZZER_PIN, 659, 150);  delay(350);
  lcd.clear(); lcd.print("SHOOT!");      tone(BUZZER_PIN, 1047, 250); delay(500);

  // Show both moves
  lcd.clear();
  lcd.print("You:   ");
  lcd.print(MOVES[yourMove]);
  lcd.setCursor(0, 1);
  lcd.print("Robot: ");
  lcd.print(MOVES[robotMove]);
  delay(1500);

  // Who won?  0 = tie, 1 = you, 2 = robot
  int result = (yourMove - robotMove + 3) % 3;
  lcd.clear();
  if (result == 0) {
    lcd.print("TIE!");
    playTie();
  } else if (result == 1) {
    lcd.print("YOU WIN!");
    yourScore++;
    playWin();
  } else {
    lcd.print("ROBOT WINS!");
    robotScore++;
    playLose();
  }
  lcd.setCursor(0, 1);
  lcd.print("You ");
  lcd.print(yourScore);
  lcd.print(" Robot ");
  lcd.print(robotScore);
}

// ---------- Sounds ----------
void playHello() {
  int notes[] = {523, 659, 784, 1047};     // C, E, G, high C
  for (int i = 0; i < 4; i++) {
    tone(BUZZER_PIN, notes[i], 150);
    delay(180);
  }
}

void playWin() {
  int notes[] = {784, 988, 1175, 1568};    // a happy climb
  for (int i = 0; i < 4; i++) {
    tone(BUZZER_PIN, notes[i], 120);
    delay(140);
  }
}

void playLose() {
  int notes[] = {392, 370, 349, 330};      // sad trombone
  for (int i = 0; i < 4; i++) {
    tone(BUZZER_PIN, notes[i], 250);
    delay(300);
  }
}

void playTie() {
  tone(BUZZER_PIN, 659, 200);
  delay(250);
  tone(BUZZER_PIN, 659, 200);
  delay(250);
}
