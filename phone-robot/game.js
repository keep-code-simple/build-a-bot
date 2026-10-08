// The Phone Robot: the rules of Rock Paper Scissors.
// No camera, no AI and no screen in this file, just thinking.
// That makes the rules easy to read, and easy to test (see game.test.mjs).

export const MOVES = ["rock", "paper", "scissors"];
export const BEATS = { rock: "scissors", paper: "rock", scissors: "paper" };   // rock beats scissors...

// The AI already knows these gestures. We turn them into game moves.
export const GESTURE_TO_MOVE = { Closed_Fist: "rock", Open_Palm: "paper", Victory: "scissors" };

export const HOW_SURE = 0.5;      // how sure the AI must be about a gesture (0.0 to 1.0)
export const WINS_NEEDED = 3;     // first to 3 wins the match

// "Closed_Fist", 0.9 -> "rock".   Anything unsure, or not a game gesture -> null.
export function gestureToMove(categoryName, score) {
  if (!(score >= HOW_SURE)) return null;
  return Object.hasOwn(GESTURE_TO_MOVE, categoryName) ? GESTURE_TO_MOVE[categoryName] : null;
}

// The camera saw your hand in several pictures. Which move did you REALLY make?
// "moves" has one entry per picture: "rock", "paper", "scissors", or null (no clear gesture).
// Pictures without a clear gesture don't vote (your hand was still moving).
// A move wins if it was seen at least twice AND in more than half of the voting pictures.
// Returns the move, or null if it's unclear.
export function majorityMove(moves) {
  const voting = moves.filter((move) => move !== null && move !== undefined);
  let best = null;
  let bestCount = 0;
  for (const move of MOVES) {
    const count = voting.filter((seen) => seen === move).length;
    if (count > bestCount) {
      best = move;
      bestCount = count;
    }
  }
  if (bestCount >= 2 && bestCount > voting.length / 2) return best;
  return null;
}

// Returns "player", "robot" or "tie".
export function winner(playerMove, robotMove) {
  if (playerMove === robotMove) return "tie";
  return BEATS[playerMove] === robotMove ? "player" : "robot";
}

// The robot's pick. The dice (randomFn) are handed in, so a test can use loaded dice.
// randomFn gives a number from 0 up to (but not including) 1, like Math.random.
export function pickRobotMove(randomFn = Math.random) {
  return MOVES[Math.floor(randomFn() * MOVES.length) % MOVES.length];
}

export function moveThatBeats(move) {
  return MOVES.find((other) => BEATS[other] === move);
}

// Adds one round's result to the score. Ties don't count.
// state is { player: 1, robot: 2 }. Returns a NEW state, plus:
//   over: true when someone reached WINS_NEEDED     matchWinner: "player", "robot" or null
export function updateMatch(state, result, winsNeeded = WINS_NEEDED) {
  const player = state.player + (result === "player" ? 1 : 0);
  const robot = state.robot + (result === "robot" ? 1 : 0);
  const matchWinner = player >= winsNeeded ? "player" : robot >= winsNeeded ? "robot" : null;
  return { player, robot, over: matchWinner !== null, matchWinner };
}

// One round. The robot must commit() BEFORE readPlayer() is allowed.
// That's the fair-play rule: the robot's move is locked in a sealed envelope
// before it gets to see yours. With cheats on, the envelope is empty and the
// robot picks after peeking. The screen shows "?" so everyone can tell.
export function newRound({ cheats = false, randomFn = Math.random, log = () => {} } = {}) {
  const round = {
    cheats,
    committed: false,
    sealed: false,            // true = a real move is locked in the envelope
    robotMove: null,
    playerMove: null,
    result: null,

    commit() {
      if (cheats) {
        log("robot: CHEAT MODE, nothing in the envelope");
      } else {
        round.robotMove = pickRobotMove(randomFn);
        round.sealed = true;
        log("robot committed: " + round.robotMove + " (sealed)");
      }
      round.committed = true;
    },

    readPlayer(move) {
      if (!round.committed) {
        throw new Error("The robot must commit before it may see the player's move!");
      }
      round.playerMove = move;
      if (cheats) round.robotMove = moveThatBeats(move);
      round.result = winner(move, round.robotMove);
      log("player showed: " + move + " -> " + round.result);
      return round.result;
    },
  };
  return round;
}
