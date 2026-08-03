"""Tests for scripts/add_game_favicons.py"""
import pytest
from pathlib import Path
import sys

# Add scripts directory to path to import the module
sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

from add_game_favicons import discover_games


def test_discover_games_count():
    """Test that discover_games finds exactly 37 games."""
    games = discover_games(Path("."))
    assert len(games) == 37, f"Expected 37 games, found {len(games)}"


def test_discover_games_excludes_dogwash():
    """Test that dogwash (external game) is not parsed."""
    games = discover_games(Path("."))
    repos = {g["repo"] for g in games}
    assert "dogwash" not in repos, "dogwash should not be in parsed repos"


def test_discover_games_first_five_sorted_repos():
    """Test that the first 5 sorted repo names match expected values."""
    games = discover_games(Path("."))
    repos = sorted({g["repo"] for g in games})
    expected_first_five = [
        "game-acronym-quiz",
        "game-aerodrome-apex",
        "game-barrel-shooter",
        "game-battleship-toys",
        "game-beach-buggy-racer",
    ]
    assert repos[:5] == expected_first_five, f"First 5 repos don't match. Got {repos[:5]}"


def test_discover_games_returns_dicts_with_repo_and_icon_path():
    """Test that discover_games returns dicts with 'repo' and 'icon_path' keys."""
    games = discover_games(Path("."))
    assert len(games) > 0, "No games found"

    for game in games:
        assert isinstance(game, dict), "Game should be a dict"
        assert "repo" in game, "Game dict should have 'repo' key"
        assert "icon_path" in game, "Game dict should have 'icon_path' key"
        assert isinstance(game["repo"], str), "repo should be a string"
        assert isinstance(game["icon_path"], Path), "icon_path should be a Path"


def test_generate_favicon_bytes():
    """Test that generate_favicon_bytes returns a 32x32 PNG image."""
    import io
    from PIL import Image
    from add_game_favicons import generate_favicon_bytes

    # Use the game-nibbles-icon.png as test input (400x250)
    icon_path = Path("games/assets/game-nibbles-icon.png")

    # Generate favicon bytes
    favicon_bytes = generate_favicon_bytes(icon_path)

    # Verify it's valid PNG bytes that decode to 32x32
    img = Image.open(io.BytesIO(favicon_bytes))
    assert img.size == (32, 32), f"Expected (32, 32), got {img.size}"
    assert img.format == "PNG", f"Expected PNG format, got {img.format}"


def test_ensure_favicon_link_plain_head_no_icon():
    """Test inserting favicon link into plain <head> with no existing icon."""
    from add_game_favicons import ensure_favicon_link

    # Test case 1: html with a plain <head> (no attrs), no existing icon link
    html1 = '<!DOCTYPE html>\n<html>\n<head>\n<meta charset="utf-8">\n</head>\n<body></body></html>'
    new1, changed1 = ensure_favicon_link(html1)

    assert changed1 is True, "Expected changed=True when inserting link"
    assert '<link rel="icon"' in new1, "Expected link tag to be present in output"
    assert '<head>\n<link rel="icon"' in new1, "Expected link tag right after <head>"


def test_ensure_favicon_link_head_with_attrs_existing_icon():
    """Test idempotency when icon link already exists."""
    from add_game_favicons import ensure_favicon_link

    # Test case 2: html with <head lang="en"> that already has a <link rel="icon">
    html2 = '<html>\n<head lang="en">\n<link rel="icon" href="x.png">\n</head>\n<body></body></html>'
    new2, changed2 = ensure_favicon_link(html2)

    assert changed2 is False, "Expected changed=False when icon already exists"
    assert new2 == html2, "Expected html to be unchanged when icon already exists"


def test_ensure_favicon_link_no_head_tag_raises():
    """Test that ValueError is raised when no <head> tag exists."""
    from add_game_favicons import ensure_favicon_link

    # Test case 3: html with no <head> tag
    html3 = '<html>\n<body>Hello</body>\n</html>'

    with pytest.raises(ValueError) as exc_info:
        ensure_favicon_link(html3)

    assert str(exc_info.value) == "no <head> tag found in index.html"
