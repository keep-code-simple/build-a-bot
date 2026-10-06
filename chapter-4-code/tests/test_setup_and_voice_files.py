import json
import re
from pathlib import Path

import pytest

import make_voice_files
import setup_cloud
from bridge import cloud
from bridge.settings import load_config

HERE = Path(__file__).resolve().parent.parent


# ---------- setup_cloud.py ----------

def test_topics_are_long_random_and_prefixed():
    topics = {setup_cloud.make_topic() for _ in range(200)}
    assert len(topics) == 200                                   # never the same twice
    for topic in topics:
        assert re.fullmatch(r"bab-[A-Za-z0-9_-]{16,}", topic)
        assert cloud.is_real_topic(topic)


def test_build_config_keeps_settings_and_replaces_both_topics():
    example = json.loads((HERE / "config.example.json").read_text())
    old = {**example, "voice": "Fred", "to_robot_topic": "bab-old-one", "from_robot_topic": "bab-old-two"}
    config = setup_cloud.build_config(example, old)
    assert config["voice"] == "Fred"
    assert config["schedule"] == example["schedule"]
    assert config["to_robot_topic"] not in ("bab-old-one", example["to_robot_topic"])
    assert config["to_robot_topic"] != config["from_robot_topic"]


def test_save_makes_a_private_file(tmp_path):
    target = tmp_path / "config.json"
    setup_cloud.save({"a": 1}, target)
    assert json.loads(target.read_text()) == {"a": 1}
    assert target.stat().st_mode & 0o077 == 0                   # nobody else can read it


def test_existing_config_is_never_overwritten_without_asking(tmp_path, monkeypatch, capsys):
    target = tmp_path / "config.json"
    target.write_text(json.dumps({"to_robot_topic": "bab-keep-me-1234567890", "ntfy_server": "x"}))
    monkeypatch.setattr(setup_cloud, "CONFIG_FILE", target)
    monkeypatch.setattr("sys.argv", ["setup_cloud.py"])
    setup_cloud.main()
    assert "bab-keep-me-1234567890" in target.read_text()
    assert "left it alone" in capsys.readouterr().out

    monkeypatch.setattr("sys.argv", ["setup_cloud.py", "--new-topics"])
    monkeypatch.setattr("builtins.input", lambda prompt: "no")
    setup_cloud.main()
    assert "bab-keep-me-1234567890" in target.read_text()

    monkeypatch.setattr("builtins.input", lambda prompt: "yes")
    monkeypatch.setattr(setup_cloud, "save", lambda config: setup_cloud.__dict__["_saved"].append(config))
    setup_cloud._saved = []
    setup_cloud.main()
    assert setup_cloud._saved[0]["to_robot_topic"] != "bab-keep-me-1234567890"


def test_phone_instructions_use_the_root_address_and_json_fields():
    config = {"ntfy_server": "https://ntfy.example", "to_robot_topic": "bab-IN", "from_robot_topic": "bab-OUT"}
    text = setup_cloud.phone_instructions(config)
    assert "URL:           https://ntfy.example/\n" in text
    assert "POST" in text and "JSON" in text
    assert "topic    (Text) = bab-IN" in text and "message  (Text) = Provided Input" in text
    assert "bab-OUT" in text


# ---------- the committed example files hold no secrets ----------

def test_example_config_has_placeholders_not_real_topics():
    example = json.loads((HERE / "config.example.json").read_text())
    assert not cloud.is_real_topic(example["to_robot_topic"])
    assert not cloud.is_real_topic(example["from_robot_topic"])
    assert example["faces"]["notify_names"] is False
    assert example["faces"]["sure_enough"] == 0.45 and example["faces"]["beat_second_by"] == 0.06
    assert example["quiet_hours"] == {"start": "21:00", "end": "07:00"}


def test_load_config_merges_private_settings_over_the_example(tmp_path):
    mine = tmp_path / "config.json"
    mine.write_text(json.dumps({"voice": "Fred", "faces": {"sure_enough": 0.5}}))
    config = load_config(mine)
    assert config["voice"] == "Fred"
    assert config["faces"]["sure_enough"] == 0.5
    assert config["faces"]["beat_second_by"] == 0.06            # still there from the example
    mine.write_text("{ oops")
    with pytest.raises(SystemExit):
        load_config(mine)


# ---------- make_voice_files.py ----------

def test_phrases_get_numbers_greetings_first():
    texts, numbers = make_voice_files.number_phrases(
        {"greetings": ["Hello!", "Welcome back!", " "], "others": ["Hi Kid 1!"]})
    assert texts == ["Hello!", "Welcome back!", "Hi Kid 1!"]
    assert numbers == {"GREETING_FIRST": 1, "GREETING_LAST": 2, "OTHER_FIRST": 3, "OTHER_LAST": 3, "COUNT": 3}


def test_phrases_h_has_numbers_only_no_words_from_the_phrases():
    phrases = json.loads((HERE / "phrases.example.json").read_text())
    texts, numbers = make_voice_files.number_phrases(phrases)
    header = make_voice_files.header_text(numbers)
    assert "#define PHRASE_GREETING_FIRST 1\n" in header
    assert f"#define PHRASE_GREETING_LAST {len(phrases['greetings'])}\n" in header
    for code_line in header.splitlines():
        if not code_line.startswith("//"):
            assert re.fullmatch(r"#define PHRASE_[A-Z_]+ \d+", code_line)
    assert "Kid" not in header and not any(text in header for text in texts)


def test_no_greetings_is_refused():
    with pytest.raises(SystemExit):
        make_voice_files.number_phrases({"greetings": []})
