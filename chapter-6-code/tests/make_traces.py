#!/usr/bin/env python3
"""Chapter 6: Dino Bot - make pretend light traces for the replay tests.

A "trace" is what the three eyes would see over time, saved as a CSV file:

    ms,a0,a1,a2
    0,820,818,823
    5,819,821,820
    ...

These traces are SYNTHETIC: made from a simple model of a screen, not
recorded from a real one. Lines starting with # are the answer key (where
each obstacle really was), which the tests use to mark the brain's work.

Run it from the tests folder to rebuild the four files in traces/:

    python3 make_traces.py

The model (all distances in millimeters on the screen):
  - the dino's nose is at 0; obstacles slide toward it from the right
  - eye A0 sits EYE_TO_DINO_MM ahead of the nose, at cactus height
  - eye A1 sits GAP_MM farther ahead, at the same height (the speed trap)
  - eye A2 sits above A1, at the height of the dino's head (for birds)
  - an eye reads BG when it sees background and OBJ when an obstacle
    covers it; at night the two swap around, the way the game's colors flip
  - a real light sensor reacts a little slowly, so readings are smoothed
    over about 15 ms, and a little random noise is added
"""
import os
import random

STEP_MS = 5              # one row every 5 ms = 200 rows a second, like light_check
EYE_TO_DINO_MM = 55
GAP_MM = 50
DINO_LEN_MM = 20
EYE_WIDTH_MM = 5         # how wide a strip of screen one eye looks at
LAG_MS = 15              # the sensor's reaction time
NOISE = 5
FADE_MS = 800            # how long the day/night fade takes

DAY_BG, DAY_OBJ = 820, 260       # bright screen, dark cactus
NIGHT_BG, NIGHT_OBJ = 140, 640   # dark screen, light cactus

# Starting points for the brain's settings; the tests read them from the trace.
ROBOT_DELAY_MS = 100
HEAD_START_MS = 150

# kind -> (which eyes can see it, what the robot should do)
KINDS = {
    "cactus":    ("low",  "jump"),
    "bird_low":  ("low",  "jump"),
    "bird_mid":  ("head", "duck"),
    "bird_high": ("none", "nothing"),
}


def make_trace(name, seconds, speed_at, obstacles, night_times=()):
    """speed_at(ms) -> mm per second.
    obstacles: list of (ms when its front reaches eye A1, kind, width in mm).
    night_times: list of ms where a day/night fade starts."""
    rng = random.Random(name)
    total_ms = int(seconds * 1000)

    # How far the ground has scrolled by each millisecond.
    scrolled = [0.0]
    for ms in range(total_ms):
        scrolled.append(scrolled[-1] + speed_at(ms) / 1000.0)

    far_x = EYE_TO_DINO_MM + GAP_MM
    # Where each obstacle's front edge is at time 0.
    things = [(far_x + scrolled[ms], kind, width) for ms, kind, width in obstacles]

    def first_ms(start_x, target_x):
        """The first millisecond the front edge is at or past target_x."""
        for ms in range(total_ms + 1):
            if start_x - scrolled[ms] <= target_x:
                return ms
        return -1

    def night_amount(ms):
        """0 = day, 1 = night, in between during a fade. Each fade flips it."""
        amount = 0.0
        for i, start in enumerate(night_times):
            if ms < start:
                break
            progress = min(1.0, (ms - start) / FADE_MS)
            before = float(i % 2)
            amount = before + (1.0 - 2.0 * before) * progress
        return amount

    def covered(eye_x, eye_row, ms):
        """How much of this eye (0 to 1) is covered by an obstacle."""
        most = 0.0
        for start_x, kind, width in things:
            if KINDS[kind][0] != eye_row:
                continue
            front = start_x - scrolled[ms]
            overlap = min(front + width, eye_x + EYE_WIDTH_MM / 2) - max(front, eye_x - EYE_WIDTH_MM / 2)
            most = max(most, min(1.0, max(0.0, overlap / EYE_WIDTH_MM)))
        return most

    lines = ["# trace," + name + " (synthetic, from make_traces.py)"]
    lines.append("# settings,eye_to_dino_mm=%d,gap_mm=%d,dino_len_mm=%d,robot_delay_ms=%d,head_start_ms=%d"
                 % (EYE_TO_DINO_MM, GAP_MM, DINO_LEN_MM, ROBOT_DELAY_MS, HEAD_START_MS))
    for start in night_times:
        lines.append("# fade,%d,%d" % (start, start + FADE_MS))
    for start_x, kind, width in things:
        lines.append("# obstacle,%s,%s,%d,%d,%d,%d" % (
            kind, KINDS[kind][1],
            first_ms(start_x, far_x),                 # front reaches eye A1 (and A2)
            first_ms(start_x, EYE_TO_DINO_MM),        # front reaches eye A0
            first_ms(start_x, 0),                     # front reaches the dino's nose
            first_ms(start_x, -DINO_LEN_MM - width)))  # its tail clears the dino's tail
    lines.append("ms,a0,a1,a2")

    eyes = [(EYE_TO_DINO_MM, "low"), (far_x, "low"), (far_x, "head")]
    smooth = [float(DAY_BG)] * 3
    for ms in range(total_ms):
        night = night_amount(ms)
        bg = DAY_BG + (NIGHT_BG - DAY_BG) * night
        obj = DAY_OBJ + (NIGHT_OBJ - DAY_OBJ) * night
        for i, (eye_x, eye_row) in enumerate(eyes):
            target = bg + (obj - bg) * covered(eye_x, eye_row, ms)
            smooth[i] += (target - smooth[i]) / LAG_MS
        if ms % STEP_MS == 0:
            row = [max(0, min(1023, int(round(v + rng.uniform(-NOISE, NOISE))))) for v in smooth]
            lines.append("%d,%d,%d,%d" % (ms, row[0], row[1], row[2]))

    folder = os.path.join(os.path.dirname(os.path.abspath(__file__)), "traces")
    os.makedirs(folder, exist_ok=True)
    path = os.path.join(folder, name + ".csv")
    with open(path, "w") as out:
        out.write("\n".join(lines) + "\n")
    print("wrote", path, "(%d obstacles)" % len(things))


def spread(start_ms, end_ms, kinds_and_widths, min_gap=1300, max_gap=2100, seed=1):
    """Lay obstacles out between start and end with random gaps."""
    rng = random.Random(seed)
    out, ms, i = [], start_ms, 0
    while ms < end_ms:
        kind, width = kinds_and_widths[i % len(kinds_and_widths)]
        out.append((ms, kind, width))
        ms += rng.randint(min_gap, max_gap)
        i += 1
    return out


CACTI = [("cactus", 9), ("cactus", 13), ("cactus", 26), ("cactus", 17),
         ("cactus", 37), ("cactus", 9), ("cactus", 25)]

if __name__ == "__main__":
    # 1. A calm day at the starting speed (6 in the game = 180 mm/s at our pretend zoom).
    make_trace("day", 30, lambda ms: 180.0, spread(1500, 28000, CACTI, seed=11))

    # 2. Day, then night, then day again.
    night_obstacles = (spread(1500, 10500, CACTI, seed=21)
                       + spread(14500, 25000, CACTI, seed=22)
                       + spread(28500, 38000, CACTI, seed=23))
    make_trace("night_flip", 40, lambda ms: 180.0, night_obstacles, night_times=(12000, 26200))

    # 3. The game speeding up from 6 to 13 (180 to 390 mm/s) over a minute.
    make_trace("speeding_up", 60, lambda ms: 180.0 + 210.0 * ms / 60000.0,
               spread(1500, 58000, CACTI, min_gap=1300, max_gap=1900, seed=31))

    # 4. Birds at all three heights, at a speed where birds appear (9 = 270 mm/s).
    birds = [(1500, "cactus", 13), (3300, "bird_low", 23), (5200, "bird_mid", 23),
             (7100, "bird_high", 23), (8900, "cactus", 26), (10800, "bird_mid", 23),
             (12500, "bird_high", 23), (14200, "bird_low", 23), (16000, "bird_mid", 23),
             (16500, "cactus", 13),   # right behind a bird: jumping must win
             (19000, "bird_high", 23), (20700, "cactus", 17),
             (22500, "bird_mid", 23), (24300, "bird_low", 23)]
    make_trace("birds", 27, lambda ms: 270.0, birds)
