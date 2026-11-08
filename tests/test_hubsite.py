"""Tests for scripts/hubsite.py"""
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

from hubsite import game_url, play_repo, subdomain  # noqa: E402


def link(href):
    return f'<a class="card__play" href="{href}" target="_blank">▶ Play</a>'


def test_all_three_play_link_forms_name_the_repo():
    for href in ("https://github.freaxnx01.ch/game-nibbles/",
                 "https://freax.games/game-nibbles/",
                 "https://nibbles.freax.games/"):
        assert play_repo(link(href)) == "game-nibbles"


def test_foreign_and_special_links_are_not_games():
    for href in ("https://julia-hase.github.io/dogwash/", "https://rhyflitzer.ch/",
                 "https://rhyflitzer.freax.games/", "https://www.freax.games/",
                 "https://freax.games/games/"):
        assert play_repo(link(href)) is None


def test_game_url_and_subdomain():
    assert subdomain("game-zen-sudoku") == "zen-sudoku.freax.games"
    assert game_url("game-zen-sudoku") == "https://zen-sudoku.freax.games/"
