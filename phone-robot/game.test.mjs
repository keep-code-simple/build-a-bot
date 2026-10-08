// Tests for the Phone Robot's rules. Run from the project folder with:
//   node --test phone-robot/game.test.mjs
import test from "node:test";
import assert from "node:assert/strict";

import {
  MOVES, gestureToMove, majorityMove, winner, pickRobotMove, moveThatBeats, updateMatch, newRound,
} from "./game.js";

test("winner: all 9 combinations", () => {
  const expected = [
    ["rock", "rock", "tie"], ["rock", "paper", "robot"], ["rock", "scissors", "player"],
    ["paper", "rock", "player"], ["paper", "paper", "tie"], ["paper", "scissors", "robot"],
    ["scissors", "rock", "robot"], ["scissors", "paper", "player"], ["scissors", "scissors", "tie"],
  ];
  for (const [player, robot, result] of expected) {
    assert.equal(winner(player, robot), result, `${player} vs ${robot}`);
  }
});

test("gestureToMove: the three game gestures", () => {
  assert.equal(gestureToMove("Closed_Fist", 0.9), "rock");
  assert.equal(gestureToMove("Open_Palm", 0.9), "paper");
  assert.equal(gestureToMove("Victory", 0.9), "scissors");
  assert.equal(gestureToMove("Victory", 0.5), "scissors");      // exactly 0.5 is sure enough
});

test("gestureToMove: low scores and other gestures give null", () => {
  assert.equal(gestureToMove("Closed_Fist", 0.49), null);
  assert.equal(gestureToMove("Open_Palm", 0), null);
  assert.equal(gestureToMove("Victory", undefined), null);
  for (const other of ["Thumb_Up", "Thumb_Down", "Pointing_Up", "ILoveYou", "None", "", "toString"]) {
    assert.equal(gestureToMove(other, 0.99), null, other);
  }
});

test("majorityMove: a clear majority", () => {
  assert.equal(majorityMove(["rock", "rock", "rock", "rock"]), "rock");
  assert.equal(majorityMove(["paper", "paper", "rock", "paper", "paper"]), "paper");
});

test("majorityMove: a 50/50 split is unclear", () => {
  assert.equal(majorityMove(["rock", "rock", "paper", "paper"]), null);
  assert.equal(majorityMove(["rock", "paper", "scissors", "rock", "paper"]), null);
});

test("majorityMove: an empty window, or too few pictures", () => {
  assert.equal(majorityMove([]), null);
  assert.equal(majorityMove([null, null, null]), null);          // no hand at all
  assert.equal(majorityMove(["rock"]), null);                    // seen only once
  assert.equal(majorityMove(["rock", null, null, null]), null);
});

test("majorityMove: mixed pictures with nulls", () => {
  assert.equal(majorityMove([null, null, null, "scissors", "scissors"]), "scissors");   // a late hand still counts
  assert.equal(majorityMove(["rock", null, "rock", null, "paper"]), "rock");
  assert.equal(majorityMove([null, "rock", "paper", null]), null);
});

test("pickRobotMove: loaded dice give a known move", () => {
  assert.equal(pickRobotMove(() => 0), "rock");
  assert.equal(pickRobotMove(() => 0.34), "paper");
  assert.equal(pickRobotMove(() => 0.67), "scissors");
  assert.equal(pickRobotMove(() => 0.999999), "scissors");
  for (let i = 0; i < 50; i++) assert.ok(MOVES.includes(pickRobotMove()));   // real dice stay in range
});

test("moveThatBeats", () => {
  for (const move of MOVES) assert.equal(winner(moveThatBeats(move), move), "player");
});

test("the robot picks BEFORE the read window (the call log proves the order)", () => {
  const calls = [];
  const dice = () => { calls.push("robot rolled its dice"); return 0; };          // 0 = rock
  const round = newRound({ randomFn: dice, log: (line) => calls.push(line) });

  assert.throws(() => round.readPlayer("paper"), /must commit/);   // reading first is not allowed
  assert.deepEqual(calls, []);                                     // and the robot hasn't picked yet

  round.commit();
  assert.equal(round.sealed, true);
  assert.equal(round.robotMove, "rock");

  calls.push("read window opens");
  assert.equal(round.readPlayer("paper"), "player");
  assert.equal(round.robotMove, "rock");                           // seeing the player's move didn't change it
  assert.deepEqual(calls, [
    "robot rolled its dice",
    "robot committed: rock (sealed)",
    "read window opens",
    "player showed: paper -> player",
  ]);
});

test("cheat mode: the envelope is not sealed, and the robot always wins", () => {
  for (const move of MOVES) {
    const lines = [];
    const dice = () => { throw new Error("a cheating robot doesn't roll dice"); };
    const round = newRound({ cheats: true, randomFn: dice, log: (line) => lines.push(line) });
    round.commit();
    assert.equal(round.sealed, false);                             // the screen shows "?" instead of a lock
    assert.equal(round.robotMove, null);
    assert.equal(round.readPlayer(move), "robot");
    assert.match(lines[0], /CHEAT MODE/);
  }
});

test("updateMatch: first to 3, and ties don't count", () => {
  let state = { player: 0, robot: 0 };
  for (const result of ["player", "tie", "robot", "tie", "player"]) {
    state = updateMatch(state, result);
    assert.equal(state.over, false);
    assert.equal(state.matchWinner, null);
  }
  assert.deepEqual([state.player, state.robot], [2, 1]);
  state = updateMatch(state, "player");
  assert.deepEqual(state, { player: 3, robot: 1, over: true, matchWinner: "player" });

  let other = { player: 0, robot: 2 };
  other = updateMatch(other, "tie");
  assert.equal(other.over, false);
  other = updateMatch(other, "robot");
  assert.deepEqual(other, { player: 0, robot: 3, over: true, matchWinner: "robot" });
});

test("updateMatch does not change the state it was given", () => {
  const before = { player: 1, robot: 1 };
  updateMatch(before, "player");
  assert.deepEqual(before, { player: 1, robot: 1 });
});
