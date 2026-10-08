# Downloads the AI models into robot-box/models/ (they're too big for GitHub, and not ours to share).
#   python setup/download_models.py                 just what Rock Paper Scissors needs (hands)
#   python setup/download_models.py faces pose      also get these
#   python setup/download_models.py all             everything
#   python setup/download_models.py voice           the robot's Piper voice (Pi only)

import sys
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from core.settings import MODELS_FOLDER, load_config
from core.vision import MODEL_FOR

VOICE_SITE = "https://huggingface.co/rhasspy/piper-voices/resolve/main/"


def download(address, file):
    if file.exists():
        print(f"Already have {file.name}")
        return
    file.parent.mkdir(parents=True, exist_ok=True)
    print(f"Downloading {file.name}...")
    part = file.with_suffix(file.suffix + ".part")      # so a half download is never mistaken for a whole one
    urllib.request.urlretrieve(address, part)
    part.rename(file)


def voice_address(voice):
    """ "en_US-lessac-medium" -> where that Piper voice lives on the internet."""
    language, name, quality = voice.split("-")
    return f"{VOICE_SITE}{language[:2]}/{language}/{name}/{quality}/{voice}.onnx"


def main(wanted):
    wanted = set(wanted or ["hands"])
    if "all" in wanted:
        wanted = set(MODEL_FOR) | {"voice"}
    for kind in sorted(wanted - {"voice"}):
        if kind not in MODEL_FOR:
            raise SystemExit(f"I don't know '{kind}'. Pick from: {', '.join(sorted(MODEL_FOR))}, voice, all")
        file_name, address = MODEL_FOR[kind]
        download(address, MODELS_FOLDER / file_name)
    if "voice" in wanted:
        voice = load_config().get("voice", {}).get("piper_voice", "en_US-lessac-medium")
        address = voice_address(voice)
        download(address, MODELS_FOLDER / "voice" / f"{voice}.onnx")
        download(address + ".json", MODELS_FOLDER / "voice" / f"{voice}.onnx.json")
    print("Done!")


if __name__ == "__main__":
    main(sys.argv[1:])
