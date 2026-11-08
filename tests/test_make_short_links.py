"""Tests for scripts/make_short_links.py"""
from pathlib import Path
import sys

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

from make_short_links import RESERVED, short_links, stub_html, write_stubs  # noqa: E402


def card(icon, href):
    return (f'<article class="card"><img class="card__thumb" src="assets/{icon}">'
            f'<a class="card__play" href="{href}" target="_blank">▶ Play</a></article>')


def test_path_play_links_also_forward_to_the_subdomain():
    html = card("game-wipfelkratzer-icon.png", "https://github.freaxnx01.ch/game-wipfelkratzer/")
    assert short_links(html) == {"wipfelkratzer": "https://wipfelkratzer.freax.games/"}


def test_subdomain_play_links_forward_to_the_subdomain():
    html = card("game-wipfelkratzer-icon.png", "https://wipfelkratzer.freax.games/")
    assert short_links(html) == {"wipfelkratzer": "https://wipfelkratzer.freax.games/"}


def test_a_game_on_its_own_domain_gets_that_domain():
    html = card("game-rhyflitzer-icon.png", "https://rhyflitzer.ch/")
    assert short_links(html) == {"rhyflitzer": "https://rhyflitzer.ch/"}


def test_cards_that_are_not_game_repos_are_skipped():
    html = card("dogwash-icon.png", "https://julia-hase.github.io/dogwash/")
    assert short_links(html) == {}


@pytest.mark.parametrize("name", sorted(RESERVED))
def test_reserved_names_are_refused(name):
    html = card(f"game-{name}-icon.png", f"https://freax.games/game-{name}/")
    with pytest.raises(SystemExit, match=name):
        short_links(html)


def test_stub_keeps_query_and_hash():
    html = stub_html("https://nibbles.freax.games/")
    assert ('location.replace("https://nibbles.freax.games/" + location.search + location.hash)'
            in html)
    assert '<meta name="generator" content="make_short_links">' in html


def test_write_stubs_removes_only_its_own_stale_stubs(tmp_path):
    (tmp_path / "games").mkdir()
    (tmp_path / "games" / "index.html").write_text(
        card("game-nibbles-icon.png", "https://github.freaxnx01.ch/game-nibbles/"))
    (tmp_path / "gone").mkdir()
    (tmp_path / "gone" / "index.html").write_text(stub_html("https://gone.freax.games/"))
    (tmp_path / "keep").mkdir()
    (tmp_path / "keep" / "index.html").write_text("<p>hand-made</p>")
    assert write_stubs(tmp_path) == ["nibbles"]
    assert (tmp_path / "nibbles" / "index.html").exists()
    assert not (tmp_path / "gone").exists()
    assert (tmp_path / "keep" / "index.html").exists()


def test_the_real_hub_gets_a_stub_per_game():
    hub = Path(__file__).parent.parent
    links = short_links((hub / "games" / "index.html").read_text())
    assert len(links) >= 40
    assert links["wipfelkratzer"] == "https://wipfelkratzer.freax.games/"
    assert "dogwash" not in links
