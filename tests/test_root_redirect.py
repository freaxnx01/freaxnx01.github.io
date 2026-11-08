"""freax.games/ opens the games hub (root index.html forwards to /games/)."""
from pathlib import Path

ROOT = Path(__file__).parent.parent


def test_root_forwards_to_the_games_hub():
    page = (ROOT / "index.html").read_text()
    assert 'location.replace("/games/" + location.search + location.hash)' in page
    assert 'content="0; url=/games/"' in page


def test_old_start_page_is_kept():
    assert "Browser Games Hub" in (ROOT / "links.md").read_text()
