# High scores: saving, reloading, and surviving a missing or scrambled file.
from core.scores import Scores


def test_save_and_reload(tmp_path):
    file = tmp_path / "data" / "scores.json"
    scores = Scores(file)
    assert scores.best("rps", "Kid 1") is None
    assert scores.record("rps", "Kid 1", 2) is True
    assert scores.record("rps", "Kid 1", 1) is False            # not better
    assert scores.record("rps", "Kid 2", 5) is True
    again = Scores(file)                                        # like restarting the box
    assert again.best("rps", "Kid 1") == 2
    assert again.table("rps") == [("Kid 2", 5), ("Kid 1", 2)]


def test_lower_is_better_for_reaction_times(tmp_path):
    scores = Scores(tmp_path / "scores.json")
    assert scores.record("reaction", "Kid 1", 300, higher_is_better=False)
    assert not scores.record("reaction", "Kid 1", 350, higher_is_better=False)
    assert scores.record("reaction", "Kid 1", 250, higher_is_better=False)
    scores.record("reaction", "Kid 2", 280, higher_is_better=False)
    assert scores.table("reaction", higher_is_better=False) == [("Kid 1", 250), ("Kid 2", 280)]


def test_it_only_writes_when_a_score_changes(tmp_path):
    file = tmp_path / "scores.json"
    scores = Scores(file)
    scores.record("rps", "Kid 1", 3)
    file.unlink()
    scores.record("rps", "Kid 1", 2)                            # not a record: no write
    assert not file.exists()


def test_missing_or_scrambled_file_does_not_crash(tmp_path):
    file = tmp_path / "scores.json"
    for junk in ["{ this is not json", "[1, 2, 3]", ""]:
        file.write_text(junk)
        scores = Scores(file)
        assert scores.table("rps") == []
        assert scores.record("rps", "Kid 1", 1)


def test_a_card_that_cannot_be_written_does_not_crash(tmp_path):
    blocker = tmp_path / "blocker"
    blocker.write_text("a file where a folder should be")
    scores = Scores(blocker / "scores.json")
    assert scores.record("rps", "Kid 1", 1)                     # kept in memory, game goes on
    assert scores.best("rps", "Kid 1") == 1
