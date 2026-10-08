# Rock Paper Scissors: the rules, the vote, and the fair-play order.
import pytest

from apps.rps import game


@pytest.mark.parametrize("player, robot, result", [
    ("rock", "rock", "tie"), ("rock", "paper", "robot"), ("rock", "scissors", "player"),
    ("paper", "rock", "player"), ("paper", "paper", "tie"), ("paper", "scissors", "robot"),
    ("scissors", "rock", "robot"), ("scissors", "paper", "player"), ("scissors", "scissors", "tie"),
])
def test_who_wins_all_nine(player, robot, result):
    assert game.who_wins(player, robot) == result


def test_move_that_beats():
    for move in game.MOVES:
        assert game.who_wins(game.move_that_beats(move), move) == "player"


def test_vote_clear_gesture():
    assert game.vote(["rock"] * 6) == ("rock", None)
    assert game.vote(["paper", "paper", None, "paper", "rock"]) == ("paper", None)
    assert game.vote([None, None, None, "rock", "rock"]) == ("rock", None)        # a late hand still counts


def test_vote_mixed_is_unclear():
    assert game.vote(["rock", "paper", "scissors", "rock", "paper"]) == (None, "unclear")
    assert game.vote(["rock", "rock", "paper", "paper"]) == (None, "unclear")      # exactly half isn't enough
    assert game.vote(["rock", None, None, None, None]) == (None, "unclear")        # seen only once


def test_vote_no_hand():
    assert game.vote([None, None, None]) == (None, "no hand")
    assert game.vote([]) == (None, "no hand")


def test_robot_commits_before_the_player_is_read(log):
    round = game.Round(pick=lambda moves: "rock", log=log.append)
    with pytest.raises(RuntimeError):
        round.read_player("paper")                  # the robot hasn't committed: not allowed!
    round.commit()
    assert round.sealed and round.robot_move == "rock"
    assert round.read_player("paper") == "player"
    assert round.robot_move == "rock"               # seeing the player's move didn't change it
    committed = next(i for i, line in enumerate(log) if "committed: rock" in line)
    showed = next(i for i, line in enumerate(log) if "player showed: paper" in line)
    assert committed < showed                       # the log proves the order


def test_cheat_mode_is_not_sealed_and_always_wins(log):
    for move in game.MOVES:
        round = game.Round(cheats=True, log=log.append)
        round.commit()
        assert round.sealed is False                # the screen shows "?" instead of a lock
        assert round.robot_move is None
        assert round.read_player(move) == "robot"
    assert any("CHEAT MODE" in line for line in log)


def test_match_first_to_three():
    match = game.Match(3)
    for result in ["player", "tie", "robot", "player"]:
        match.add(result)
        assert match.winner() is None
    match.add("player")
    assert match.winner() == "player"
    assert (match.player, match.robot) == (3, 1)
