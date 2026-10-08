# TEMPLATE: copy this whole folder to make a new app.
#   1. Copy  apps/_template/  to  apps/my_app/   (any name without spaces)
#   2. Change the name, color and needs below
#   3. Fill in update() and draw()
#   4. Restart the box. Your app is in the menu!
# Folders that start with "_" (like this one) stay hidden from the menu.

from core import draw


class App:
    name = "My App"                 # what the menu tile says
    color = (255, 170, 0)           # the menu tile's color: (red, green, blue), each 0 to 255
    needs = set()                   # which AI to switch on. Any of:
                                    #   "hands"   your hand: its gesture and 21 points
                                    #   "faces"   a box around each face
                                    #   "people"  a box around each person
                                    #   "objects" everyday things, like "cat", "dog", "cup"
                                    #   "pose"    body points (a stick figure)
                                    # Example: needs = {"hands"}. Leave it empty for no AI.

    def start(self, box):
        """The app opens. Set up your game here."""
        self.box = box
        self.count = 0

    def update(self, box, frame, vision, dt):
        """Runs every frame. Read what the AI saw, and change your game.

        frame   the camera's picture (or None)
        vision  what the AI found: vision.hands, vision.faces, vision.people,
                vision.objects, vision.poses. Only the ones in "needs" are filled in.
        dt      seconds since the last frame (about 0.03). Add it up to make a timer.
        """
        # Example: if vision.hands and vision.hands[0].gesture == "Thumb_Up": ...
        pass

    def draw(self, screen):
        """Runs every frame, after update(). Draw your game."""
        wide, high = screen.get_size()
        screen.fill(draw.BLACK)
        draw.text(screen, "My App", (wide / 2, high * 0.3), 12, draw.YELLOW)
        draw.text(screen, f"You pressed A {self.count} times", (wide / 2, high * 0.5), 7)
        draw.text(screen, "Press B for the menu", (wide / 2, high * 0.9), 5, draw.GRAY)

    def on_button(self, box, name):
        """A button or a touch. name is "A", "B", or ("touch", x, y).

        Return True if you used it. If you return False for "B", the box goes back to the menu.
        """
        if name == "A":
            self.count += 1
            box.beep(880, 100)          # also try: box.tune("WIN")  box.say("Hello!")
            return True
        return False

    def stop(self, box):
        """The app closes. Usually there's nothing to do."""
        pass

# What "box" can do for you:
#   box.say("Hello!")                       the robot's voice
#   box.beep(880, 200)                      one beep: pitch, then milliseconds
#   box.tune("WIN")                         HELLO, WIN, LOSE, TIE, COUNT, SHOOT, OOPS
#   box.scores.record("my_app", "Kid 1", 12)   save a high score (returns True for a new record)
#   box.scores.best("my_app", "Kid 1")         read it back
#   box.scores.table("my_app")                 the leaderboard, best first
#   box.config                              the settings from config.json
#   box.arduino                             the Arduino, if one is plugged in: box.arduino.send("F")
#   box.log("something happened")           write a line in the box's log
