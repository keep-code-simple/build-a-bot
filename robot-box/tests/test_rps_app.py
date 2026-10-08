# Rock Paper Scissors: playing whole rounds through the app, with pretend eyes.
import numpy as np

from apps.rps.app import App
from core.vision import Hand, Seen
from conftest import FakeArduino

PICTURE = np.zeros((72, 128, 3), np.uint8)
POINTS = [(0.5, 0.5)] * 21


def showing(gesture):
    return Seen(hands=[Hand(gesture, 0.9, POINTS)])


def play(app, box, seen, seconds, screen=None):
    """Runs the app for some seconds, with the camera "seeing" the same thing the whole time."""
    for step in range(round(seconds / 0.05)):
        app.update(box, PICTURE, seen, 0.05)
        if screen:
            app.draw(screen)


def play_until(app, box, seen, state, screen=None):
    """Runs the app until it reaches a state (and fails if it takes more than 10 seconds)."""
    for step in range(200):
        if app.state == state:
            return
        app.update(box, PICTURE, seen, 0.05)
        if screen:
            app.draw(screen)
    raise AssertionError(f"never reached '{state}', stuck in '{app.state}'")


def start_round(app, box, screen):
    app.start(box)
    play(app, box, showing("Open_Palm"), 0.7, screen)       # hand in view: attract -> pick a player
    assert app.state == "pick"
    play(app, box, showing("Open_Palm"), 1.6, screen)       # keep showing: the match starts
    assert app.state == "commit"


def test_a_full_round_and_the_envelope(box, screen, log):
    app = App()
    start_round(app, box, screen)
    assert app.round.sealed                                 # locked in before the countdown
    robot_move = app.round.robot_move
    play_until(app, box, Seen(), "count", screen)           # envelope screen
    play_until(app, box, Seen(), "read", screen)            # ROCK... PAPER... SCISSORS... SHOOT!
    play(app, box, showing("Closed_Fist"), 0.7, screen)     # you show rock
    assert app.state == "reveal"
    assert app.round.player_move == "rock"
    assert app.round.robot_move == robot_move               # the sealed move didn't change
    assert "Rock, paper, scissors, shoot!" in box.sound.said
    assert box.sound.played.count("COUNT") == 3 and "SHOOT" in box.sound.played
    committed = next(i for i, line in enumerate(log) if "robot committed" in line)
    showed = next(i for i, line in enumerate(log) if "player showed" in line)
    assert committed < showed
    play(app, box, Seen(), 3.1, screen)                     # the reveal ends, the next round begins
    assert app.state == "commit"


def test_no_hand_means_again_with_the_same_envelope(box, screen):
    app = App()
    start_round(app, box, screen)
    sealed_round = app.round
    play_until(app, box, Seen(), "read", screen)
    play_until(app, box, Seen(), "again", screen)           # nobody shows a hand after SHOOT
    assert "I couldn't see that. Again!" in box.sound.said
    play(app, box, Seen(), 2.1, screen)
    assert app.state == "count" and app.round is sealed_round   # the robot keeps its move


def test_a_whole_match_and_the_leaderboard(box, screen):
    box.config["rps"]["robot_cheats"] = False
    app = App()
    start_round(app, box, screen)
    for round_number in range(30):
        if app.state == "over":
            break
        beats_robot = {"rock": "Open_Palm", "paper": "Victory", "scissors": "Closed_Fist"}[app.round.robot_move]
        play_until(app, box, Seen(), "read")
        play_until(app, box, showing(beats_robot), "reveal")    # we peek, so the player always wins
        play(app, box, Seen(), 3.1)
    assert app.state == "over" and app.match.winner() == "player"
    assert (app.match.player, app.match.robot) == (3, 0)
    assert box.scores.best("rps", "Kid 1") == 3             # three wins in a row
    assert "Kid 1 wins the match!" in box.sound.said
    app.draw(screen)
    assert app.on_button(box, "B") is False                 # B is left for the box: back to the menu
    app.on_button(box, "A")
    assert app.state == "commit"                            # A: play again


def test_cheat_mode_shows_on_screen(box, screen):
    box.config["rps"]["robot_cheats"] = True
    app = App()
    start_round(app, box, screen)
    assert app.round.sealed is False                        # draw_envelope draws "?" when not sealed
    play_until(app, box, Seen(), "read", screen)
    play_until(app, box, showing("Victory"), "reveal", screen)
    assert app.round.result == "robot"


def test_picking_a_player(box, screen):
    app = App()
    app.start(box)
    app.on_button(box, "A")                                 # attract -> pick
    assert app.state == "pick"
    app.draw(screen)
    app.on_button(box, "A")
    assert app.player() == "Kid 2"                          # A cycles through the names
    x, y = app.name_buttons[2].center
    app.on_button(box, ("touch", x, y))                     # tapping a name picks it and starts
    assert app.player() == "Guest" and app.state == "commit"


def test_with_an_arduino_it_sends_the_move_like_chapter_3(box, screen):
    box.arduino = FakeArduino()
    app = App()
    app.start(box)
    assert app.state == "watch"
    play(app, box, showing("Victory"), 0.4, screen)
    assert box.arduino.sent == ["s"]
    assert app.state == "robot"
    play(app, box, showing("Victory"), 5.1, screen)         # the Arduino plays its turn
    assert app.state == "away"
    play(app, box, showing("Victory"), 1, screen)           # hand still there: wait
    assert app.state == "away"
    play(app, box, Seen(), 0.6, screen)                     # hand away: ready for the next round
    assert app.state == "watch"
    play(app, box, showing("Closed_Fist"), 0.4, screen)
    assert box.arduino.sent == ["s", "r"]
