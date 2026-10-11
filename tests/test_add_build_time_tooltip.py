"""Tests for scripts/add_build_time_tooltip.py."""
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

from add_build_time_tooltip import (  # noqa: E402
    CHANGELOG_LINE,
    END_MARKER,
    START_MARKER,
    add_unreleased_line,
    has_version_badge,
    inject_snippet,
    load_snippet,
    served_file,
)
from add_fullscreen_toggle import END_MARKER as FULLSCREEN_END  # noqa: E402

SNIP = f"{START_MARKER}\n<script>x()</script>\n{END_MARKER}"


def test_load_snippet_is_marker_delimited():
    s = load_snippet()
    assert s.startswith(START_MARKER)
    assert s.endswith(END_MARKER)


def test_inject_goes_right_after_the_fullscreen_block():
    html = f"<body><nav id='game-nav'></nav>fs{FULLSCREEN_END}\n<p>tail</p></body>"
    new, changed = inject_snippet(html, SNIP)
    assert changed
    assert new == f"<body><nav id='game-nav'></nav>fs{FULLSCREEN_END}\n{SNIP}\n<p>tail</p></body>"


def test_inject_before_body_close_without_a_fullscreen_block():
    html = "<html><body><span id='version-badge'></span></body></html>"
    new, changed = inject_snippet(html, SNIP)
    assert changed
    assert new == f"<html><body><span id='version-badge'></span>{SNIP}\n</body></html>"


def test_inject_is_idempotent():
    html = f"<body>{FULLSCREEN_END}</body>"
    once, _ = inject_snippet(html, SNIP)
    twice, changed = inject_snippet(once, SNIP)
    assert not changed
    assert twice == once


def test_inject_refreshes_an_outdated_block():
    old = f"<body>{START_MARKER}\n<script>old()</script>\n{END_MARKER}</body>"
    new, changed = inject_snippet(old, SNIP)
    assert changed
    assert new == f"<body>{SNIP}</body>"


def test_inject_without_anchor_raises():
    with pytest.raises(ValueError):
        inject_snippet("<div>no body close</div>", SNIP)


def test_has_version_badge_ignores_our_own_snippet():
    assert has_version_badge("<span id='version-badge'></span>")
    assert not has_version_badge(f"<body>{load_snippet()}</body>")


def test_served_file_knows_the_odd_ones():
    assert served_file("game-nibbles") == "index.html"
    assert served_file("game-gorillazz") == "docs/index.html"
    assert served_file("game-rhyflitzer") == "prototype/index.html"


def test_changelog_line_joins_an_existing_added_list():
    text = "# Changelog\n\n## [Unreleased]\n\n### Added\n\n- One\n- Two\n\n### Fixed\n\n- Bug\n\n## [0.2.0] - 2026-09-30\n\n### Added\n- Old\n"
    assert add_unreleased_line(text) == (
        "# Changelog\n\n## [Unreleased]\n\n### Added\n\n- One\n- Two\n"
        f"- {CHANGELOG_LINE}\n\n### Fixed\n\n- Bug\n\n## [0.2.0] - 2026-09-30\n\n### Added\n- Old\n")


def test_changelog_line_opens_added_in_an_empty_unreleased():
    text = "# Changelog\n\n## [Unreleased]\n\n## [0.2.0] - 2026-09-30\n\n### Added\n- Old\n"
    assert add_unreleased_line(text) == (
        f"# Changelog\n\n## [Unreleased]\n\n### Added\n- {CHANGELOG_LINE}\n\n## [0.2.0] - 2026-09-30\n\n### Added\n- Old\n")


def test_changelog_line_puts_added_before_other_unreleased_groups():
    text = "# Changelog\n\n## [Unreleased]\n\n### Fixed\n- Bug\n\n## [0.2.0] - 2026-09-30\n"
    assert add_unreleased_line(text) == (
        f"# Changelog\n\n## [Unreleased]\n\n### Added\n- {CHANGELOG_LINE}\n\n### Fixed\n- Bug\n\n## [0.2.0] - 2026-09-30\n")


def test_changelog_gets_an_unreleased_section_when_it_has_none():
    text = "# Changelog\n\nIntro.\n\n## [0.2.0] - 2026-09-30\n\n### Added\n- Old\n"
    assert add_unreleased_line(text) == (
        f"# Changelog\n\nIntro.\n\n## [Unreleased]\n\n### Added\n- {CHANGELOG_LINE}\n\n"
        "## [0.2.0] - 2026-09-30\n\n### Added\n- Old\n")


def test_changelog_keeps_link_references_at_the_bottom():
    text = ("# Changelog\n\n## [Unreleased]\n\n### Added\n- One\n\n"
            "[Unreleased]: https://github.com/o/r/compare/v0.2.0...HEAD\n")
    assert add_unreleased_line(text) == (
        f"# Changelog\n\n## [Unreleased]\n\n### Added\n- One\n- {CHANGELOG_LINE}\n\n"
        "[Unreleased]: https://github.com/o/r/compare/v0.2.0...HEAD\n")


def test_changelog_line_is_not_added_twice():
    text = "# Changelog\n\n## [Unreleased]\n\n### Added\n- One\n\n## [0.2.0] - 2026-09-30\n"
    once = add_unreleased_line(text)
    assert add_unreleased_line(once) == once


TEMPLATE = Path(__file__).parent.parent / "docs" / "superpowers" / "specs" / "2026-07-13-game-card-feedback-star-snippet.html"


def test_canonical_template_contains_snippet_verbatim():
    assert load_snippet() in TEMPLATE.read_text()
