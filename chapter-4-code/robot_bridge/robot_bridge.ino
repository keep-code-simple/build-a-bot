// Chapter 4: Robot Bridge
// The Arduino is the robot's LITTLE brain: quick reflexes, a screen and a buzzer.
// The Mac is the BIG brain: talking, faces and the internet.
// They pass notes down the USB cable. Every note is one short line of text.
//
// Notes the Mac can send (try them in the Serial Monitor: 9600 baud, "New Line"):
//   PING                     -> PONG
//   SHOW Hello|I am a robot  -> shows two lines on the screen
//   BEEP 880 200             -> one beep: pitch 100 to 5000, length 10 to 2000 ms
//   TUNE HELLO               -> HELLO, WIN, SAD or SIREN
//   NOTES 523 659 784        -> your own tune, up to 8 notes
//   LED ON                   -> ON, OFF or BLINK
//   PLAY 1                   -> voice file 1 from the SD card (Step 6 only)
//   IDLE                     -> back to the waiting screen
//
// Notes the Arduino sends back:
//   READY, PONG, OK <word>, ERR <why>, EVENT VISITOR <count>, EVENT LEFT
#include <LiquidCrystal.h>

// Step 6 only: change this 0 to 1 when the DFPlayer Mini is wired in.
#define USE_DFPLAYER 0

#if USE_DFPLAYER
#include <SoftwareSerial.h>
#include <DFRobotDFPlayerMini.h>
SoftwareSerial playerSerial(A1, A2);     // A1 listens to the player's TX, A2 talks to its RX
DFRobotDFPlayerMini player;
#endif

// make_voice_files.py writes phrases.h: which sound files are greetings.
#if __has_include("phrases.h")
#include "phrases.h"
#else
#define PHRASE_GREETING_FIRST 1
#define PHRASE_GREETING_LAST  1
#endif

LiquidCrystal lcd(12, 11, 5, 4, 3, 2);   // RS, E, D4, D5, D6, D7

const int TRIG_PIN   = 9;
const int ECHO_PIN   = 10;
const int BUZZER_PIN = 8;
const int LED_PIN    = 7;                // if you have an LED on pin 7. Fine without one.

const int TRIGGER_CM = 60;               // how close before it counts as a visitor
const int PLAYER_VOLUME = 22;            // 0 to 30 (Step 6 only)
const unsigned long MAC_QUIET_MS = 60000;   // no note from the Mac for this long = "I'm on my own"

// ---------- memory ----------
char line[65];                // one note from the Mac: 64 letters plus the end mark
byte lineLength = 0;
bool lineTooLong = false;

bool someoneHere = false;
int visitors = 0;
unsigned long lastSensorCheck = 0;

bool macHasTalked = false;
unsigned long lastMacNote = 0;

int tuneNotes[8];             // the tune that is playing right now
byte tuneLength = 0;
byte tunePosition = 0;
int tuneNoteMs = 150;
unsigned long nextNoteAt = 0;

bool ledBlinking = false;
unsigned long lastBlink = 0;

bool playerFound = false;

void setup() {
  pinMode(TRIG_PIN, OUTPUT);
  pinMode(ECHO_PIN, INPUT);
  pinMode(BUZZER_PIN, OUTPUT);
  pinMode(LED_PIN, OUTPUT);
  Serial.begin(9600);
  lcd.begin(16, 2);
  randomSeed(analogRead(A0));
  showIdle();
  findPlayer();
  Serial.println(F("READY"));
}

void loop() {
  readNotesFromMac();
  playNextNote();
  blinkLed();

  if (millis() - lastSensorCheck >= 100) {     // look 10 times a second
    lastSensorCheck = millis();
    checkForVisitor();
  }
}

// ---------- reflexes: these never wait for the Mac ----------
void checkForVisitor() {
  long cm = readDistanceCm();

  // Someone walked up
  if (cm < TRIGGER_CM && !someoneHere) {
    someoneHere = true;
    visitors++;
    Serial.print(F("EVENT VISITOR "));
    Serial.println(visitors);

    setLed(true);                              // the reflex: light up...
    startTune(1319, 1760, 0, 0, 2, 70);        // ...and chirp

    if (!macIsTalking()) {                     // no Mac? Do the greeting myself.
      lcd.clear();
      lcd.print(F("Hello, human!"));
      lcd.setCursor(0, 1);
      lcd.print(F("Visitor #"));
      lcd.print(visitors);
      playGreetingFile();
    }
  }

  // They walked away
  if (cm > TRIGGER_CM + 20 && someoneHere) {
    someoneHere = false;
    Serial.println(F("EVENT LEFT"));
    setLed(false);
    showIdle();
  }
}

// Has the Mac sent a note in the last minute? Then it does the talking.
bool macIsTalking() {
  return macHasTalked && (millis() - lastMacNote < MAC_QUIET_MS);
}

long readDistanceCm() {
  digitalWrite(TRIG_PIN, LOW);
  delayMicroseconds(2);
  digitalWrite(TRIG_PIN, HIGH);    // shout!
  delayMicroseconds(10);
  digitalWrite(TRIG_PIN, LOW);

  long echoTime = pulseIn(ECHO_PIN, HIGH, 30000);  // listen for the echo
  if (echoTime == 0) return 999;   // no echo = nothing nearby
  return echoTime / 58;            // 58 microseconds per cm, there and back
}

// ---------- reading notes from the Mac ----------
void readNotesFromMac() {
  while (Serial.available() > 0) {
    char letter = Serial.read();

    if (letter == '\n' || letter == '\r') {    // end of the note
      if (lineTooLong) {
        Serial.println(F("ERR TOO_LONG"));
      } else if (lineLength > 0) {
        line[lineLength] = '\0';
        obey(line);
      }
      lineLength = 0;
      lineTooLong = false;
    } else if (lineLength < 64) {
      line[lineLength] = letter;
      lineLength++;
    } else {
      lineTooLong = true;                      // more than 64 letters: ignore the rest
    }
  }
}

// Does the note start with this word? If so, point "rest" at what comes after it.
bool startsWith(char* note, const char* word, char*& rest) {
  size_t length = strlen(word);
  if (strncasecmp(note, word, length) != 0) return false;
  if (note[length] != ' ' && note[length] != '\0') return false;
  rest = note + length;
  while (*rest == ' ') rest++;
  return true;
}

// Read one whole number and move "text" past it. Gives -1 if there is no number.
long nextNumber(char*& text) {
  while (*text == ' ') text++;
  if (*text < '0' || *text > '9') return -1;
  long number = 0;
  while (*text >= '0' && *text <= '9') {
    if (number < 100000) number = number * 10 + (*text - '0');
    text++;
  }
  if (*text != ' ' && *text != '\0') return -1;   // "88x" is not a number
  return number;
}

void obey(char* note) {
  char* rest;
  macHasTalked = true;
  lastMacNote = millis();

  if (startsWith(note, "PING", rest)) {
    Serial.println(F("PONG"));

  } else if (startsWith(note, "SHOW", rest)) {
    showText(rest);
    Serial.println(F("OK SHOW"));

  } else if (startsWith(note, "BEEP", rest)) {
    long hz = nextNumber(rest);
    long ms = nextNumber(rest);
    if (hz < 100 || hz > 5000 || ms < 10 || ms > 2000) {
      Serial.println(F("ERR RANGE"));
    } else {
      tuneLength = 0;                          // stop any tune
      tone(BUZZER_PIN, hz, ms);
      Serial.println(F("OK BEEP"));
    }

  } else if (startsWith(note, "TUNE", rest)) {
    if (strcasecmp(rest, "HELLO") == 0)      startTune(523, 659, 784, 1047, 4, 150);
    else if (strcasecmp(rest, "WIN") == 0)   startTune(784, 988, 1175, 1568, 4, 120);
    else if (strcasecmp(rest, "SAD") == 0)   startTune(392, 370, 349, 330, 4, 250);
    else if (strcasecmp(rest, "SIREN") == 0) startSiren();
    else { Serial.println(F("ERR UNKNOWN")); return; }
    Serial.println(F("OK TUNE"));

  } else if (startsWith(note, "NOTES", rest)) {
    int newNotes[8];
    byte count = 0;
    bool good = (*rest != '\0');
    while (good && *rest != '\0') {
      long hz = nextNumber(rest);
      if (hz < 100 || hz > 5000 || count == 8) good = false;
      else { newNotes[count] = hz; count++; }
      while (*rest == ' ') rest++;
    }
    if (!good) {
      Serial.println(F("ERR RANGE"));
    } else {
      for (byte i = 0; i < count; i++) tuneNotes[i] = newNotes[i];
      beginTune(count, 150);
      Serial.println(F("OK NOTES"));
    }

  } else if (startsWith(note, "LED", rest)) {
    if (strcasecmp(rest, "ON") == 0)         setLed(true);
    else if (strcasecmp(rest, "OFF") == 0)   setLed(false);
    else if (strcasecmp(rest, "BLINK") == 0) ledBlinking = true;
    else { Serial.println(F("ERR UNKNOWN")); return; }
    Serial.println(F("OK LED"));

  } else if (startsWith(note, "PLAY", rest)) {
    long number = nextNumber(rest);
    if (number < 1 || number > 9999) Serial.println(F("ERR RANGE"));
    else if (!playerFound)           Serial.println(F("ERR NO_PLAYER"));
    else {
      playFile(number);
      Serial.println(F("OK PLAY"));
    }

  } else if (startsWith(note, "IDLE", rest)) {
    setLed(false);
    showIdle();
    Serial.println(F("OK IDLE"));

  } else {
    Serial.println(F("ERR UNKNOWN"));
  }
}

// ---------- screen ----------
void showIdle() {
  lcd.clear();
  lcd.print(F("Talking Robot ON"));
  lcd.setCursor(0, 1);
  lcd.print(F("Visitors: "));
  lcd.print(visitors);
}

// "Hello|I am a robot" -> line 1 and line 2. Each line is cut at 16 letters.
void showText(char* text) {
  lcd.clear();
  byte row = 0;
  byte column = 0;
  for (; *text != '\0'; text++) {
    if (*text == '|' && row == 0) {            // the | means "next line"
      row = 1;
      column = 0;
      lcd.setCursor(0, 1);
    } else if (column < 16) {
      lcd.print(*text);
      column++;
    }
  }
}

// ---------- LED ----------
void setLed(bool on) {
  ledBlinking = false;
  digitalWrite(LED_PIN, on ? HIGH : LOW);
}

void blinkLed() {
  if (ledBlinking && millis() - lastBlink >= 250) {
    lastBlink = millis();
    digitalWrite(LED_PIN, !digitalRead(LED_PIN));
  }
}

// ---------- tunes: played one note at a time, so the robot keeps listening ----------
void beginTune(byte length, int noteMs) {
  tuneLength = length;
  tunePosition = 0;
  tuneNoteMs = noteMs;
  nextNoteAt = millis();
}

void startTune(int a, int b, int c, int d, byte length, int noteMs) {
  tuneNotes[0] = a;
  tuneNotes[1] = b;
  tuneNotes[2] = c;
  tuneNotes[3] = d;
  beginTune(length, noteMs);
}

void startSiren() {
  for (byte i = 0; i < 8; i++) tuneNotes[i] = (i % 2 == 0) ? 1200 : 800;
  beginTune(8, 250);
}

void playNextNote() {
  if (tunePosition < tuneLength && millis() >= nextNoteAt) {
    tone(BUZZER_PIN, tuneNotes[tunePosition], tuneNoteMs);
    tunePosition++;
    nextNoteAt = millis() + tuneNoteMs + tuneNoteMs / 5;   // a tiny gap between notes
  }
}

// ---------- Step 6: the DFPlayer Mini (talking with no Mac) ----------
void findPlayer() {
#if USE_DFPLAYER
  playerSerial.begin(9600);
  playerFound = player.begin(playerSerial, true, true);
  if (!playerFound) {
    // Some clone chips never send "got it" answers, so try again without them...
    player.begin(playerSerial, false, true);
    playerFound = (player.readState() != -1);   // ...and ask a question to see if it's there
  }
  if (playerFound) player.volume(PLAYER_VOLUME);
#endif
}

void playFile(int number) {
#if USE_DFPLAYER
  if (playerFound) player.playMp3Folder(number);   // plays /MP3/0001.mp3 and so on
#else
  (void)number;                                    // no player in this build
#endif
}

void playGreetingFile() {
  playFile(random(PHRASE_GREETING_FIRST, PHRASE_GREETING_LAST + 1));
}
