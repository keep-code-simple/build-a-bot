# App 1: Rock Paper Scissors against the robot.
# fist = rock, open hand = paper, peace sign = scissors. First to 3 wins the match.
# The robot locks its move in a sealed envelope BEFORE the countdown, so it can't cheat.
# The rules are in game.py. This file is the screens and the timing.

import pygame

from core import draw
from . import game

HOW_SURE = 0.5              # how sure the AI must be about a gesture
COUNT_SECONDS = 0.7         # time for each word of "Rock... Paper... Scissors... SHOOT!"
READ_SECONDS = 0.5          # after SHOOT, collect your gesture for this long, then vote
ROBOT_TURN_SECONDS = 5      # (Arduino only) how long the Arduino needs to play its turn
COUNT_WORDS = ["ROCK...", "PAPER...", "SCISSORS...", "SHOOT!"]


class App:
    name = "Rock Paper Scissors"
    color = (225, 70, 95)
    needs = {"hands"}

    def start(self, box):
        self.box = box
        self.players = box.config.get("players", ["Kid 1", "Kid 2", "Guest"])
        settings = box.config.get("rps", {})
        self.wins_needed = settings.get("wins_needed", 3)
        self.cheats = settings.get("robot_cheats", False)
        self.chosen = 0             # which player is picked
        self.time = 0.0             # the app's own stopwatch
        self.frame = None
        self.hand = None
        self.hand_time = 0.0        # how long a hand has been in view without a break
        self.streak = 0             # rounds won in a row
        self.match = game.Match(self.wins_needed)
        self.round = None
        self.votes = []             # the move seen in each picture, for the vote
        self.name_buttons = []
        self.go("watch" if box.arduino else "attract")

    def go(self, state):
        self.state = state
        self.since = self.time
        self.hand_time = 0.0
        self.step = -1

    def waited(self):
        return self.time - self.since

    def player(self):
        return self.players[self.chosen]

    # ---------- every frame: what's happening? ----------
    def update(self, box, frame, vision, dt):
        self.time += dt
        self.frame = frame
        self.hand = vision.hands[0] if vision.hands else None
        self.hand_time = self.hand_time + dt if self.hand else 0.0
        move_now = None
        if self.hand and self.hand.score >= HOW_SURE:
            move_now = game.GESTURE_TO_MOVE.get(self.hand.gesture)

        if self.state == "attract":
            if self.hand_time >= 0.6:
                self.go("pick")
        elif self.state == "pick":
            if self.hand_time >= 1.5:
                self.start_match()
        elif self.state == "commit":
            if self.waited() >= 1.5:
                self.start_countdown()
        elif self.state == "count":
            step = int(self.waited() / COUNT_SECONDS)
            if step != self.step and step < 4:
                self.step = step
                box.tune("SHOOT" if step == 3 else "COUNT")
            if step >= 3:
                self.go("read")
                self.step = 3
                self.votes = []
        elif self.state == "read":
            if frame is not None:
                self.votes.append(move_now)
            enough = self.waited() >= READ_SECONDS and len(self.votes) >= 2
            if enough or self.waited() >= 1.5:
                self.finish_round()
        elif self.state == "again":
            if self.waited() >= 2:
                self.start_countdown()
        elif self.state == "reveal":
            if self.waited() >= 3:
                if self.match.winner():
                    self.finish_match()
                else:
                    self.new_round()
        elif self.state == "over":
            if self.hand_time >= 1.5:
                self.start_match()

        # ---------- Path A: the Arduino plays the round, like in Chapter 3 ----------
        elif self.state == "watch":
            self.votes = (self.votes + [move_now])[-8:]     # the last few pictures
            move, problem = game.vote(self.votes)
            if move and self.votes.count(move) >= 4:    # held steady for a few pictures
                box.arduino.send(move[0])               # "r", "p" or "s"
                box.log(f"RPS sent {move} to the Arduino")
                self.go("robot")
        elif self.state == "robot":
            if self.waited() >= ROBOT_TURN_SECONDS:
                self.go("away")
        elif self.state == "away":
            if not self.hand and self.waited() >= 0.5:
                self.votes = []
                self.go("watch")

    def start_match(self):
        self.match = game.Match(self.wins_needed)
        self.new_round()

    def new_round(self):
        self.round = game.Round(self.cheats, log=self.box.log)
        self.round.commit()                 # the robot picks FIRST, before the countdown
        self.go("commit")

    def start_countdown(self):
        self.box.say("Rock, paper, scissors, shoot!")
        self.go("count")

    def finish_round(self):
        move, problem = game.vote(self.votes)
        if move is None:
            self.box.say("I couldn't see that. Again!")
            self.go("again")
            return
        result = self.round.read_player(move)
        self.match.add(result)
        if result == "player":
            self.streak += 1
            self.box.scores.record("rps", self.player(), self.streak)
            self.box.tune("WIN")
            self.box.say("You win!")
        elif result == "robot":
            self.streak = 0
            self.box.tune("LOSE")
            self.box.say("I win!")
        else:
            self.box.tune("TIE")
            self.box.say("Tie!")
        self.go("reveal")

    def finish_match(self):
        if self.match.winner() == "player":
            self.box.say(f"{self.player()} wins the match!")
        else:
            self.box.say("The robot wins the match!")
        self.go("over")

    # ---------- buttons and touches ----------
    def on_button(self, box, name):
        if name == "A":
            if self.state == "attract":
                self.go("pick")
            elif self.state == "pick":
                self.chosen = (self.chosen + 1) % len(self.players)     # A cycles through the names
            elif self.state == "over":
                self.start_match()
            return True
        if isinstance(name, tuple):                     # ("touch", x, y)
            touch, x, y = name
            if self.state == "attract":
                self.go("pick")
            elif self.state == "pick":
                for number, rect in enumerate(self.name_buttons):
                    if rect.collidepoint(x, y):
                        self.chosen = number
                        self.start_match()
            elif self.state == "over":
                self.start_match()
            return True
        return False                                    # B: let the box go back to the menu

    # ---------- every frame: draw it ----------
    def draw(self, screen):
        wide, high = screen.get_size()
        u = draw.unit(screen)
        middle = wide / 2
        screen.fill(draw.BLACK)
        if self.state not in ("attract", "pick", "watch", "robot", "away"):
            score = f"{self.player()}  {self.match.player} : {self.match.robot}  Robot"
            draw.text(screen, score, (middle, 7 * u), 8, draw.YELLOW)

        if self.state == "attract":
            blinking = self.time % 4 > 3.8
            draw.robot_face(screen, (middle, high * 0.3), 22 * u, eyes_open=not blinking)
            draw.text(screen, "Show me your hand to play!", (middle, high * 0.55), 9)
            self.draw_camera(screen, big=True)
        elif self.state == "pick":
            draw.text(screen, "Who is playing?", (middle, high * 0.12), 10)
            self.name_buttons = []
            tall = high * 0.11
            for number, name in enumerate(self.players):
                rect = pygame.Rect(wide * 0.15, high * 0.2 + number * tall * 1.2, wide * 0.7, tall)
                best = self.box.scores.best("rps", name)
                label = name if best is None else f"{name}   (best streak {best})"
                draw.button(screen, rect, label, draw.BLUE, chosen=number == self.chosen)
                self.name_buttons.append(rect)
            draw.text(screen, "Tap a name, or press A to change.", (middle, high * 0.68), 5, draw.GRAY)
            draw.text(screen, "Then show your hand to start!", (middle, high * 0.73), 5, draw.GRAY)
            self.draw_camera(screen)
        elif self.state == "commit":
            self.draw_envelope(screen, (middle, high * 0.4), 34 * u)
            words = "The robot is peeking!" if self.cheats else "The robot picked its move."
            draw.text(screen, words, (middle, high * 0.68), 7)
            self.draw_camera(screen)
        elif self.state in ("count", "read"):
            word = COUNT_WORDS[max(0, min(self.step, 3))]
            draw.text(screen, word, (middle, high * 0.4), 18, draw.GREEN if self.step == 3 else draw.WHITE)
            self.draw_envelope(screen, (wide * 0.2, high * 0.68), 14 * u)
            self.draw_camera(screen)
        elif self.state == "again":
            draw.text(screen, "I couldn't see that.", (middle, high * 0.38), 10)
            draw.text(screen, "Again!", (middle, high * 0.5), 14, draw.YELLOW)
            self.draw_camera(screen)
        elif self.state == "reveal":
            self.draw_move(screen, self.round.player_move, (wide * 0.27, high * 0.38), 30 * u, "You")
            self.draw_move(screen, self.round.robot_move, (wide * 0.73, high * 0.38), 30 * u, "Robot")
            words, color = {"player": ("YOU WIN!", draw.GREEN), "robot": ("ROBOT WINS!", draw.RED),
                            "tie": ("TIE!", draw.YELLOW)}[self.round.result]
            draw.text(screen, words, (middle, high * 0.7), 14, color)
        elif self.state == "over":
            won = self.match.winner() == "player"
            draw.text(screen, f"{self.player()} wins!" if won else "The robot wins!",
                      (middle, high * 0.2), 12, draw.GREEN if won else draw.RED)
            draw.text(screen, "Best win streaks", (middle, high * 0.36), 7, draw.YELLOW)
            for row, (name, best) in enumerate(self.box.scores.table("rps")[:5]):
                draw.text(screen, f"{row + 1}. {name}   {best}", (middle, high * 0.43 + row * 6 * u), 6)
            draw.text(screen, "Press A or show your hand to play again", (middle, high * 0.86), 5, draw.GRAY)
            draw.text(screen, "Press B for the menu", (middle, high * 0.91), 5, draw.GRAY)
        elif self.state == "watch":
            draw.text(screen, "Rock, paper or scissors?", (middle, high * 0.2), 9)
            self.draw_camera(screen, big=True)
        elif self.state == "robot":
            draw.text(screen, "Look at the robot!", (middle, high * 0.4), 11, draw.YELLOW)
        elif self.state == "away":
            draw.text(screen, "Hand away... then go again", (middle, high * 0.4), 9)

    def draw_camera(self, screen, big=False):
        """The live camera in a corner, with dots on your hand."""
        wide, high = screen.get_size()
        width = wide * (0.5 if big else 0.3)
        rect = pygame.Rect(0, 0, width, width * 9 / 16)
        if big:
            rect.midbottom = (wide / 2, high * 0.97)
        else:
            rect.bottomright = (wide * 0.98, high * 0.98)
        draw.camera_picture(screen, self.frame, rect)
        if self.hand and self.frame is not None:
            for x, y in self.hand.points:
                spot = (rect.left + x * rect.width, rect.top + y * rect.height)
                pygame.draw.circle(screen, (255, 0, 255), spot, max(2, rect.width // 90))

    def draw_envelope(self, screen, center, size):
        """The sealed envelope with the robot's move inside. A lock if it's fair, "?" if it cheats."""
        rect = pygame.Rect(0, 0, size, size * 0.66)
        rect.center = center
        line = max(2, int(size / 40))
        pygame.draw.rect(screen, (245, 235, 200), rect, border_radius=line * 2)
        pygame.draw.lines(screen, draw.DIM, False, [rect.topleft, rect.center, rect.topright], line)
        if self.round and self.round.sealed:
            body = pygame.Rect(0, 0, size * 0.2, size * 0.16)
            body.center = (rect.centerx, rect.centery + size * 0.12)
            loop = pygame.Rect(0, 0, size * 0.13, size * 0.16)
            loop.midbottom = (body.centerx, body.top + size * 0.05)
            pygame.draw.arc(screen, draw.DIM, loop, 0, 3.15, line * 2)
            pygame.draw.rect(screen, draw.RED, body, border_radius=line)
        else:
            draw.text(screen, "?", (rect.centerx, rect.centery + size * 0.12), size * 0.3 / draw.unit(screen), draw.RED)

    def draw_move(self, screen, move, center, size, who):
        """A big picture of rock, paper or scissors, with a label under it."""
        x, y = center
        half = size / 2
        if move == "rock":
            pygame.draw.circle(screen, (140, 140, 150), center, half * 0.8)
            pygame.draw.circle(screen, (110, 110, 120), (x - half * 0.25, y - half * 0.2), half * 0.25)
        elif move == "paper":
            sheet = pygame.Rect(0, 0, size * 0.62, size * 0.8)
            sheet.center = center
            pygame.draw.rect(screen, draw.WHITE, sheet, border_radius=int(size * 0.03))
            for row in range(1, 5):
                height = sheet.top + row * sheet.height / 5
                pygame.draw.line(screen, draw.GRAY, (sheet.left + size * 0.08, height),
                                 (sheet.right - size * 0.08, height), max(2, int(size / 60)))
        elif move == "scissors":
            thick = max(4, int(size / 14))
            pygame.draw.line(screen, (200, 205, 215), (x - half * 0.45, y + half * 0.5), (x + half * 0.5, y - half * 0.75), thick)
            pygame.draw.line(screen, (200, 205, 215), (x + half * 0.45, y + half * 0.5), (x - half * 0.5, y - half * 0.75), thick)
            for side in (-1, 1):
                pygame.draw.circle(screen, draw.RED, (x + side * half * 0.5, y + half * 0.62), half * 0.24, thick)
        u = draw.unit(screen)
        draw.text(screen, f"{who}: {move}", (x, y + half + 5 * u), 6)

    def stop(self, box):
        pass
