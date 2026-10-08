# Rock Paper Scissors: the rules. No screen and no camera in this file, just thinking.
# That makes it easy to test, and easy to read.

from collections import Counter
import random

MOVES = ["rock", "paper", "scissors"]
BEATS = {"rock": "scissors", "paper": "rock", "scissors": "paper"}      # rock beats scissors...

# The AI already knows these gestures. We turn them into game moves.
GESTURE_TO_MOVE = {"Closed_Fist": "rock", "Open_Palm": "paper", "Victory": "scissors"}


def who_wins(player, robot):
    """Returns "player", "robot" or "tie"."""
    if player == robot:
        return "tie"
    return "player" if BEATS[player] == robot else "robot"


def move_that_beats(move):
    return next(winner for winner, loser in BEATS.items() if loser == move)


def vote(moves):
    """The camera saw your hand in several pictures. Which move did you REALLY make?

    moves is one entry per picture: "rock", "paper", "scissors", or None (no clear gesture).
    Pictures without a clear gesture don't vote (your hand was still moving).
    A move wins if it was seen at least twice AND in more than half of the voting pictures.
    Returns (move, problem). problem is None, "no hand" or "unclear".
    """
    seen = [move for move in moves if move is not None]
    if not seen:
        return None, "no hand"
    move, count = Counter(seen).most_common(1)[0]
    if count >= 2 and count > len(seen) / 2:
        return move, None
    return None, "unclear"


class Round:
    """One round. The robot must commit() to its move BEFORE read_player() is allowed.

    That's the fair-play rule: the robot's move is locked in a sealed envelope
    before it gets to see yours. If cheats is True, the envelope is empty and the
    robot picks after peeking. The screen shows a "?" so everyone can tell.
    """

    def __init__(self, cheats=False, pick=random.choice, log=print):
        self.cheats = cheats
        self.pick = pick
        self.log = log
        self.committed = False
        self.sealed = False           # True = a real move is locked in the envelope
        self.robot_move = None
        self.player_move = None
        self.result = None

    def commit(self):
        if self.cheats:
            self.log("RPS robot: CHEAT MODE, nothing in the envelope")
        else:
            self.robot_move = self.pick(MOVES)
            self.sealed = True
            self.log(f"RPS robot committed: {self.robot_move} (sealed)")
        self.committed = True

    def read_player(self, move):
        if not self.committed:
            raise RuntimeError("The robot must commit before it may see the player's move!")
        self.player_move = move
        if self.cheats:
            self.robot_move = move_that_beats(move)
        self.result = who_wins(move, self.robot_move)
        self.log(f"RPS player showed: {move} -> {self.result}")
        return self.result


class Match:
    """First to wins_needed wins the match."""

    def __init__(self, wins_needed=3):
        self.wins_needed = wins_needed
        self.player = 0
        self.robot = 0

    def add(self, result):
        if result == "player":
            self.player += 1
        elif result == "robot":
            self.robot += 1

    def winner(self):
        """ "player", "robot", or None while the match is still going."""
        if self.player >= self.wins_needed:
            return "player"
        if self.robot >= self.wins_needed:
            return "robot"
        return None
