# Reads the settings file.
# config.json is PRIVATE (it holds the secret topic names) and is made by setup_cloud.py.
# Until it exists, the safe example settings are used and the phone features stay off.

import json
from pathlib import Path

HERE = Path(__file__).resolve().parent.parent
CONFIG_FILE = HERE / "config.json"
EXAMPLE_FILE = HERE / "config.example.json"


def load_config(config_file=CONFIG_FILE, example_file=EXAMPLE_FILE):
    config = json.loads(Path(example_file).read_text())
    if Path(config_file).exists():
        try:
            mine = json.loads(Path(config_file).read_text())
        except ValueError as problem:
            raise SystemExit(f"config.json has a typo: {problem}\n"
                             "Check for a missing comma or quote mark.")
        faces = {**config.get("faces", {}), **mine.get("faces", {})}
        config.update(mine)                # your settings win over the example ones
        config["faces"] = faces
    return config
