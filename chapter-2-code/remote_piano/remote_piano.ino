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
