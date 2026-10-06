# Chapter 4, Step 1: The Robot Speaks
# The screen shows your sentence AND the Mac says it out loud, at the same moment.
#
#   python say_it.py "Hello, I am a robot"     say one thing
#   python say_it.py                           chat mode: it keeps asking
#   python say_it.py --fake-arduino "Hi"       no robot plugged in? Pretend one.
#
# Close the Serial Monitor first: only one program can use the USB cable.

import argparse

from bridge import protocol
from bridge.arduino_link import ArduinoLink, FakeArduino
from bridge.settings import load_config
from bridge.speech import SpeechQueue


def main():
    parser = argparse.ArgumentParser(description="Make the robot show and say a sentence.")
    parser.add_argument("words", nargs="*", help="what the robot should say")
    parser.add_argument("--voice", help="a voice name from: say -v '?'")
    parser.add_argument("--fake-arduino", action="store_true", help="use a pretend Arduino")
    args = parser.parse_args()

    config = load_config()
    speech = SpeechQueue(args.voice or config.get("voice", ""), config.get("speech_rate", 0))
    link = ArduinoLink(fake=FakeArduino() if args.fake_arduino else None).start()
    if not link.wait_until_ready():
        print("🤖 The robot isn't answering yet. I'll still talk, and the screen will catch up.")

    def show_and_say(text):
        line = protocol.show_wrapped(text)
        print("🤖 Screen:", line[5:].replace("|", "  /  "))
        speech.say(text, first=lambda: link.send(line))   # screen first, then the voice starts
        speech.wait_until_quiet()

    try:
        if args.words:
            show_and_say(" ".join(args.words))
        else:
            print("Chat mode! Type something and press Return. Press Return on an empty line to stop.")
            while True:
                text = input("What should I say? ").strip()
                if not text:
                    break
                show_and_say(text)
    except (KeyboardInterrupt, EOFError):
        print()
    link.stop()
    speech.stop()


if __name__ == "__main__":
    main()
