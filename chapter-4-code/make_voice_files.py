# Chapter 4, Step 6: turn the robot's phrases into sound files for the SD card
# The Mac's own voice reads every phrase in phrases.json into sd_card/MP3/0001.mp3, 0002.mp3...
# It also writes robot_bridge/phrases.h so the Arduino knows which numbers are greetings.
# Only NUMBERS go into the Arduino sketch. No names, no words.
#
#   python make_voice_files.py

import json
import shutil
import subprocess
import tempfile
import wave
from pathlib import Path

HERE = Path(__file__).resolve().parent
PHRASES_FILE = HERE / "phrases.json"               # PRIVATE: your own phrases
EXAMPLE_FILE = HERE / "phrases.example.json"
MP3_FOLDER = HERE / "sd_card" / "MP3"
HEADER_FILE = HERE / "robot_bridge" / "phrases.h"


def number_phrases(phrases):
    """Give every phrase a number: greetings first, then the others. Returns (list, numbers)."""
    greetings = [text for text in phrases.get("greetings", []) if text.strip()]
    others = [text for text in phrases.get("others", []) if text.strip()]
    if not greetings:
        raise SystemExit("phrases.json needs at least one greeting.")
    numbers = {"GREETING_FIRST": 1, "GREETING_LAST": len(greetings)}
    if others:
        numbers["OTHER_FIRST"] = len(greetings) + 1
        numbers["OTHER_LAST"] = len(greetings) + len(others)
    numbers["COUNT"] = len(greetings) + len(others)
    return greetings + others, numbers


def header_text(numbers):
    """The phrases.h file: numbers only."""
    lines = ["// Made by make_voice_files.py. Numbers only: no names or words in here.",
             "// File 1 is sd_card/MP3/0001.mp3, file 2 is 0002.mp3, and so on."]
    lines += [f"#define PHRASE_{name} {number}" for name, number in numbers.items()]
    return "\n".join(lines) + "\n"


def speak_to_mp3(text, voice, mp3_file, work_folder):
    """say -> AIFF sound file -> WAV sound file -> MP3."""
    import lameenc                                  # the MP3 squasher

    aiff, wav = Path(work_folder) / "voice.aiff", Path(work_folder) / "voice.wav"
    text = text.lstrip("-")                         # so it can't be mistaken for an option
    command = ["say", "-o", str(aiff), text]
    if voice:
        command[1:1] = ["-v", voice]
    subprocess.run(command, check=True)             # a list, never shell=True
    subprocess.run(["afconvert", "-f", "WAVE", "-d", "LEI16@22050", str(aiff), str(wav)], check=True)

    with wave.open(str(wav), "rb") as sound:
        encoder = lameenc.Encoder()
        encoder.set_bit_rate(64)
        encoder.set_in_sample_rate(sound.getframerate())
        encoder.set_channels(sound.getnchannels())
        encoder.set_quality(2)                      # 2 = best quality
        mp3 = encoder.encode(sound.readframes(sound.getnframes())) + encoder.flush()
    Path(mp3_file).write_bytes(mp3)


def main():
    if not PHRASES_FILE.exists():
        shutil.copy(EXAMPLE_FILE, PHRASES_FILE)
        print("📝 Made phrases.json from the example. Edit it and run me again to use your own phrases.")
    phrases = json.loads(PHRASES_FILE.read_text())
    texts, numbers = number_phrases(phrases)

    shutil.rmtree(MP3_FOLDER, ignore_errors=True)   # start clean so old files don't linger
    MP3_FOLDER.mkdir(parents=True)
    with tempfile.TemporaryDirectory() as work_folder:
        for number, text in enumerate(texts, start=1):
            mp3_file = MP3_FOLDER / f"{number:04d}.mp3"
            speak_to_mp3(text, phrases.get("voice", ""), mp3_file, work_folder)
            print(f"🔊 {mp3_file.name}  {text}")

    HEADER_FILE.write_text(header_text(numbers))
    print(f"✅ {len(texts)} sound files are in sd_card/MP3/")
    print("✅ Wrote robot_bridge/phrases.h. Upload robot_bridge.ino again so the Arduino gets the new numbers.")
    print("Next: copy the whole MP3 folder onto the SD card.")


if __name__ == "__main__":
    main()
