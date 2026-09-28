"""Tests for scripts/add_fullscreen_toggle.py (issue #25)."""
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

from add_fullscreen_toggle import (  # noqa: E402
    END_MARKER,
    START_MARKER,
    bump_minor,
    has_game_nav,
    inject_snippet,
    load_snippet,
    read_version,
    served_file,
    write_version,
)

SNIP = f"{START_MARKER}\n<script>x()</script>\n{END_MARKER}"


def test_load_snippet_is_marker_delimited():
    s = load_snippet()
    assert s.startswith(START_MARKER)
    assert s.endswith(END_MARKER)


def test_inject_before_body_close():
    html = "<html><body><nav id='game-nav'></nav></body></html>"
    new, changed = inject_snippet(html, SNIP)
    assert changed
    assert new == f"<html><body><nav id='game-nav'></nav>{SNIP}\n</body></html>"


def test_inject_uses_last_body_close_case_insensitive():
    html = "<body><script>var t='</body>';</script></BODY></html>"
    new, changed = inject_snippet(html, SNIP)
    assert changed
    assert new == f"<body><script>var t='</body>';</script>{SNIP}\n</BODY></html>"


def test_inject_is_idempotent():
    html = "<body></body>"
    once, _ = inject_snippet(html, SNIP)
    twice, changed = inject_snippet(once, SNIP)
    assert not changed
    assert twice == once


def test_inject_replaces_outdated_block():
    old = f"<body>{START_MARKER}\n<script>old()</script>\n{END_MARKER}\n</body>"
    new, changed = inject_snippet(old, SNIP)
    assert changed
    assert new == f"<body>{SNIP}\n</body>"
    assert new.count(START_MARKER) == 1


def test_inject_without_body_raises():
    with pytest.raises(ValueError, match="</body>"):
        inject_snippet("<div>no body close</div>", SNIP)


def test_inject_defaults_to_real_snippet():
    new, changed = inject_snippet("<body></body>")
    assert changed
    assert load_snippet() in new


def test_has_game_nav_static_and_selfhealing():
    assert has_game_nav('<nav id="game-nav">')
    assert has_game_nav('nav.id = "game-nav";')
    assert not has_game_nav("<body>plain</body>")


def test_has_game_nav_ignores_own_snippet():
    html = f"<body>{load_snippet()}\n</body>"
    assert not has_game_nav(html)


def test_read_and_write_version():
    js = '// mirror\nwindow.GAME_VERSION = "0.11.1";\n'
    assert read_version(js) == "0.11.1"
    assert write_version(js, "0.12.0") == '// mirror\nwindow.GAME_VERSION = "0.12.0";\n'
    assert read_version("// nothing here\n") is None


@pytest.mark.parametrize("old,new", [
    ("0.1.0", "0.2.0"),
    ("0.11.1", "0.12.0"),
    ("1.9.9", "1.10.0"),
])
def test_bump_minor(old, new):
    assert bump_minor(old) == new


def test_bump_minor_rejects_garbage():
    with pytest.raises(ValueError):
        bump_minor("v1.2")


def test_served_file():
    assert served_file("game-gorillazz") == "docs/index.html"
    assert served_file("game-nibbles") == "index.html"
