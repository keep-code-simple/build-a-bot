# Loading apps from folders, and the launcher: menu, opening apps, crashes, going back.

import numpy as np

import box as box_file
from core.camera import FakeCamera
from core.vision import FakeVision, Hand, Seen
from conftest import BOX_FOLDER, FakeButtons

PARTS = '''
class App:
    name = "{name}"
    color = (1, 2, 3)
    needs = {needs}
    def start(self, box): self.frames = 0
    def update(self, box, frame, vision, dt): {update}
    def draw(self, screen): screen.fill((0, 0, 0))
    def on_button(self, box, name): return False
    def stop(self, box): pass
'''


def test_the_real_apps_all_load(log):
    apps = box_file.find_apps(log=log.append)
    assert {"rps", "reaction", "_template"} <= set(apps)
    assert log == []                                        # nothing was skipped
    for name, app in apps.items():
        for part in box_file.APP_PARTS:
            assert hasattr(app, part), f"{name} is missing {part}"
    assert apps["rps"].needs == {"hands"} and apps["reaction"].needs == set()


def test_every_app_folder_has_an_app_file():
    for folder in (BOX_FOLDER / "apps").iterdir():
        if folder.is_dir() and folder.name != "__pycache__":
            assert (folder / "app.py").exists(), f"apps/{folder.name}/ has no app.py"


def make_apps(tmp_path, monkeypatch, package, files):
    folder = tmp_path / package
    for name, code in files.items():
        (folder / name).mkdir(parents=True)
        (folder / name / "app.py").write_text(code)
    monkeypatch.syspath_prepend(str(tmp_path))
    return folder


def test_a_broken_app_is_skipped_with_a_message(tmp_path, monkeypatch, log):
    folder = make_apps(tmp_path, monkeypatch, "shelf_one", {
        "good": PARTS.format(name="Good", needs="set()", update="pass"),
        "typo": "class App:\n    def oops(:\n",
        "half": "class App:\n    name = 'Half done'\n",
        "empty": "",
    })
    (folder / "notes").mkdir()                              # a folder without app.py is just ignored
    apps = box_file.find_apps(folder, log.append, package="shelf_one")
    assert list(apps) == ["good"]
    assert len(log) == 3
    assert any("'typo'" in line for line in log)
    assert any("'half'" in line and "missing" in line for line in log)


def make_launcher(box, screen, apps=None, seen=None):
    buttons = FakeButtons()
    camera = FakeCamera([np.zeros((72, 128, 3), np.uint8)])
    launcher = box_file.Launcher(screen, box, camera, FakeVision(seen), buttons, apps=apps, desktop=True)
    return launcher, buttons


def test_menu_to_rps_and_back(box, screen):
    launcher, buttons = make_launcher(box, screen)
    launcher.frame(0.03)
    assert launcher.app is None and launcher.menu[:2] == ["reaction", "rps"]
    assert "_template" not in launcher.menu                 # hidden from the menu
    buttons.next = ["B"]                                    # B: highlight the next tile
    launcher.frame(0.03)
    assert launcher.menu[launcher.chosen] == "rps"
    buttons.next = ["A"]                                    # A: open it
    launcher.frame(0.03)
    assert launcher.app_name == "rps" and launcher.vision.opened_with == {"hands"}
    for step in range(5):
        launcher.frame(0.03)
    buttons.next = ["B"]                                    # B inside the app: back to the menu
    launcher.frame(0.03)
    assert launcher.app is None and launcher.vision.opened_with is None
    launcher.frame(0.03)


def test_tapping_a_tile_opens_that_app(box, screen):
    launcher, buttons = make_launcher(box, screen)
    launcher.frame(0.03)
    x, y = launcher.tiles[launcher.menu.index("reaction")].center
    buttons.next = [("touch", x, y)]
    launcher.frame(0.03)
    assert launcher.app_name == "reaction"


def test_a_crashing_app_goes_to_oops_then_the_menu(tmp_path, monkeypatch, box, screen, log):
    folder = make_apps(tmp_path, monkeypatch, "shelf_two", {
        "boom": PARTS.format(name="Boom", needs="set()", update="self.frames += 1; 1 / (3 - self.frames)"),
    })
    apps = box_file.find_apps(folder, log.append, package="shelf_two")
    launcher, buttons = make_launcher(box, screen, apps)
    launcher.open_app("boom")
    launcher.frame(0.03)
    launcher.frame(0.03)
    assert launcher.app_name == "boom" and launcher.crash is None
    launcher.frame(0.03)                                    # third frame: divide by zero!
    assert launcher.app is None
    assert launcher.crash == ("boom", "ZeroDivisionError: division by zero")
    assert any("CRASH in boom" in line and "Traceback" in line for line in log)    # details are in the log
    assert "OOPS" in box.sound.played
    launcher.frame(0.03)                                    # the Oops screen draws without trouble
    buttons.next = ["A"]
    launcher.frame(0.03)
    assert launcher.crash is None and launcher.app is None  # back at the menu, still running
    assert launcher.running


def test_an_app_asking_for_eyes_that_do_not_exist(tmp_path, monkeypatch, box, screen, log):
    folder = make_apps(tmp_path, monkeypatch, "shelf_three", {
        "nose": PARTS.format(name="Nose", needs='{"smells"}', update="pass"),
    })
    launcher, buttons = make_launcher(box, screen, box_file.find_apps(folder, log.append, package="shelf_three"))
    launcher.open_app("nose")
    assert launcher.app is None and "smells" in launcher.crash[1]


def test_debug_overlay_and_quit(box, screen):
    launcher, buttons = make_launcher(box, screen, seen=[Seen(hands=[Hand("Victory", 0.9, [(0.5, 0.5)] * 21)])])
    launcher.open_app("rps")
    buttons.next = ["DEBUG"]
    launcher.frame(0.03)
    assert launcher.debug is True
    buttons.next = ["QUIT"]
    launcher.frame(0.03)
    assert launcher.running is False


def test_check_for_updates_messages(box, screen):
    class Answer:
        def __init__(self, code, out):
            self.returncode, self.stdout = code, out

    for answer, words in [(Answer(0, "Already up to date.\n"), "Nothing new"),
                          (Answer(0, "Updating abc..def\n"), "Updated!"),
                          (Answer(1, ""), "Couldn't update")]:
        app = box_file.UpdateApp(run=lambda command, **options: answer)
        app.pull()
        assert words in app.words and app.done
        app.draw(screen)
    def no_git(command, **options):
        raise OSError("no git")
    app = box_file.UpdateApp(run=no_git)
    app.pull()
    assert "Couldn't update" in app.words
