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
