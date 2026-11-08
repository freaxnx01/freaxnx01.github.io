"""Tests for scripts/hubsite.py"""
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

from hubsite import PLAY_RE, SITE, SITE_HOSTS, game_url  # noqa: E402


def test_play_links_on_either_domain_name_the_repo():
    for host in ("github.freaxnx01.ch", "freax.games"):
        m = PLAY_RE.search(f'<a class="card__play" href="https://{host}/game-nibbles/" target="_blank">')
        assert m and m.group(1) == "game-nibbles"


def test_foreign_play_links_do_not_match():
    assert not PLAY_RE.search('href="https://julia-hase.github.io/dogwash/"')
    assert not PLAY_RE.search('href="https://rhyflitzer.ch/"')


def test_game_url_uses_the_current_site():
    assert game_url("game-nibbles") == f"{SITE}/game-nibbles/"
    assert SITE.split("//")[1] in SITE_HOSTS
