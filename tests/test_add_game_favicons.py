"""Tests for scripts/add_game_favicons.py"""
import pytest
from pathlib import Path
import sys

# Add scripts directory to path to import the module
sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

from add_game_favicons import discover_games


def test_discover_games_sanity_floor():
    """Test that discover_games finds at least 30 games.

    A loose floor rather than an exact count, so this doesn't break every
    time a game card is added or removed from the hub.
    """
    games = discover_games(Path("."))
    assert len(games) >= 30, f"Expected at least 30 games, found {len(games)}"


def test_discover_games_structural_invariants():
    """Every discovered game has a repo prefixed 'game-' and an icon that exists on disk."""
    games = discover_games(Path("."))
    for game in games:
        assert game["repo"].startswith("game-"), (
            f"repo {game['repo']!r} does not start with 'game-'"
        )
        assert game["icon_path"].exists(), (
            f"icon_path {game['icon_path']} does not exist on disk"
        )


def test_discover_games_excludes_dogwash():
    """Test that dogwash (external game) is not parsed."""
    games = discover_games(Path("."))
    repos = {g["repo"] for g in games}
    assert "dogwash" not in repos, "dogwash should not be in parsed repos"


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


def test_generate_favicon_bytes_center_crop(tmp_path):
    """Verify generate_favicon_bytes center-crops before resizing.

    Builds a synthetic 400x250 image with a red band on the left, a green
    band exactly matching the algorithm's 250px-wide center-crop region,
    and a blue band on the right. If the crop happens before resizing, the
    *entire* 32x32 output is sampled only from the green band — including
    pixels near its left/right edges. A naive resize with no crop would
    instead stretch the whole 400px width into the output, so those same
    edge pixels would come out red/blue instead of green. Checking only the
    exact center pixel would NOT distinguish the two cases (the crop is
    symmetric, so the center column maps to the same source pixel either
    way) — checking near-edge pixels is what actually proves the crop ran.
    """
    from PIL import Image
    import io
    from add_game_favicons import generate_favicon_bytes

    width, height = 400, 250
    side = min(width, height)  # 250 - the center-crop region width
    left = (width - side) // 2  # 75

    img = Image.new("RGB", (width, height), (255, 0, 0))  # red left/right bands
    green_region = Image.new("RGB", (side, height), (0, 255, 0))
    img.paste(green_region, (left, 0))
    blue_region = Image.new("RGB", (width - (left + side), height), (0, 0, 255))
    img.paste(blue_region, (left + side, 0))

    icon_path = tmp_path / "synthetic-icon.png"
    img.save(icon_path)

    favicon_bytes = generate_favicon_bytes(icon_path)
    out = Image.open(io.BytesIO(favicon_bytes)).convert("RGB")

    for x, y in [(16, 16), (2, 16), (29, 16), (2, 2), (29, 29)]:
        r, g, b = out.getpixel((x, y))
        assert g > r + 50 and g > b + 50, (
            f"pixel ({x},{y}) = {(r, g, b)} is not green-dominant; a naive "
            "resize (without center-crop) would leak red/blue bands into "
            "the output"
        )


def test_ensure_favicon_link_plain_head_no_icon():
    """Test inserting favicon link into plain <head> with no existing icon."""
    from add_game_favicons import ensure_favicon_link, LINK_TAG

    # Test case 1: html with a plain <head> (no attrs), no existing icon link
    html1 = '<!DOCTYPE html>\n<html>\n<head>\n<meta charset="utf-8">\n</head>\n<body></body></html>'
    new1, changed1 = ensure_favicon_link(html1)

    assert changed1 is True, "Expected changed=True when inserting link"
    assert LINK_TAG in new1, f"Expected exact LINK_TAG {LINK_TAG!r} to be present in output"
    assert f"<head>\n{LINK_TAG}" in new1, "Expected link tag right after <head>"


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
