"""Tests for scripts/capture_screenshots.py"""
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

from capture_screenshots import MANUAL_IMAGES, REPOS, repos_to_capture


def test_full_run_skips_hand_made_images():
    repos = repos_to_capture([])
    assert "game-rhyflitzer" not in repos
    assert not MANUAL_IMAGES & set(repos)
    assert set(repos) | MANUAL_IMAGES == set(REPOS)


def test_naming_a_repo_still_captures_it():
    assert repos_to_capture(["game-rhyflitzer"]) == ["game-rhyflitzer"]


def test_hand_made_images_are_known_repos():
    assert MANUAL_IMAGES <= set(REPOS)
