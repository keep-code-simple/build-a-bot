// Chapter 6: Dino Bot - test the robot's brain on a computer, no robot needed.
//
// This compiles the very same dino_logic.h the UNO uses, feeds it light
// traces (CSV files), and checks the brain pressed the right keys.
//
// Build and run from this folder (the program goes in /tmp, not in the project):
//
//   c++ -std=c++11 -Wall -Wextra -o /tmp/replay_test replay_test.cpp && /tmp/replay_test
//
// Other ways to run it:
//   /tmp/replay_test traces                        run all the checks (same as no arguments)
//   /tmp/replay_test --replay traces/my_screen.csv show what each level does with YOUR recording
//   /tmp/replay_test --dump traces/day.csv 2       print every key press, row by row (Level 2)
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <string>
#include <vector>

#include "../dino_bot/dino_logic.h"

struct Obstacle {
  std::string kind;     // cactus, bird_low, bird_mid, bird_high
  std::string action;   // jump, duck, nothing
  int32_t farMs, lowMs, arriveMs, leaveMs;
};
struct Row { int32_t ms, a0, a1, a2; };
struct Trace {
  std::string name;
  std::vector<Row> rows;
  std::vector<Obstacle> obstacles;
  std::vector<int32_t> fadeStart, fadeEnd;
  int32_t eyeToDinoMm, gapMm, dinoLenMm, robotDelayMs, headStartMs;
};
struct Jump { int32_t ms; int32_t predictedArriveAt; };
struct Hold { int32_t downMs, upMs; };
struct Result {
  std::vector<Jump> jumps;
  std::vector<Hold> ducks;
  std::vector<Hold> presses;   // how long the jump finger was down each time
  int bothDown;                // rows where both fingers were down (must be 0)
  bool stopped;
};

static int passed = 0, failed = 0;

static void check(bool ok, const char *what) {
  std::printf("  %s  %s\n", ok ? "PASS" : "FAIL", what);
  if (ok) passed++; else failed++;
}

static std::vector<std::string> split(const std::string &line) {
  std::vector<std::string> parts;
  std::string part;
  for (size_t i = 0; i < line.size(); i++) {
    char c = line[i];
    if (c == ',') { parts.push_back(part); part.clear(); }
    else if (c != '\r' && c != '\n') part += c;
  }
  parts.push_back(part);
  return parts;
}

static int32_t setting(const std::vector<std::string> &parts, const char *name, int32_t fallback) {
  std::string key = std::string(name) + "=";
  for (size_t i = 0; i < parts.size(); i++) {
    if (parts[i].compare(0, key.size(), key) == 0) return std::atoi(parts[i].c_str() + key.size());
  }
  return fallback;
}

static bool loadTrace(const std::string &path, Trace &t) {
  std::FILE *f = std::fopen(path.c_str(), "r");
  if (!f) { std::printf("Could not open %s\n", path.c_str()); return false; }
  t.name = path;
  t.eyeToDinoMm = 55; t.gapMm = 50; t.dinoLenMm = 20; t.robotDelayMs = 100; t.headStartMs = 150;
  char buf[512];
  while (std::fgets(buf, sizeof buf, f)) {
    std::string line(buf);
    if (line.size() < 2) continue;
    if (line[0] == '#') {
      std::vector<std::string> p = split(line.substr(2));
      if (p[0] == "settings") {
        t.eyeToDinoMm = setting(p, "eye_to_dino_mm", t.eyeToDinoMm);
        t.gapMm = setting(p, "gap_mm", t.gapMm);
        t.dinoLenMm = setting(p, "dino_len_mm", t.dinoLenMm);
        t.robotDelayMs = setting(p, "robot_delay_ms", t.robotDelayMs);
        t.headStartMs = setting(p, "head_start_ms", t.headStartMs);
      } else if (p[0] == "fade" && p.size() >= 3) {
        t.fadeStart.push_back(std::atoi(p[1].c_str()));
        t.fadeEnd.push_back(std::atoi(p[2].c_str()));
      } else if (p[0] == "obstacle" && p.size() >= 7) {
        Obstacle o;
        o.kind = p[1]; o.action = p[2];
        o.farMs = std::atoi(p[3].c_str()); o.lowMs = std::atoi(p[4].c_str());
        o.arriveMs = std::atoi(p[5].c_str()); o.leaveMs = std::atoi(p[6].c_str());
        t.obstacles.push_back(o);
      }
      continue;
    }
    if (line[0] < '0' || line[0] > '9') continue;      // the "ms,a0,a1,a2" heading
    std::vector<std::string> p = split(line);
    if (p.size() < 2) continue;
    Row r;
    r.ms = std::atoi(p[0].c_str());
    r.a0 = std::atoi(p[1].c_str());
    r.a1 = p.size() > 2 ? std::atoi(p[2].c_str()) : r.a0;
    r.a2 = p.size() > 3 ? std::atoi(p[3].c_str()) : r.a0;
    t.rows.push_back(r);
  }
  std::fclose(f);
  return !t.rows.empty();
}

static DinoSettings settingsFor(const Trace &t, int level) {
  DinoSettings s;
  s.level = level;
  s.threshold = 540;        // halfway between the trace's "white" (820) and "cactus" (260)
  s.bigChange = 120;
  s.pressMs = 80;
  s.cooldownMs = 300;
  s.sensorGapMm = t.gapMm;
  s.eyeToDinoMm = t.eyeToDinoMm;
  s.headStartMs = t.headStartMs;
  s.robotDelayMs = t.robotDelayMs;
  s.maxRunMs = 0;
  return s;
}

static Result run(const Trace &t, const DinoSettings &s, bool dump) {
  Result r;
  r.bothDown = 0;
  DinoBrain brain;
  dinoBrainReset(brain);
  bool jumpWas = false, duckWas = false;
  if (dump) std::printf("ms,jump,duck\n");
  for (size_t i = 0; i < t.rows.size(); i++) {
    const Row &row = t.rows[i];
    DinoKeys k = dinoStep(brain, s, row.ms, row.a0, row.a1, row.a2);
    if (dump) std::printf("%d,%d,%d\n", (int)row.ms, k.jump ? 1 : 0, k.duck ? 1 : 0);
    if (k.jumpStarted) { Jump j; j.ms = row.ms; j.predictedArriveAt = brain.predictedArriveAt; r.jumps.push_back(j); }
    if (k.jump && !jumpWas) { Hold h; h.downMs = row.ms; h.upMs = -1; r.presses.push_back(h); }
    if (!k.jump && jumpWas) r.presses.back().upMs = row.ms;
    if (k.duck && !duckWas) { Hold h; h.downMs = row.ms; h.upMs = -1; r.ducks.push_back(h); }
    if (!k.duck && duckWas) r.ducks.back().upMs = row.ms;
    if (k.jump && k.duck) r.bothDown++;
    jumpWas = k.jump;
    duckWas = k.duck;
  }
  r.stopped = brain.stopped;
  if (dump) std::printf("jumps=%d ducks=%d\n", (int)brain.jumpCount, (int)brain.duckCount);
  return r;
}

// How many jump presses started while this obstacle was anywhere between the far eye and the dino's tail?
static int jumpsFor(const Result &r, const Obstacle &o, int32_t *firstMs, int32_t *predicted) {
  int n = 0;
  for (size_t i = 0; i < r.jumps.size(); i++) {
    if (r.jumps[i].ms >= o.farMs - 30 && r.jumps[i].ms <= o.leaveMs) {
      if (n == 0) { if (firstMs) *firstMs = r.jumps[i].ms; if (predicted) *predicted = r.jumps[i].predictedArriveAt; }
      n++;
    }
  }
  return n;
}

static int countAction(const Trace &t, const char *action) {
  int n = 0;
  for (size_t i = 0; i < t.obstacles.size(); i++) if (t.obstacles[i].action == action) n++;
  return n;
}

// "One jump per obstacle, never two, and none when the screen is clear."
static bool oneJumpEach(const Trace &t, const Result &r) {
  int expected = 0;
  for (size_t i = 0; i < t.obstacles.size(); i++) {
    const Obstacle &o = t.obstacles[i];
    int n = jumpsFor(r, o, 0, 0);
    if (o.action == "jump") { expected++; if (n != 1) return false; }
    else if (o.action == "nothing" && n != 0) return false;
  }
  return (int)r.jumps.size() == expected;
}

static bool duckHeldDuring(const Result &r, int32_t fromMs, int32_t toMs) {
  for (size_t i = 0; i < r.ducks.size(); i++) {
    int32_t up = r.ducks[i].upMs < 0 ? 2000000000 : r.ducks[i].upMs;
    if (r.ducks[i].downMs <= fromMs && up >= toMs) return true;
  }
  return false;
}

static void testDay(const std::string &dir) {
  std::printf("\nDAY: a calm day at the starting speed\n");
  Trace t;
  if (!loadTrace(dir + "/day.csv", t)) { check(false, "day.csv loads"); return; }
  for (int level = 1; level <= 4; level++) {
    Result r = run(t, settingsFor(t, level), false);
    char what[160];
    std::snprintf(what, sizeof what, "Level %d: one jump per cactus (%d cacti, %d jumps), none on a clear screen",
                  level, countAction(t, "jump"), (int)r.jumps.size());
    check(oneJumpEach(t, r), what);
    std::snprintf(what, sizeof what, "Level %d: never ducks on a day with no birds", level);
    check(r.ducks.empty(), what);
  }
}

static void testNight(const std::string &dir) {
  std::printf("\nNIGHT FLIP: day, then night, then day again\n");
  Trace t;
  if (!loadTrace(dir + "/night_flip.csv", t)) { check(false, "night_flip.csv loads"); return; }
  int cacti = countAction(t, "jump");
  char what[200];

  Result r1 = run(t, settingsFor(t, 1), false);
  int nightJumps = 0;
  for (size_t i = 0; i < r1.jumps.size(); i++) {
    if (r1.jumps[i].ms >= t.fadeEnd[0] && r1.jumps[i].ms < t.fadeStart[1]) nightJumps++;
  }
  std::snprintf(what, sizeof what,
                "Level 1 FAILS at night, as expected: %d jumps for %d cacti (%d of them in the dark)",
                (int)r1.jumps.size(), cacti, nightJumps);
  check((int)r1.jumps.size() > 2 * cacti && nightJumps > 20, what);

  for (int level = 2; level <= 4; level++) {
    Result r = run(t, settingsFor(t, level), false);
    std::snprintf(what, sizeof what, "Level %d: exactly one jump per obstacle across the flip (%d cacti, %d jumps)",
                  level, cacti, (int)r.jumps.size());
    check(oneJumpEach(t, r), what);
    int inFade = 0;
    for (size_t i = 0; i < r.jumps.size(); i++) {
      for (size_t f = 0; f < t.fadeStart.size(); f++) {
        if (r.jumps[i].ms >= t.fadeStart[f] && r.jumps[i].ms <= t.fadeEnd[f] + 400) inFade++;
      }
    }
    std::snprintf(what, sizeof what, "Level %d: no jumps while the screen is fading", level);
    check(inFade == 0, what);
  }
}

static void testSpeed(const std::string &dir) {
  std::printf("\nSPEEDING UP: from speed 6 to speed 13 in one minute\n");
  Trace t;
  if (!loadTrace(dir + "/speeding_up.csv", t)) { check(false, "speeding_up.csv loads"); return; }
  char what[220];
  DinoSettings s3 = settingsFor(t, 3);
  Result r3 = run(t, s3, false);
  std::snprintf(what, sizeof what, "Level 3: one jump per cactus (%d cacti, %d jumps)",
                countAction(t, "jump"), (int)r3.jumps.size());
  check(oneJumpEach(t, r3), what);

  // When does each press start, compared to the moment the cactus passes eye A0?
  // (The first cactus is skipped: the trap has not measured a speed yet.)
  std::vector<int32_t> offset, lead;
  bool predictionOk = true, timingOk = true;
  int32_t worstPercent = 0, worstTiming = 0;
  for (size_t i = 1; i < t.obstacles.size(); i++) {
    const Obstacle &o = t.obstacles[i];
    int32_t start = 0, predicted = 0;
    if (jumpsFor(r3, o, &start, &predicted) != 1) continue;
    offset.push_back(start - o.lowMs);
    lead.push_back(o.arriveMs - (start + s3.robotDelayMs));
    int32_t trip = o.arriveMs - o.farMs;                 // the true trip from the far eye to the dino
    int32_t error = dinoAbs(predicted - o.arriveMs);
    int32_t percent = error * 100 / trip;
    if (percent > worstPercent) worstPercent = percent;
    if (error * 100 > trip * 15) predictionOk = false;
    int32_t timing = dinoAbs(o.arriveMs - (start + s3.robotDelayMs) - s3.headStartMs);
    if (timing > worstTiming) worstTiming = timing;
    if (timing > 40) timingOk = false;
  }
  size_t n = offset.size();
  long firstAvg = 0, lastAvg = 0;
  for (size_t i = 0; i < 5 && i < n; i++) { firstAvg += offset[i]; lastAvg += offset[n - 1 - i]; }
  firstAvg /= 5; lastAvg /= 5;
  std::snprintf(what, sizeof what,
                "Level 3: the press starts earlier as the game speeds up (%ld ms after eye A0 at first, %ld ms at the end)",
                firstAvg, lastAvg);
  check(n >= 10 && lastAvg < firstAvg - 50, what);
  std::snprintf(what, sizeof what, "Level 3: predicted arrival within 15%% of the true arrival (worst: %d%%)",
                (int)worstPercent);
  check(n >= 10 && predictionOk, what);
  std::snprintf(what, sizeof what,
                "Level 3: every jump begins %d ms before the cactus arrives, give or take 40 ms (worst miss: %d ms)",
                (int)s3.headStartMs, (int)worstTiming);
  check(n >= 10 && timingOk, what);

  // The lesson: Level 2 only reacts, so its head start shrinks as the game gets faster.
  DinoSettings s2 = settingsFor(t, 2);
  Result r2 = run(t, s2, false);
  int32_t firstLead = 0, lastLead = 0, start = 0;
  if (jumpsFor(r2, t.obstacles[1], &start, 0) == 1) firstLead = t.obstacles[1].arriveMs - (start + s2.robotDelayMs);
  if (jumpsFor(r2, t.obstacles.back(), &start, 0) == 1) lastLead = t.obstacles.back().arriveMs - (start + s2.robotDelayMs);
  std::snprintf(what, sizeof what,
                "Level 2 runs out of time, as expected: its head start shrinks from %d ms to %d ms",
                (int)firstLead, (int)lastLead);
  check(lastLead < firstLead - 80 && lastLead < s2.headStartMs - 60, what);
}

static void testBirds(const std::string &dir) {
  std::printf("\nBIRDS: low, middle and high birds mixed with cacti\n");
  Trace t;
  if (!loadTrace(dir + "/birds.csv", t)) { check(false, "birds.csv loads"); return; }
  char what[200];
  DinoSettings s = settingsFor(t, 4);
  Result r = run(t, s, false);

  bool lowOk = true, midOk = true, highOk = true, swapOk = false;
  for (size_t i = 0; i < t.obstacles.size(); i++) {
    const Obstacle &o = t.obstacles[i];
    int jumps = jumpsFor(r, o, 0, 0);
    if (o.kind == "bird_low" && jumps != 1) lowOk = false;
    if (o.kind == "bird_high") {
      if (jumps != 0) highOk = false;
      for (size_t d = 0; d < r.ducks.size(); d++) {
        if (r.ducks[d].downMs >= o.farMs - 30 && r.ducks[d].downMs <= o.leaveMs) highOk = false;
      }
    }
    // A middle bird: the duck key must be down the whole time the bird is over the dino
    // (and early enough to cover the robot's own delay).
    if (o.kind == "bird_mid" && !duckHeldDuring(r, o.arriveMs - s.robotDelayMs, o.leaveMs)) midOk = false;
  }
  check(lowOk, "Level 4: low bird -> jump");
  check(midOk, "Level 4: middle bird -> duck, and stay down until it has passed");
  check(highOk, "Level 4: high bird -> do nothing");
  std::snprintf(what, sizeof what, "Level 4: one jump for each cactus and low bird (%d expected, %d jumps)",
                countAction(t, "jump"), (int)r.jumps.size());
  check(oneJumpEach(t, r), what);
  std::snprintf(what, sizeof what, "Level 4: one duck for each middle bird (%d expected, %d ducks)",
                countAction(t, "duck"), (int)r.ducks.size());
  check((int)r.ducks.size() == countAction(t, "duck"), what);
  check(r.bothDown == 0, "Level 4: jump and duck are never down at the same time");

  // One cactus arrives right behind a middle bird: the duck must be let go BEFORE the jump.
  for (size_t d = 0; d < r.ducks.size(); d++) {
    for (size_t j = 0; j < r.jumps.size(); j++) {
      int32_t wait = r.jumps[j].ms - r.ducks[d].upMs;
      if (r.ducks[d].upMs > 0 && wait >= DINO_SWAP_MS && wait <= DINO_SWAP_MS + 10) swapOk = true;
    }
  }
  check(swapOk, "Level 4: jumping wins, and the duck finger lifts first");

  Result r3 = run(t, settingsFor(t, 3), false);
  check(r3.ducks.empty(), "Level 3 never ducks (it has no duck finger): middle birds will get it");
}

static void testRules(const std::string &dir) {
  std::printf("\nRULES: cooldown, hold time and the safety stop\n");
  Trace t;
  if (!loadTrace(dir + "/day.csv", t)) { check(false, "day.csv loads"); return; }
  char what[200];

  // Safety stop: nothing is pressed after maxRunMs.
  DinoSettings s = settingsFor(t, 2);
  s.maxRunMs = 10000;
  Result r = run(t, s, false);
  bool quiet = !r.jumps.empty();
  for (size_t i = 0; i < r.jumps.size(); i++) if (r.jumps[i].ms >= 10000) quiet = false;
  check(quiet && r.stopped, "Safety stop: no presses after the time limit");

  // The finger holds the key for pressMs, then lets go.
  Result r1 = run(t, settingsFor(t, 1), false);
  bool holdOk = !r1.presses.empty();
  for (size_t i = 0; i < r1.presses.size(); i++) {
    int32_t held = r1.presses[i].upMs - r1.presses[i].downMs;
    if (held < 80 || held > 90) holdOk = false;
  }
  check(holdOk, "Each press holds the key for PRESS_MS (80 ms), then lets go");

  // Level 1 in the dark: a jump every cooldown, forever.
  Trace dark;
  for (int ms = 0; ms < 3000; ms += 5) { Row row; row.ms = ms; row.a0 = row.a1 = row.a2 = 140; dark.rows.push_back(row); }
  dark.eyeToDinoMm = 55; dark.gapMm = 50; dark.dinoLenMm = 20; dark.robotDelayMs = 100; dark.headStartMs = 150;
  Result rd = run(dark, settingsFor(dark, 1), false);
  std::snprintf(what, sizeof what, "Level 1 in the dark jumps once per cooldown (%d jumps in 3 seconds)", (int)rd.jumps.size());
  check(rd.jumps.size() == 10, what);

  // Level 2 when the screen flips in an instant (no fade): at most one mistake, then it adapts.
  Trace flip;
  for (int ms = 0; ms < 6000; ms += 5) { Row row; row.ms = ms; row.a0 = row.a1 = row.a2 = (ms < 2000 ? 820 : 140); flip.rows.push_back(row); }
  flip.eyeToDinoMm = 55; flip.gapMm = 50; flip.dinoLenMm = 20; flip.robotDelayMs = 100; flip.headStartMs = 150;
  Result rf = run(flip, settingsFor(flip, 2), false);
  std::snprintf(what, sizeof what, "Level 2 with an instant flip: at most one false jump, then it learns the new normal (%d)", (int)rf.jumps.size());
  check(rf.jumps.size() <= 1, what);

  // Level 2 when the screen fades quickly (a third of a second): normal is moving fast,
  // so the eye must not be trusted until it settles. No jumps at all.
  Trace fade;
  for (int ms = 0; ms < 6000; ms += 5) {
    Row row;
    row.ms = ms;
    row.a0 = ms < 2000 ? 820 : (ms < 2300 ? 820 - (ms - 2000) * 680 / 300 : 140);
    row.a1 = row.a2 = row.a0;
    fade.rows.push_back(row);
  }
  fade.eyeToDinoMm = 55; fade.gapMm = 50; fade.dinoLenMm = 20; fade.robotDelayMs = 100; fade.headStartMs = 150;
  Result rq = run(fade, settingsFor(fade, 2), false);
  std::snprintf(what, sizeof what, "Level 2 with a quick fade: the eye is ignored while normal is moving (%d jumps)", (int)rq.jumps.size());
  check(rq.jumps.empty(), what);

  check(dinoTravelMs(200, 50, 50) == 200 && dinoTravelMs(200, 100, 50) == 400 && dinoTravelMs(200, 55, 0) == 0,
        "Speed trap maths: twice the distance takes twice the time");
}

// For the family's own recordings: there is no answer key, so just show what each level does.
static int replay(const std::string &path) {
  Trace t;
  if (!loadTrace(path, t)) return 1;
  std::printf("%s: %d rows, %.1f seconds\n", path.c_str(), (int)t.rows.size(),
              (t.rows.back().ms - t.rows.front().ms) / 1000.0);
  for (int level = 1; level <= 4; level++) {
    Result r = run(t, settingsFor(t, level), false);
    std::printf("Level %d: %d jumps, %d ducks. Jumps at (seconds):", level, (int)r.jumps.size(), (int)r.ducks.size());
    for (size_t i = 0; i < r.jumps.size() && i < 40; i++) std::printf(" %.2f", r.jumps[i].ms / 1000.0);
    if (r.jumps.size() > 40) std::printf(" ...");
    std::printf("\n");
  }
  std::printf("Count the cacti in your recording. Does each level jump once for each?\n");
  return 0;
}

int main(int argc, char **argv) {
  if (argc >= 3 && std::strcmp(argv[1], "--replay") == 0) return replay(argv[2]);
  if (argc >= 4 && std::strcmp(argv[1], "--dump") == 0) {
    Trace t;
    if (!loadTrace(argv[2], t)) return 1;
    run(t, settingsFor(t, std::atoi(argv[3])), true);
    return 0;
  }
  std::string dir = argc >= 2 ? argv[1] : "traces";
  std::printf("Dino Bot brain tests (traces from %s)\n", dir.c_str());
  testDay(dir);
  testNight(dir);
  testSpeed(dir);
  testBirds(dir);
  testRules(dir);
  std::printf("\n%d passed, %d failed\n", passed, failed);
  return failed == 0 ? 0 : 1;
}
