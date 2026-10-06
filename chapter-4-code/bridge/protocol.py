# The notes the two brains pass down the USB cable.
# This file builds the notes the Mac sends, and reads the notes the Arduino sends back.
# It also tidies up text so it fits the little 16x2 screen.

LCD_WIDTH = 16          # letters per line on the screen
MAX_LINE = 64           # the Arduino refuses notes longer than this
MAX_SPOKEN = 100        # the robot never says more than this many letters
TUNES = ("HELLO", "WIN", "SAD", "SIREN")
LED_MODES = ("ON", "OFF", "BLINK")
MAX_NOTES = 8

# Phones like to swap plain quotes for curly ones. The screen only knows plain ones.
LOOKALIKES = {
    "‘": "'", "’": "'", "“": '"', "”": '"',
    "–": "-", "—": "-", "…": "...", " ": " ",
}


# ---------- tidying text ----------

def clean_for_lcd(text):
    """Keep only letters the screen can draw. Emoji and other fancy letters become ?"""
    for fancy, plain in LOOKALIKES.items():
        text = text.replace(fancy, plain)
    cleaned = ""
    for letter in text:
        if letter in "\r\n\t":
            letter = " "
        elif letter == "|":
            letter = "/"                 # | is special: it means "next line" in SHOW
        elif not (32 <= ord(letter) <= 126):
            if cleaned.endswith("?"):
                continue                 # one ? per emoji is plenty
            letter = "?"
        cleaned += letter
    return " ".join(cleaned.split())     # squash double spaces


def clean_for_speech(text):
    """Get text ready for the voice: no hidden control letters, 100 letters at most."""
    text = "".join(letter if letter.isprintable() else " " for letter in text)
    text = " ".join(text.split())
    text = text.lstrip("-")              # so the voice program can't mistake it for an option
    return text[:MAX_SPOKEN].strip()


def wrap_for_lcd(text):
    """Split text into two screen lines without chopping words in half."""
    lines = ["", ""]
    row = 0
    for word in clean_for_lcd(text).split():
        while row < 2:
            gap = " " if lines[row] else ""
            if len(lines[row]) + len(gap) + len(word) <= LCD_WIDTH:
                lines[row] += gap + word
                break
            if not lines[row]:           # a giant word: cut it to fit
                lines[row] = word[:LCD_WIDTH]
                break
            row += 1                     # this line is full, try the next one
        if row == 2:
            break                        # the screen is full
    return lines[0], lines[1]


# ---------- notes from the Mac to the Arduino ----------

def ping():
    return "PING"


def idle():
    return "IDLE"


def show(line1, line2=""):
    line1 = clean_for_lcd(line1)[:LCD_WIDTH]
    line2 = clean_for_lcd(line2)[:LCD_WIDTH]
    return f"SHOW {line1}|{line2}"


def show_wrapped(text):
    return show(*wrap_for_lcd(text))


def beep(hz=880, ms=200):
    if not (100 <= hz <= 5000 and 10 <= ms <= 2000):
        raise ValueError("BEEP needs a pitch from 100 to 5000 and a length from 10 to 2000")
    return f"BEEP {int(hz)} {int(ms)}"


def tune(name):
    name = str(name).upper()
    if name not in TUNES:
        raise ValueError(f"I only know these tunes: {', '.join(TUNES)}")
    return f"TUNE {name}"


def notes(pitches):
    pitches = [int(hz) for hz in pitches]
    if not 1 <= len(pitches) <= MAX_NOTES:
        raise ValueError("A theme tune has 1 to 8 notes")
    if any(not 100 <= hz <= 5000 for hz in pitches):
        raise ValueError("Every note must be from 100 to 5000")
    return "NOTES " + " ".join(str(hz) for hz in pitches)


def led(mode):
    mode = str(mode).upper()
    if mode not in LED_MODES:
        raise ValueError("The LED can be ON, OFF or BLINK")
    return f"LED {mode}"


def play(number):
    if not 1 <= int(number) <= 9999:
        raise ValueError("Voice files are numbered 1 to 9999")
    return f"PLAY {int(number)}"


NOTE_NAMES = {"C": 523, "D": 587, "E": 659, "F": 698, "G": 784, "A": 880, "B": 988, "C2": 1047}


def read_tune(text):
    """ "C E G C2" or "523, 659, 784" -> [523, 659, 784, 1047]. At most 8 notes."""
    pitches = []
    for word in text.replace(",", " ").upper().split():
        hz = NOTE_NAMES.get(word) or (int(word) if word.isdigit() else 0)
        if not 100 <= hz <= 5000:
            raise ValueError(f"{word!r} is not a note. Use C D E F G A B C2, or numbers from 100 to 5000.")
        pitches.append(hz)
    if not 1 <= len(pitches) <= MAX_NOTES:
        raise ValueError("A theme tune has 1 to 8 notes.")
    return pitches


# ---------- notes from the Arduino to the Mac ----------

def parse_line(line):
    """Turn one line from the Arduino into a small dictionary, like {"kind": "VISITOR", "count": 3}."""
    line = line.strip()
    if len(line) > MAX_LINE:
        return {"kind": "JUNK", "text": line[:MAX_LINE]}
    words = line.split()
    if line == "READY":
        return {"kind": "READY"}
    if line == "PONG":
        return {"kind": "PONG"}
    if line == "EVENT LEFT":
        return {"kind": "LEFT"}
    if len(words) == 3 and words[:2] == ["EVENT", "VISITOR"] and words[2].isdigit():
        return {"kind": "VISITOR", "count": int(words[2])}
    if len(words) == 2 and words[0] == "OK":
        return {"kind": "OK", "verb": words[1]}
    if len(words) == 2 and words[0] == "ERR":
        return {"kind": "ERR", "reason": words[1]}
    return {"kind": "JUNK", "text": line}
