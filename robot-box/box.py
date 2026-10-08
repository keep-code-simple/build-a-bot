# The Robot Box launcher: the menu, switching apps, and the main loop.
#
#   On the Mac:        python box.py --desktop           (Mac camera, a window, keyboard as buttons)
#   Straight to a game: python box.py --desktop --app rps
#   Path A on the Pi:  python box.py --app rps --arduino  (the Chapter 1 Arduino is the screen)
#   Debug numbers:     add --debug, or press D (hold button B for 2 seconds on the box)
#
# Every app is a folder in apps/. Drop in a new folder and it shows up in the menu.
# Buttons in the menu:  B = next app    A = open it    (or just tap a tile)

import argparse
import importlib
import logging
import logging.handlers
import os
import subprocess
import sys
import threading
import traceback
from pathlib import Path

BOX_FOLDER = Path(__file__).resolve().parent
sys.path.insert(0, str(BOX_FOLDER))             # so apps can say "from core import draw"

import pygame

if sys.platform == "darwin":
    # On the Mac, pygame and OpenCV each bring their own copy of a library called SDL, and macOS
    # prints a wall of scary-looking (but harmless) warnings about it. Hide just those lines.
    hidden, keep = os.open(os.devnull, os.O_WRONLY), os.dup(2)
    os.dup2(hidden, 2)
    try:
        import cv2      # noqa: F401 (imported here only to hide its warnings)
    finally:
        os.dup2(keep, 2)
        os.close(hidden)
        os.close(keep)

from core import draw
from core.health import Health, Speedometer
from core.scores import Scores
from core.settings import DATA_FOLDER, load_config
from core.vision import MissingModel

APP_PARTS = ["name", "needs", "start", "update", "draw", "on_button", "stop"]


def find_apps(apps_folder=BOX_FOLDER / "apps", log=print, package="apps"):
    """Loads every app folder. Returns {"rps": AppClass, ...}. A broken app is skipped, not fatal."""
    apps = {}
    for folder in sorted(Path(apps_folder).iterdir()):
        if not (folder / "app.py").exists():
            continue
        try:
            module = importlib.import_module(f"{package}.{folder.name}.app")
            missing = [part for part in APP_PARTS if not hasattr(module.App, part)]
            if missing:
                raise AttributeError(f"its App is missing {missing}")
            apps[folder.name] = module.App
        except Exception as problem:
            log(f"Skipped the app '{folder.name}': {problem}")
    return apps


class Box:
    """The helpers every app gets: box.say(), box.beep(), box.scores and friends."""

    def __init__(self, config, sound=None, scores=None, arduino=None, log=print):
        self.config = config
        self.sound = sound
        self.scores = scores
        self.arduino = arduino
        self.log = log

    def say(self, text):
        if self.sound:
            self.sound.say(text)

    def beep(self, hz=880, ms=200):
        if self.sound:
            self.sound.beep(hz, ms)

    def tune(self, name):
        if self.sound:
            self.sound.tune(name)


class UpdateApp:
    """Built in: "Check for updates" runs git pull, so new apps arrive from GitHub."""
    name = "Check for updates"
    color = (90, 96, 120)
    needs = set()

    def __init__(self, run=subprocess.run):
        self.run = run

    def start(self, box):
        self.words = "Looking for new apps..."
        self.done = False
        threading.Thread(target=self.pull, daemon=True).start()

    def pull(self):
        try:
            answer = self.run(["git", "-C", str(BOX_FOLDER), "pull", "--ff-only"],
                              capture_output=True, text=True, timeout=60)
            if answer.returncode != 0:
                self.words = "Couldn't update. Is the Wi-Fi on?"
            elif "Already up to date" in answer.stdout:
                self.words = "Nothing new. You have the latest!"
            else:
                self.words = "Updated! Restart the box to see new apps."
        except (OSError, subprocess.SubprocessError):
            self.words = "Couldn't update. Is the Wi-Fi on?"
        self.done = True

    def update(self, box, frame, vision, dt):
        pass

    def draw(self, screen):
        wide, high = screen.get_size()
        screen.fill(draw.BLACK)
        draw.text(screen, self.words, (wide / 2, high * 0.4), 7)
        if self.done:
            draw.text(screen, "Press B for the menu", (wide / 2, high * 0.9), 5, draw.GRAY)

    def on_button(self, box, name):
        return False

    def stop(self, box):
        pass


class Launcher:
    def __init__(self, screen, box, camera, vision, buttons, health=None, apps=None,
                 desktop=False, debug=False):
        self.screen = screen
        self.box = box
        self.camera = camera
        self.vision = vision
        self.buttons = buttons
        self.health = health
        self.desktop = desktop
        self.debug = debug
        self.apps = dict(apps if apps is not None else find_apps(log=box.log))
        self.menu = [name for name in self.apps if not name.startswith("_")]
        self.apps["_update"] = UpdateApp
        self.menu.append("_update")
        self.chosen = 0                 # which menu tile is highlighted
        self.tiles = []
        self.app = None                 # the app that's open (None = the menu)
        self.app_name = None
        self.crash = None               # words for the "Oops" screen, when an app broke
        self.running = True
        self.loop_speed = Speedometer()

    # ---------- opening and closing apps ----------
    def open_app(self, name):
        self.close_app()
        self.box.log(f"Opening {name}")
        try:
            app = self.apps[name]()
            self.vision.open(app.needs)
            app.start(self.box)
            self.app, self.app_name = app, name
        except Exception as problem:
            self.oops(name, problem)

    def close_app(self):
        if self.app is not None:
            try:
                self.app.stop(self.box)
            except Exception as problem:
                self.box.log(f"{self.app_name} had a problem while closing: {problem}")
        self.app, self.app_name = None, None
        self.vision.close()

    def oops(self, name, problem):
        """An app broke. Say so kindly, write down the details, and go back to the menu."""
        self.box.log(f"CRASH in {name}:\n{traceback.format_exc()}")
        self.app, self.app_name = None, None
        try:
            self.vision.close()
        except Exception:
            pass
        if isinstance(problem, MissingModel):
            self.crash = (name, str(problem))
        else:
            self.crash = (name, f"{type(problem).__name__}: {problem}")
        self.box.tune("OOPS")

    # ---------- one frame ----------
    def frame(self, dt):
        for event in self.buttons.read():
            self.handle(event)
        if self.app is not None:
            name = self.app_name
            try:
                picture = self.camera.read() if self.camera else None
                seen = self.vision.look(picture)
                self.app.update(self.box, picture, seen, dt)
                if self.app is not None:
                    self.app.draw(self.screen)
            except Exception as problem:
                self.oops(name, problem)
        if self.app is None:
            if self.crash:
                self.draw_oops()
            else:
                self.draw_menu()
        self.draw_health()
        self.loop_speed.tick()
        pygame.display.flip()

    def handle(self, event):
        if event == "QUIT":
            self.running = False
        elif event == "DEBUG":
            self.debug = not self.debug
        elif self.crash:
            self.crash = None           # any button leaves the Oops screen
        elif self.app is not None:
            name = self.app_name
            try:
                used = self.app.on_button(self.box, event)
            except Exception as problem:
                self.oops(name, problem)
                return
            if event == "B" and not used:
                self.close_app()
        elif event == "B":
            self.chosen = (self.chosen + 1) % len(self.menu)
            self.box.beep(660, 60)
        elif event == "A":
            self.open_app(self.menu[self.chosen])
        elif isinstance(event, tuple):
            for number, rect in enumerate(self.tiles):
                if rect.collidepoint(event[1], event[2]):
                    self.chosen = number
                    self.open_app(self.menu[number])

    # ---------- the launcher's own screens ----------
    def draw_menu(self):
        screen = self.screen
        wide, high = screen.get_size()
        u = draw.unit(screen)
        screen.fill(draw.BLACK)
        draw.text(screen, "Robot Box", (wide / 2, 8 * u), 11, draw.YELLOW)
        columns = 2 if wide >= high else 1
        rows = -(-len(self.menu) // columns)                    # divide, rounding up
        gap = 3 * u
        tile_wide = (wide - gap * (columns + 1)) / columns
        tile_high = min(26 * u, (high - 22 * u - gap * rows) / rows)
        self.tiles = []
        for number, name in enumerate(self.menu):
            rect = pygame.Rect(gap + (number % columns) * (tile_wide + gap),
                               16 * u + (number // columns) * (tile_high + gap), tile_wide, tile_high)
            app = self.apps[name]
            draw.button(screen, rect, app.name, app.color, chosen=number == self.chosen, size=6)
            self.tiles.append(rect)
        draw.text(screen, "B = next    A = open    or tap", (wide / 2, high - 4 * u), 4, draw.GRAY)

    def draw_oops(self):
        screen = self.screen
        wide, high = screen.get_size()
        name, words = self.crash
        screen.fill((70, 20, 30))
        draw.text(screen, "Oops! This app crashed", (wide / 2, high * 0.25), 10)
        draw.text(screen, name, (wide / 2, high * 0.38), 7, draw.YELLOW)
        draw.paragraph(screen, words, (wide / 2, high * 0.52), 5)
        draw.text(screen, "Press any button to go back to the menu", (wide / 2, high * 0.8), 5, draw.GRAY)

    def draw_health(self):
        """Warning badges (too hot, weak charger) and, in debug mode, the numbers."""
        screen = self.screen
        wide, high = screen.get_size()
        u = draw.unit(screen)
        warnings = self.health.check() if self.health else []
        bottom = high - u                           # stack things up from the bottom-left corner
        for name, words in warnings:
            color = draw.RED if name == "hot" else draw.YELLOW
            rect = pygame.Rect(u, bottom - 6 * u, 45 * u, 6 * u)
            pygame.draw.rect(screen, color, rect, border_radius=int(u))
            draw.text(screen, words, rect.center, 4, draw.BLACK)
            bottom = rect.top - u
        if self.debug:
            lines = [f"{self.loop_speed.per_second:.0f} pictures a second (camera + AI)"]
            if self.health and self.health.temperature is not None:
                lines.append(f"chip temperature {self.health.temperature:.0f} C")
            routes = getattr(self.vision, "routes", {})
            lines += [f"{need}: {who}" for need, who in sorted(routes.items())]
            lines.append("warnings: " + (", ".join(name for name, words in warnings) or "none"))
            for line in reversed(lines):
                picture = draw.font(3.5 * u).render(line, True, draw.WHITE, draw.BLACK)
                bottom -= 4 * u
                screen.blit(picture, (u, bottom))

    def run(self, first_app=None):
        if first_app:
            self.open_app(first_app)
        clock = pygame.time.Clock()
        while self.running:
            dt = clock.tick(30) / 1000              # at most 30 frames a second
            self.frame(min(dt, 0.25))
        self.close_app()


def make_log():
    """Log lines go to the Terminal and to data/box.log (kept small: kind to the SD card)."""
    DATA_FOLDER.mkdir(parents=True, exist_ok=True)
    logger = logging.getLogger("robot-box")
    logger.setLevel(logging.INFO)
    file = logging.handlers.RotatingFileHandler(DATA_FOLDER / "box.log", maxBytes=200_000, backupCount=1)
    file.setFormatter(logging.Formatter("%(asctime)s %(message)s", "%Y-%m-%d %H:%M:%S"))
    logger.addHandler(file)
    logger.addHandler(logging.StreamHandler())
    return logger.info


def main():
    parser = argparse.ArgumentParser(description="The Robot Box")
    parser.add_argument("--desktop", action="store_true", help="run on the Mac: its camera, a window, keyboard buttons")
    parser.add_argument("--app", help="open this app right away, like: rps")
    parser.add_argument("--arduino", action="store_true", help="use the Chapter 1 Arduino on USB (Path A)")
    parser.add_argument("--debug", action="store_true", help="show speed, temperature and warnings")
    parser.add_argument("--size", default="1280x720", help="window size with --desktop, like 720x1280")
    args = parser.parse_args()

    log = make_log()
    config = load_config()
    apps = find_apps(log=log)
    if args.app and args.app not in apps:
        names = ", ".join(name for name in apps if not name.startswith("_"))
        raise SystemExit(f"There's no app called '{args.app}'. I have: {names}")

    # No screen plugged in (Path A)? Tell pygame to draw on a pretend one.
    on_linux = sys.platform.startswith("linux")
    if on_linux and not os.environ.get("DISPLAY") and not os.environ.get("WAYLAND_DISPLAY"):
        os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
    pygame.init()
    if args.desktop:
        wide, high = (int(number) for number in args.size.lower().split("x"))
        screen = pygame.display.set_mode((wide, high))
    else:
        screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
        pygame.mouse.set_visible(False)
    pygame.display.set_caption("Robot Box")

    from core.arduino import Arduino
    from core.buttons import Buttons
    from core.camera import open_camera
    from core.sound import Sound
    from core.vision import Vision

    try:
        camera = open_camera(args.desktop, config, log)
    except (SystemExit, Exception) as problem:      # no camera: apps without AI still work
        log(f"No camera: {problem}")
        camera = None
    box = Box(config, Sound(config, args.desktop, log=log), Scores(DATA_FOLDER / "scores.json"),
              Arduino(log=log) if args.arduino else None, log)
    vision = Vision(camera, args.desktop, config.get("ai_picture_width", 640))
    launcher = Launcher(screen, box, camera, vision, Buttons(config, args.desktop, log),
                        Health(log=log), apps, args.desktop, args.debug)
    log("Robot Box is ready")
    try:
        launcher.run(args.app)
    finally:
        if camera:
            camera.close()
        if box.arduino:
            box.arduino.close()
        pygame.quit()


if __name__ == "__main__":
    main()
