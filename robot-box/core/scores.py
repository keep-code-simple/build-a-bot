# High scores, saved in a small file on the box (data/scores.json).
# The file only gets written when a score actually changes. That's kind to the SD card.

import json
from pathlib import Path


class Scores:
    def __init__(self, file):
        self.file = Path(file)
        self.games = self._load()         # {"rps": {"Kid 1": 4}, "reaction": {"Kid 2": 231}}

    def _load(self):
        try:
            games = json.loads(self.file.read_text())
            return games if isinstance(games, dict) else {}
        except (OSError, ValueError):     # no file yet, or the file got scrambled: start fresh
            return {}

    def best(self, game, player):
        """This player's best score in this game, or None if they haven't played."""
        return self.games.get(game, {}).get(player)

    def record(self, game, player, score, higher_is_better=True):
        """Saves the score if it beats the player's best. Returns True for a new record."""
        old = self.best(game, player)
        if old is not None:
            if (score <= old) if higher_is_better else (score >= old):
                return False
        self.games.setdefault(game, {})[player] = score
        self._save()
        return True

    def table(self, game, higher_is_better=True):
        """The leaderboard: a list of (player, score), best first."""
        players = self.games.get(game, {})
        return sorted(players.items(), key=lambda row: row[1], reverse=higher_is_better)

    def _save(self):
        try:
            self.file.parent.mkdir(parents=True, exist_ok=True)
            self.file.write_text(json.dumps(self.games, indent=2))
        except OSError:
            pass                          # a full or broken card must not crash the game
