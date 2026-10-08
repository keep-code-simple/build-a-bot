# 📦 Robot Box

The code for **Chapter 7**. A Raspberry Pi, a camera, a touchscreen and two buttons in a box, running small apps you can swap. The guide is `../chapter-7-robot-box.html`.

> **The hardware is fixed. The behavior is software.**

## Try it on the Mac first

No Pi needed. The Mac's camera, a window, and the keyboard stand in for the box.

```
cd robot-box
uv venv --python 3.12
source .venv/bin/activate
uv pip install -r requirements.txt
python setup/download_models.py
python box.py --desktop
```

| On the box | With `--desktop` |
|---|---|
| Button **A** (green): select / play | `A`, Space or Enter |
| Button **B** (red): back / menu | `B`, Escape or Backspace |
| Touchscreen | Mouse click |
| Hold B for 2 seconds: debug numbers | `D` |
| | `Q` quits |

In the menu, **B moves to the next app and A opens it**. Or tap a tile.

Other ways to start it:

```
python box.py --desktop --app rps          straight into Rock Paper Scissors
python box.py --desktop --size 720x1280    a window shaped like the touchscreen standing up
python box.py --desktop --debug            show speed and warnings
python box.py --app rps --arduino          Path A: the Chapter 1 Arduino plays the round
```

## On the Raspberry Pi

```
git clone <this repo>
cd "Door Greeter Bot/robot-box"
bash setup/install.sh              # Path B: screen, speaker, buttons
bash setup/install.sh --path-a     # Path A: no screen, Arduino on USB
```

The script installs everything, downloads the models, and makes the box start by itself. Undo that with `bash setup/install.sh --uninstall-autostart`.

To get new apps onto the box: push from the Mac, then pick **Check for updates** in the box's menu (or run `git pull`), and restart.

## Make a new app

1. Copy `apps/_template/` to `apps/my_app/`.
2. Edit `app.py`: the name, the color, which AI it needs, then `update()` and `draw()`.
3. Restart the box. It's in the menu.

A folder whose name starts with `_` stays hidden. A broken app is skipped (the log says why), and an app that crashes while running shows "Oops!" and goes back to the menu.

`apps/reaction/app.py` is the smallest complete example. Ideas for the next app are in `../robot-box-ideas.md`.

## What's in the folder

```
robot-box/
├── box.py                 the launcher: menu, switching apps, the main loop
├── core/
│   ├── camera.py          Pi camera, Mac camera, or a pretend one for tests
│   ├── vision.py          the vision router: who does the seeing for each app
│   ├── ai_camera.py       the AI Camera's own chip (people, things, pose)
│   ├── health.py          too hot? weak charger? how fast?
│   ├── sound.py           beeps, tunes and the voice
│   ├── buttons.py         arcade buttons, keyboard and touch
│   ├── draw.py            text, buttons and the camera picture, for any screen size
│   ├── scores.py          high scores
│   ├── arduino.py         the optional Arduino on USB
│   └── settings.py        loads config.json
├── apps/
│   ├── _template/app.py   copy this to make a new app
│   ├── rps/               Rock Paper Scissors (app.py = screens, game.py = rules)
│   └── reaction/app.py    Reaction Tester
├── setup/
│   ├── install.sh         sets up a Raspberry Pi
│   ├── run_box.sh         starts the box, and restarts it after a crash
│   └── download_models.py gets the AI models
├── config.example.json    copy to config.json to use real names
└── tests/                 run with: pytest
```

## Settings

Copy `config.example.json` to `config.json` and change it. `config.json` is private: it's never uploaded to GitHub, so real names are fine there.

- `players`: the names on the "Who is playing?" screen.
- `rps.robot_cheats`: `true` makes the robot peek. The envelope then shows **?** instead of a lock, so everyone can tell.
- `rps.wins_needed`: first to this many wins the match.

## Privacy

- No photos or videos are saved. Pictures are looked at and thrown away.
- Nothing is sent to the internet. "Check for updates" only downloads code.
- `config.json`, `models/` and `data/` (scores and the log) stay on your computer. Git ignores them.

## What was tested

Tested on a Mac: the 55 tests pass, and a full Rock Paper Scissors match ran through the launcher with the real hand AI reading a sample photo.

**Not tested, because there was no Raspberry Pi to test on:** the Pi camera and AI Camera code, the arcade buttons, the Piper and espeak voices, the temperature and power readings, and `install.sh`. Expect to fix small things on the first real build.
