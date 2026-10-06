// Chapter 6: Dino Bot - the robot's brain
//
// Every decision the robot makes lives in this file: is that a cactus?
// how fast is the game? when should the finger press?
//
// There are NO Arduino calls in here. The time and the light readings are
// passed in as plain numbers, so exactly the same code runs
//   - on the UNO (dino_bot.ino calls dinoStep() over and over),
//   - on a computer (tests/replay_test.cpp replays recorded light traces),
//   - in the Dino Lab on the web page (a line-for-line JavaScript copy).
//
// Everything is whole-number math (no decimals), so all three get exactly
// the same answers.
#ifndef DINO_LOGIC_H
#define DINO_LOGIC_H

#include <stdint.h>

// ---- Fine tuning (you should not need to change these) ----
const int32_t DINO_BASE_MS        = 80;    // how quickly "normal light" follows slow changes
const int32_t DINO_STUCK_MS       = 400;   // "different" for this long = the whole screen changed
const int32_t DINO_SETTLE_MS      = 150;   // ignore the eye this long after normal moved fast
const int32_t DINO_RATE_MS        = 50;    // how often to check if normal is moving fast
const int32_t DINO_TRAP_MIN_MS    = 20;    // speed trap: faster than this is a glitch
const int32_t DINO_TRAP_MAX_MS    = 1500;  // speed trap: slower than this is a glitch
const int32_t DINO_SWAP_MS        = 60;    // pause between one finger lifting and the other pressing
const int32_t DINO_DUCK_MARGIN_MS = 250;  // stay ducked a little longer, to be safe
const int32_t DINO_DUCK_GUESS_MS  = 500;   // bird travel time when the speed is not known yet

// The settings from the top of dino_bot.ino, bundled together.
struct DinoSettings {
  int32_t level;          // 1, 2, 3 or 4
  int32_t threshold;      // Level 1: light below this = cactus
  int32_t bigChange;      // Level 2+: this far away from normal = something is there
  int32_t pressMs;        // how long the finger holds the key
  int32_t cooldownMs;     // after a jump, ignore the eye for this long
  int32_t sensorGapMm;    // speed trap: millimeters between eye A1 and eye A0
  int32_t eyeToDinoMm;    // millimeters from eye A0 to the dino's nose
  int32_t headStartMs;    // start the jump this long before the cactus arrives
  int32_t robotDelayMs;   // the robot's own delay (finger travel)
  int32_t maxRunMs;       // safety stop: no more pressing after this long (0 = never stop)
};

// One eye's memory.
struct DinoEye {
  bool ready;             // has it had its first reading yet?
  int32_t base256;        // "normal light" times 256 (keeps the fractions without decimals)
  bool seeing;            // is something different in front of the eye right now?
  bool counts;            // false = it showed up while normal was moving, so ignore it
  int32_t seeSince;       // when "seeing" started
  int32_t refBase256;     // normal light at the last rate check
  int32_t refAt;          // when the last rate check was
  int32_t settleUntil;    // ignore the eye until this time
  int32_t lastMs;         // time of the previous reading
};

// The whole brain's memory.
struct DinoBrain {
  bool started;
  bool stopped;           // true once the safety stop has kicked in
  int32_t startMs;
  DinoEye low;            // A0: cactus height, near the dino
  DinoEye far;            // A1: cactus height, farther ahead (speed trap)
  DinoEye head;           // A2: head height (birds)
  bool lowWas;            // what the low eye said last time (to spot the moment it changes)
  bool farWas;
  // the jump finger
  bool jumpDown;
  bool jumpPlanned;
  int32_t jumpAt;         // when the planned press should start
  int32_t jumpUpAt;       // when to let go
  int32_t jumpReleasedAt;
  int32_t lastJumpAt;
  int32_t jumpCount;
  // the speed trap
  bool trapArmed;         // the far eye saw something; waiting for the near eye
  bool warned;            // a jump was already planned from the far eye
  int32_t farSeenAt;
  int32_t trapMs;         // time to cross the gap between the eyes (0 = not measured yet)
  int32_t predictedArriveAt;  // when the brain thinks the obstacle reaches the dino
  // the duck finger
  bool duckDown;
  bool duckActive;
  int32_t duckUntil;
  int32_t duckReleasedAt;
  int32_t duckCount;
};

// What the brain wants the fingers to do right now.
struct DinoKeys {
  bool jump;              // jump finger down?
  bool duck;              // duck finger down?
  bool jumpStarted;       // true only on the step a new jump press begins
  bool duckStarted;       // true only on the step a new duck press begins
  bool lowSees;           // the low eye sees something (handy for a debug light)
};

static inline int32_t dinoAbs(int32_t v) {
  return v < 0 ? -v : v;
}

static inline void dinoEyeReset(DinoEye &e) {
  e.ready = false;
  e.base256 = 0;
  e.seeing = false;
  e.counts = false;
  e.seeSince = 0;
  e.refBase256 = 0;
  e.refAt = 0;
  e.settleUntil = 0;
  e.lastMs = 0;
}

static inline void dinoBrainReset(DinoBrain &b) {
  b.started = false;
  b.stopped = false;
  b.startMs = 0;
  dinoEyeReset(b.low);
  dinoEyeReset(b.far);
  dinoEyeReset(b.head);
  b.lowWas = false;
  b.farWas = false;
  b.jumpDown = false;
  b.jumpPlanned = false;
  b.jumpAt = 0;
  b.jumpUpAt = 0;
  b.jumpReleasedAt = 0;
  b.lastJumpAt = 0;
  b.jumpCount = 0;
  b.trapArmed = false;
  b.warned = false;
  b.farSeenAt = 0;
  b.trapMs = 0;
  b.predictedArriveAt = 0;
  b.duckDown = false;
  b.duckActive = false;
  b.duckUntil = 0;
  b.duckReleasedAt = 0;
  b.duckCount = 0;
}

// LEVEL 2 EYE: learn what normal looks like, then notice anything different.
// Returns true while something is in front of the eye.
static inline bool dinoEyeUpdate(DinoEye &e, int32_t light, int32_t now, int32_t bigChange) {
  if (!e.ready) {                       // first reading: this is our first idea of normal
    e.ready = true;
    e.base256 = light * 256;
    e.refBase256 = e.base256;
    e.refAt = now;
    e.settleUntil = now;
    e.lastMs = now;
    return false;
  }
  int32_t dt = now - e.lastMs;
  e.lastMs = now;
  int32_t diff = dinoAbs(light - e.base256 / 256);   // how far from normal? (darker OR brighter)

  if (e.seeing) {
    if (diff * 2 < bigChange) {
      e.seeing = false;                 // back to normal: it has gone past
    } else if (now - e.seeSince > DINO_STUCK_MS) {
      e.base256 = light * 256;          // too long to be a cactus: the whole screen changed,
      e.seeing = false;                 // so this is the new normal
      e.settleUntil = now + DINO_SETTLE_MS;
    }
  } else if (diff > bigChange) {
    e.seeing = true;                    // something different just showed up
    e.seeSince = now;
    e.counts = now >= e.settleUntil;    // ...but don't trust it if normal was just moving
  } else {
    // Nothing there: slide normal a little toward what we see now.
    // (Normal is frozen while something is passing, so a cactus can't drag it down.)
    e.base256 += (light * 256 - e.base256) * dt / (DINO_BASE_MS + dt);
  }

  // Is normal moving fast (the fade between day and night)? Then don't trust the eye for a moment.
  if (now - e.refAt >= DINO_RATE_MS) {
    if (dinoAbs(e.base256 - e.refBase256) > bigChange * 64) {
      e.settleUntil = now + DINO_SETTLE_MS;
    }
    e.refBase256 = e.base256;
    e.refAt = now;
  }
  return e.seeing && e.counts;
}

// LEVEL 3 SPEED TRAP: if crossing the gap between the eyes took trapMs,
// how long will it take to travel distanceMm?
static inline int32_t dinoTravelMs(int32_t trapMs, int32_t distanceMm, int32_t gapMm) {
  if (gapMm <= 0) return 0;
  return trapMs * distanceMm / gapMm;
}

// Ask for a jump press at time "at". If one is already planned, the earlier one wins.
static inline void dinoPlanJump(DinoBrain &b, int32_t at) {
  if (!b.jumpPlanned || at < b.jumpAt) {
    b.jumpPlanned = true;
    b.jumpAt = at;
  }
}

// One tick of the brain: SENSE, THINK, ACT.
// now = time in milliseconds. a0, a1, a2 = light readings (0 to 1023).
static inline DinoKeys dinoStep(DinoBrain &b, const DinoSettings &s, int32_t now,
                                int32_t a0, int32_t a1, int32_t a2) {
  DinoKeys keys;
  keys.jump = false;
  keys.duck = false;
  keys.jumpStarted = false;
  keys.duckStarted = false;
  keys.lowSees = false;

  if (!b.started) {
    b.started = true;
    b.startMs = now;
    b.lastJumpAt = now - 100000;
    b.jumpReleasedAt = now - 100000;
    b.duckReleasedAt = now - 100000;
  }

  // SAFETY STOP: after maxRunMs, lift both fingers and stay off.
  if (s.maxRunMs > 0 && now - b.startMs >= s.maxRunMs) {
    b.stopped = true;
    b.jumpDown = false;
    b.duckDown = false;
    b.jumpPlanned = false;
    b.duckActive = false;
    return keys;
  }

  // ---- 1. SENSE: what do the eyes see? ----
  bool lowSees = false;
  bool farSees = false;
  bool headSees = false;
  if (s.level <= 1) {
    lowSees = a0 < s.threshold;                              // Level 1: dark = cactus
  } else {
    lowSees = dinoEyeUpdate(b.low, a0, now, s.bigChange);    // Level 2+: different = cactus
  }
  if (s.level >= 3) farSees = dinoEyeUpdate(b.far, a1, now, s.bigChange);
  if (s.level >= 4) headSees = dinoEyeUpdate(b.head, a2, now, s.bigChange);
  bool lowEdge = lowSees && !b.lowWas;    // "edge" = the moment it first shows up
  bool farEdge = farSees && !b.farWas;
  b.lowWas = lowSees;
  b.farWas = farSees;
  keys.lowSees = lowSees;

  // ---- 2. THINK: should we jump, and when? ----
  bool cooled = now - b.lastJumpAt >= s.cooldownMs;
  int32_t early = s.headStartMs + s.robotDelayMs;   // how far ahead of the cactus the press must start
  if (s.level <= 1) {
    if (lowSees && cooled) dinoPlanJump(b, now);    // Level 1: dark? press now!
  } else if (s.level == 2) {
    if (lowEdge && cooled) dinoPlanJump(b, now);    // Level 2: different? press now!
  } else {
    // Level 3+: the far eye gives an early warning.
    if (farEdge) {
      b.trapArmed = true;                 // start the speed-trap stopwatch
      b.farSeenAt = now;
      b.warned = false;
      if (b.trapMs > 0) {                 // we know the speed from the last cactus: plan ahead
        b.predictedArriveAt = now + dinoTravelMs(b.trapMs, s.sensorGapMm + s.eyeToDinoMm, s.sensorGapMm);
        dinoPlanJump(b, b.predictedArriveAt - early);
        b.warned = true;
      }
    }
    if (b.trapArmed && now - b.farSeenAt > DINO_TRAP_MAX_MS) {
      b.trapArmed = false;                // it never reached the near eye: forget it
      b.warned = false;
    }
    if (lowEdge) {
      if (b.trapArmed) {                  // stop the stopwatch: that is the speed
        int32_t gapMs = now - b.farSeenAt;
        if (gapMs >= DINO_TRAP_MIN_MS) b.trapMs = gapMs;
        b.trapArmed = false;
      }
      if (b.trapMs > 0) {
        int32_t arrive = now + dinoTravelMs(b.trapMs, s.eyeToDinoMm, s.sensorGapMm);
        if (b.warned) {
          if (b.jumpPlanned) {            // not pressed yet: fix the plan with the fresh speed
            b.predictedArriveAt = arrive;
            b.jumpAt = arrive - early;
          }
        } else if (cooled) {              // no early warning: plan from here
          b.predictedArriveAt = arrive;
          dinoPlanJump(b, arrive - early);
        }
      } else if (cooled) {
        dinoPlanJump(b, now);             // speed not known yet: just react, like Level 2
      }
      b.warned = false;
    }
  }

  // ---- 3. ACT: move the fingers (never both at once) ----
  if (b.jumpDown && now >= b.jumpUpAt) {  // held long enough: let go
    b.jumpDown = false;
    b.jumpReleasedAt = now;
  }
  bool jumpDue = b.jumpPlanned && now >= b.jumpAt;
  if (jumpDue) {
    if (b.duckDown) {                     // jumping wins: lift the duck finger first
      b.duckDown = false;
      b.duckActive = false;
      b.duckReleasedAt = now;
    } else if (!b.jumpDown && now - b.duckReleasedAt >= DINO_SWAP_MS) {
      b.jumpDown = true;                  // PRESS!
      b.jumpUpAt = now + s.pressMs;
      b.lastJumpAt = now;
      b.jumpPlanned = false;
      b.jumpCount++;
      keys.jumpStarted = true;
      jumpDue = false;
    }
  }

  if (s.level >= 4) {
    // Level 4: head eye sees something but the low eyes are clear = a middle bird. Duck!
    if (headSees && !lowSees && !farSees) {
      int32_t pass = DINO_DUCK_GUESS_MS;
      if (b.trapMs > 0) pass = dinoTravelMs(b.trapMs, s.sensorGapMm + s.eyeToDinoMm, s.sensorGapMm);
      b.duckActive = true;                // stay down until the bird is past the dino
      b.duckUntil = now + pass + DINO_DUCK_MARGIN_MS;
    }
    if (b.duckActive && now >= b.duckUntil) b.duckActive = false;
    if (b.duckDown && !b.duckActive) {
      b.duckDown = false;
      b.duckReleasedAt = now;
    }
    if (b.duckActive && !b.duckDown && !b.jumpDown && !jumpDue
        && now - b.jumpReleasedAt >= DINO_SWAP_MS) {
      b.duckDown = true;                  // DUCK!
      b.duckCount++;
      keys.duckStarted = true;
    }
  }

  keys.jump = b.jumpDown;
  keys.duck = b.duckDown;
  return keys;
}

#endif
