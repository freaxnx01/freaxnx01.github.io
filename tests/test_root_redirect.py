"""freax.games/ is the games hub itself; the old /games/ path forwards to the root."""
from pathlib import Path

ROOT = Path(__file__).parent.parent


def test_root_is_the_games_hub():
    page = (ROOT / "index.html").read_text()
    assert "Browser Games Hub" in page
    assert '<link rel="stylesheet" href="style.css">' in page
    assert 'class="card"' in page
    assert "location.replace" not in page
    assert 'http-equiv="refresh"' not in page


def test_old_games_path_forwards_to_the_root():
    page = (ROOT / "games" / "index.html").read_text()
    assert 'location.replace("/" + location.search + location.hash)' in page
    assert 'content="0; url=/"' in page
    assert '<link rel="canonical" href="https://freax.games/">' in page
    assert sorted(p.name for p in (ROOT / "games").iterdir()) == ["index.html"]


def test_hub_files_live_at_the_root():
    for name in ("style.css", "filter.js", "lightbox.js", "favicon.svg",
                 "favicon-32.png", "apple-touch-icon.png"):
        assert (ROOT / name).is_file(), name
    assert (ROOT / "assets" / "game-nibbles-icon.png").is_file()


def test_old_start_page_is_kept():
    assert "Browser Games Hub" in (ROOT / "links.md").read_text()
