# Reaction Tester: the timing rules, and the app saving a record.
from apps.reaction.app import App, ReactionGame


def test_a_normal_go():
    game = ReactionGame(pick_wait=lambda: 2.0)
    assert game.press() == "started"
    assert game.tick(1.9) is None and game.state == "wait"
    assert game.tick(0.2) == "green" and game.state == "go"
    game.tick(0.25)
    assert game.press() == "result"
    assert game.milliseconds == 250


def test_pressing_too_soon():
    game = ReactionGame(pick_wait=lambda: 2.0)
    game.press()
    game.tick(1.0)
    assert game.press() == "too_soon" and game.state == "too_soon"
    assert game.press() == "started"                # press again to retry


def test_the_app_saves_only_better_times(box, screen):
    app = App()
    app.start(box)
    app.game = ReactionGame(pick_wait=lambda: 1.0)

    def one_go(seconds):
        app.on_button(box, "A")
        app.update(box, None, None, 1.1)            # turns green
        app.draw(screen)
        app.update(box, None, None, seconds)
        app.on_button(box, "A")
        app.draw(screen)

    one_go(0.300)
    assert box.scores.best("reaction", "Kid 1") == 300 and app.new_record
    one_go(0.450)
    assert box.scores.best("reaction", "Kid 1") == 300 and not app.new_record      # slower: not saved
    one_go(0.210)
    assert box.scores.best("reaction", "Kid 1") == 210
    assert app.on_button(box, "B") is False         # B goes back to the menu

    x, y = app.name_buttons[1].center
    app.on_button(box, ("touch", x, y))             # tap the second name
    assert app.player() == "Kid 2" and app.game.state == "result"   # picking a name doesn't start a go
