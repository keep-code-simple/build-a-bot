# App 2: Reaction Tester. No AI, just speed.
# The screen turns green at a surprise moment. Slap button A as fast as you can!
# This is the smallest complete app. Read it before you write your own.

import random

import pygame

from core import draw


class ReactionGame:
    """The rules, without any screen. state is "ready", "wait", "go", "result" or "too_soon"."""

    def __init__(self, pick_wait=lambda: random.uniform(1.5, 4.0)):
        self.pick_wait = pick_wait        # how long until green (a surprise each time)
        self.state = "ready"
        self.timer = 0.0
        self.wait_for = 0.0
        self.milliseconds = None

    def tick(self, dt):
        """Call every frame with the seconds that passed."""
        self.timer += dt
        if self.state == "wait" and self.timer >= self.wait_for:
            self.state = "go"
            self.timer = 0.0              # the stopwatch starts NOW
            return "green"
        return None

    def press(self):
        """The player hit the button. Returns what happened."""
        if self.state in ("ready", "result", "too_soon"):
            self.state = "wait"
            self.timer = 0.0
            self.wait_for = self.pick_wait()
            return "started"
        if self.state == "wait":          # pressed before green: no cheating!
            self.state = "too_soon"
            return "too_soon"
        self.milliseconds = round(self.timer * 1000)
        self.state = "result"
        return "result"


class App:
    name = "Reaction Tester"
    color = (60, 200, 110)
    needs = set()                         # no AI needed

    def start(self, box):
        self.box = box
        self.players = box.config.get("players", ["Kid 1", "Kid 2", "Guest"])
        self.chosen = 0
        self.game = ReactionGame()
        self.new_record = False
        self.name_buttons = []

    def player(self):
        return self.players[self.chosen]

    def update(self, box, frame, vision, dt):
        if self.game.tick(dt) == "green":
            box.beep(1047, 120)

    def on_button(self, box, name):
        if name == "B":
            return False                  # B: let the box go back to the menu
        if isinstance(name, tuple) and self.game.state in ("ready", "result", "too_soon"):
            touch, x, y = name
            for number, rect in enumerate(self.name_buttons):
                if rect.collidepoint(x, y):
                    self.chosen = number  # tapping a name picks the player
                    return True
        happened = self.game.press()
        if happened == "too_soon":
            box.tune("OOPS")
        elif happened == "result":
            self.new_record = box.scores.record("reaction", self.player(), self.game.milliseconds,
                                                higher_is_better=False)
            box.tune("WIN" if self.new_record else "COUNT")
        return True

    def draw(self, screen):
        wide, high = screen.get_size()
        middle = wide / 2
        state = self.game.state
        screen.fill({"wait": (150, 30, 30), "go": (30, 170, 70)}.get(state, draw.BLACK))
        if state == "wait":
            draw.text(screen, "Wait for green...", (middle, high * 0.45), 12)
            return
        if state == "go":
            draw.text(screen, "GO!", (middle, high * 0.45), 30)
            return

        if state == "result":
            draw.text(screen, f"{self.game.milliseconds} ms", (middle, high * 0.14), 18, draw.YELLOW)
            if self.new_record:
                draw.text(screen, "New record!", (middle, high * 0.25), 8, draw.GREEN)
        elif state == "too_soon":
            draw.text(screen, "Too soon!", (middle, high * 0.16), 16, draw.RED)
        else:
            draw.text(screen, "Reaction Tester", (middle, high * 0.16), 12)

        draw.text(screen, "Who is playing? Tap a name.", (middle, high * 0.34), 5, draw.GRAY)
        self.name_buttons = []
        tall = high * 0.09
        for number, name in enumerate(self.players):
            rect = pygame.Rect(wide * 0.15, high * 0.38 + number * tall * 1.2, wide * 0.7, tall)
            best = self.box.scores.best("reaction", name)
            label = name if best is None else f"{name}   (best {best} ms)"
            draw.button(screen, rect, label, draw.BLUE, chosen=number == self.chosen, size=5)
            self.name_buttons.append(rect)
        draw.text(screen, "Press A to start. Hit A again when it turns green!",
                  (middle, high * 0.82), 5, draw.GRAY)
        draw.text(screen, "Press B for the menu", (middle, high * 0.88), 5, draw.GRAY)

    def stop(self, box):
        pass
