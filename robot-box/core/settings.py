# Loads the box's settings.
# config.json is YOUR private copy (real names, never on GitHub).
# If it doesn't exist yet, the box uses config.example.json.

import json
from pathlib import Path

BOX_FOLDER = Path(__file__).resolve().parent.parent
CONFIG_FILE = BOX_FOLDER / "config.json"
EXAMPLE_FILE = BOX_FOLDER / "config.example.json"
MODELS_FOLDER = BOX_FOLDER / "models"
DATA_FOLDER = BOX_FOLDER / "data"


def load_config(config_file=CONFIG_FILE, example_file=EXAMPLE_FILE):
    config = json.loads(Path(example_file).read_text())
    if Path(config_file).exists():
        try:
            config.update(json.loads(Path(config_file).read_text()))
        except json.JSONDecodeError as problem:
            raise SystemExit(f"config.json has a typo: {problem}")
    return config
