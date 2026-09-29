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


import shutil
import subprocess

from add_fullscreen_toggle import process_repo  # noqa: E402

needs_cliff = pytest.mark.skipif(shutil.which("git-cliff") is None, reason="git-cliff not installed")

CLIFF_TOML = '''[changelog]
header = "# Changelog\\n"
body = """
{% if version %}## [{{ version | trim_start_matches(pat="v") }}]{% else %}## [Unreleased]{% endif %}
{% for commit in commits %}- {{ commit.message | split(pat="\\n") | first }}
{% endfor %}"""
trim = true

[git]
conventional_commits = true
filter_unconventional = false
tag_pattern = "v[0-9].*"
'''

GAME_HTML = """<!doctype html><html><body>
<nav id="game-nav"><span id="version-badge"></span></nav>
</body></html>
"""


@pytest.fixture
def git_identity(monkeypatch):
    for k, v in {
        "GIT_AUTHOR_NAME": "Test", "GIT_AUTHOR_EMAIL": "test@example.com",
        "GIT_COMMITTER_NAME": "Test", "GIT_COMMITTER_EMAIL": "test@example.com",
    }.items():
        monkeypatch.setenv(k, v)


def git(cwd, *args):
    return subprocess.run(["git", "-C", str(cwd), *args], check=True, capture_output=True, text=True).stdout


@pytest.fixture
def remote(tmp_path, git_identity):
    """A bare remote game-demo.git seeded with a game at v0.3.1."""
    base = tmp_path / "remotes"
    bare = base / "game-demo.git"
    git(tmp_path, "init", "-q", "--bare", "-b", "main", str(bare))
    seed = tmp_path / "seed"
    git(tmp_path, "clone", "-q", str(bare), str(seed))
    (seed / "index.html").write_text(GAME_HTML)
    (seed / "version.js").write_text('window.GAME_VERSION = "0.3.1";\n')
    (seed / "cliff.toml").write_text(CLIFF_TOML)
    (seed / "CHANGELOG.md").write_text("# Changelog\n")
    git(seed, "add", ".")
    git(seed, "commit", "-q", "-m", "chore(release): v0.3.1")
    git(seed, "tag", "v0.3.1")
    git(seed, "push", "-q", "--follow-tags", "origin", "main")
    return {"base": f"file://{base}", "bare": bare, "clones": tmp_path / "clones", "tmp": tmp_path}


def remote_file(remote, path, ref="main"):
    return git(remote["bare"], "show", f"{ref}:{path}")


def test_process_repo_injects_releases_and_pushes(remote):
    status = process_repo("game-demo", remote["clones"], remote_base=remote["base"])
    assert status.startswith("succeeded"), status
    assert "v0.4.0" in status
    assert "game-nav-fullscreen:start" in remote_file(remote, "index.html")
    assert '"0.4.0"' in remote_file(remote, "version.js")
    assert "0.4.0" in remote_file(remote, "CHANGELOG.md")
    assert "v0.4.0" in git(remote["bare"], "tag", "--list")
    log = git(remote["bare"], "log", "--format=%s", "-2", "main").splitlines()
    assert log == ["chore(release): v0.4.0", "feat(nav): add fullscreen toggle"]


def test_process_repo_rerun_is_noop(remote):
    process_repo("game-demo", remote["clones"], remote_base=remote["base"])
    head = git(remote["bare"], "rev-parse", "main")
    status = process_repo("game-demo", remote["clones"], remote_base=remote["base"])
    assert status == "skipped: up to date"
    assert git(remote["bare"], "rev-parse", "main") == head


def test_stale_local_tag_from_failed_push_does_not_block(remote):
    # A previous run tagged locally, then the push failed.
    clone = remote["clones"] / "game-demo"
    git(remote["tmp"], "clone", "-q", f"{remote['base']}/game-demo.git", str(clone))
    git(clone, "tag", "v0.4.0")
    status = process_repo("game-demo", remote["clones"], remote_base=remote["base"])
    assert status.startswith("succeeded"), status
    assert "v0.4.0" in git(remote["bare"], "tag", "--list")


def test_existing_remote_tag_fails_without_pushing(remote):
    seed = remote["tmp"] / "seed"
    git(seed, "tag", "v0.4.0")
    git(seed, "push", "-q", "origin", "v0.4.0")
    head = git(remote["bare"], "rev-parse", "main")
    status = process_repo("game-demo", remote["clones"], remote_base=remote["base"])
    assert status.startswith("failed"), status
    assert "v0.4.0" in status and "exists" in status
    assert git(remote["bare"], "rev-parse", "main") == head


def test_dry_run_touches_nothing(remote):
    head = git(remote["bare"], "rev-parse", "main")
    status = process_repo("game-demo", remote["clones"], remote_base=remote["base"], dry_run=True)
    assert status == "would update → v0.4.0 (dry-run)"
    assert git(remote["bare"], "rev-parse", "main") == head
    assert "game-nav-fullscreen" not in (remote["clones"] / "game-demo" / "index.html").read_text()


def test_page_without_nav_is_skipped(remote):
    seed = remote["tmp"] / "seed"
    (seed / "index.html").write_text("<html><body>no nav</body></html>")
    git(seed, "commit", "-q", "-am", "chore: drop nav")
    git(seed, "push", "-q", "origin", "main")
    status = process_repo("game-demo", remote["clones"], remote_base=remote["base"])
    assert status == "skipped: no game-nav"


def test_no_version_js_commits_without_release(remote):
    seed = remote["tmp"] / "seed"
    git(seed, "rm", "-q", "version.js")
    git(seed, "commit", "-q", "-m", "chore: drop version")
    git(seed, "push", "-q", "origin", "main")
    status = process_repo("game-demo", remote["clones"], remote_base=remote["base"])
    assert status == "succeeded (no release: no version.js)"
    assert git(remote["bare"], "log", "--format=%s", "-1", "main").strip() == "feat(nav): add fullscreen toggle"


TEMPLATE = Path(__file__).parent.parent / "docs" / "superpowers" / "specs" / "2026-07-13-game-card-feedback-star-snippet.html"


def test_canonical_template_contains_snippet_verbatim():
    assert load_snippet() in TEMPLATE.read_text()


# --- changelog release section (replaces git-cliff regeneration, which
# --- rewrote hand-curated changelogs) and version.js location -------------

from add_fullscreen_toggle import CHANGELOG_LINE, release_changelog, version_file  # noqa: E402

HEADER = "# Changelog\n\nAll notable changes.\n\n"


def test_version_file_sits_next_to_served_page():
    assert version_file("game-gorillazz") == "docs/version.js"
    assert version_file("game-nibbles") == "version.js"


def test_release_empty_unreleased_keeps_it_on_top():
    text = HEADER + "## [Unreleased]\n\n## [0.1.0] - 2026-07-27\n\n### Added\n- Old\n"
    out = release_changelog(text, "0.2.0", "2026-09-29")
    assert out == (
        HEADER + "## [Unreleased]\n\n"
        "## [0.2.0] - 2026-09-29\n\n### Added\n- " + CHANGELOG_LINE + "\n\n"
        "## [0.1.0] - 2026-07-27\n\n### Added\n- Old\n"
    )


def test_release_moves_curated_unreleased_entries_into_version():
    text = HEADER + (
        "## [Unreleased]\n\n### Added\n- Feature A\n\n### Fixed\n- Bug B\n\n"
        "## [0.1.0] - 2026-07-27\n\n- Old\n"
    )
    out = release_changelog(text, "0.2.0", "2026-09-29")
    assert out == HEADER + (
        "## [Unreleased]\n\n"
        "## [0.2.0] - 2026-09-29\n\n### Added\n- Feature A\n- " + CHANGELOG_LINE + "\n\n### Fixed\n- Bug B\n\n"
        "## [0.1.0] - 2026-07-27\n\n- Old\n"
    )


def test_release_adds_added_subsection_when_missing():
    text = HEADER + "## [Unreleased]\n\n### Fixed\n- Bug B\n\n## [0.1.0] - 2026-07-27\n"
    out = release_changelog(text, "0.2.0", "2026-09-29")
    assert "## [0.2.0] - 2026-09-29\n\n### Added\n- " + CHANGELOG_LINE + "\n\n### Fixed\n- Bug B\n\n## [0.1.0]" in out


def test_release_without_unreleased_goes_above_newest_version():
    text = HEADER + "## [0.2.0] - 2026-08-18\n\n- Old\n"
    out = release_changelog(text, "0.3.0", "2026-09-29")
    assert out == HEADER + (
        "## [0.3.0] - 2026-09-29\n\n### Added\n- " + CHANGELOG_LINE + "\n\n"
        "## [0.2.0] - 2026-08-18\n\n- Old\n"
    )


def test_release_on_header_only_changelog_appends():
    out = release_changelog("# Changelog\n", "0.4.0", "2026-09-29")
    assert out == "# Changelog\n\n## [0.4.0] - 2026-09-29\n\n### Added\n- " + CHANGELOG_LINE + "\n"


def test_release_never_drops_existing_lines():
    text = HEADER + "## [Unreleased]\n\n### Added\n- A\n\n## [0.1.0] - 2026-07-27\n\n- Old\n"
    out = release_changelog(text, "0.2.0", "2026-09-29")
    for line in text.splitlines():
        assert line in out.splitlines()


def test_release_updates_link_references():
    base = "https://github.com/freaxnx01/game-x"
    text = HEADER + (
        "## [Unreleased]\n\n## [0.1.0] - 2026-07-27\n\n- Old\n\n"
        f"[Unreleased]: {base}/compare/v0.1.0...HEAD\n"
        f"[0.1.0]: {base}/releases/tag/v0.1.0\n"
    )
    out = release_changelog(text, "0.2.0", "2026-09-29")
    assert out.endswith(
        f"[Unreleased]: {base}/compare/v0.2.0...HEAD\n"
        f"[0.2.0]: {base}/releases/tag/v0.2.0\n"
        f"[0.1.0]: {base}/releases/tag/v0.1.0\n"
    )
