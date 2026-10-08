# The box's buttons. Every frame, buttons.read() returns a list of what just happened:
#   "A"                 the green button (select / play)
#   "B"                 the red button (back / menu)
#   ("touch", x, y)     a finger on the touchscreen (or a mouse click with --desktop)
#   "DEBUG"             show or hide the debug overlay (hold B for 2 seconds; D on the keyboard)
#   "QUIT"              close the program (Q on the keyboard, or closing the window)
# On the Pi the arcade buttons are wired to GPIO pins. With --desktop the keyboard stands in:
#   A = A, Space or Enter       B = B, Escape or Backspace

import queue

import pygame

A_KEYS = {pygame.K_a, pygame.K_SPACE, pygame.K_RETURN}
B_KEYS = {pygame.K_b, pygame.K_ESCAPE, pygame.K_BACKSPACE}
HOLD_SECONDS = 2


class Buttons:
    def __init__(self, config=None, desktop=False, log=print):
        self.pressed = queue.Queue()      # the GPIO buttons drop their presses in here
        self.arcade = []
        self.b_was_held = False
        if not desktop:
            pins = (config or {}).get("buttons", {"A": 17, "B": 27})
            try:
                from gpiozero import Button           # Pi-only, so it's imported here
                a = Button(pins["A"], pull_up=True, bounce_time=0.05)
                b = Button(pins["B"], pull_up=True, bounce_time=0.05, hold_time=HOLD_SECONDS)
                a.when_pressed = lambda: self.pressed.put("A")
                b.when_released = self._b_released
                b.when_held = self._b_held
                self.arcade = [a, b]                  # keep them, or they stop listening
            except Exception as problem:              # no buttons wired yet (Path A): that's fine
                log(f"No arcade buttons ({problem}). Touch and keyboard still work.")

    def _b_held(self):
        self.b_was_held = True
        self.pressed.put("DEBUG")

    def _b_released(self):
        if not self.b_was_held:           # a short press is "B"; a long one already sent "DEBUG"
            self.pressed.put("B")
        self.b_was_held = False

    def read(self):
        happened = []
        while not self.pressed.empty():
            happened.append(self.pressed.get())
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                happened.append("QUIT")
            elif event.type == pygame.KEYDOWN:
                if event.key in A_KEYS:
                    happened.append("A")
                elif event.key in B_KEYS:
                    happened.append("B")
                elif event.key == pygame.K_d:
                    happened.append("DEBUG")
                elif event.key == pygame.K_q:
                    happened.append("QUIT")
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                happened.append(("touch", event.pos[0], event.pos[1]))
        return happened
