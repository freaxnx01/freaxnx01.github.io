#!/usr/bin/env python3
"""Short paths for the games hub: freax.games/<name> forwards to the game.

One stub <name>/index.html per game card, generated from games/index.html. Run after
adding a card:  python3 scripts/make_short_links.py
Spec: docs/superpowers/specs/2026-11-07-short-domains-design.md
"""
import html as htmllib
import re
import shutil
from pathlib import Path

from hubsite import PLAY_RE

ARTICLE_RE = re.compile(r'<article class="card"[^>]*>(.*?)</article>', re.DOTALL)
ICON_RE = re.compile(r'<img class="card__thumb" src="assets/game-([a-z0-9-]+)-icon\.png"')
ANY_PLAY_RE = re.compile(r'class="card__play" href="(https://[^"]+)"')
RESERVED = {"games", "docs", "scripts", "testhub", "tests", "assets"}
MARKER = '<meta name="generator" content="make_short_links">'


def short_links(page: str) -> dict[str, str]:
    links = {}
    for block in ARTICLE_RE.findall(page):
        icon = ICON_RE.search(block)
        if not icon:
            continue
        name = icon.group(1)
        if name in RESERVED:
            raise SystemExit(f"game-{name}: short name '{name}' clashes with a hub directory")
        site = PLAY_RE.search(block)
        if site:
            links[name] = f"/{site.group(1)}/"
            continue
        other = ANY_PLAY_RE.search(block)
        if other:
            links[name] = other.group(1)
    return links


def stub_html(target: str) -> str:
    t = htmllib.escape(target)
    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
{MARKER}
<title>Redirecting…</title>
<meta http-equiv="refresh" content="0; url={t}">
<script>location.replace("{target}" + location.search + location.hash);</script>
</head>
<body>
<p><a href="{t}">Play</a></p>
</body>
</html>
"""


def write_stubs(hub_root: Path) -> list[str]:
    links = short_links((hub_root / "games" / "index.html").read_text())
    for d in hub_root.iterdir():
        stub = d / "index.html"
        if d.is_dir() and d.name not in links and stub.exists() and MARKER in stub.read_text():
            shutil.rmtree(d)
    for name, target in links.items():
        (hub_root / name).mkdir(exist_ok=True)
        (hub_root / name / "index.html").write_text(stub_html(target))
    return sorted(links)


if __name__ == "__main__":
    names = write_stubs(Path(__file__).resolve().parent.parent)
    print(f"{len(names)} short links: " + ", ".join(names))
