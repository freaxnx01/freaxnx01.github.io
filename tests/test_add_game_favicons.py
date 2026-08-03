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
