"""Headless end-to-end tests for testhub/: the hub and a fake game in two pages of one browser context."""
import re
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

import pytest
from playwright.sync_api import expect, sync_playwright

ROOT = Path(__file__).parent.parent
FIXTURES = Path(__file__).parent / "testhub" / "fixtures"
ORIGIN = "http://localhost:4173"
TZ = "Europe/Zurich"
TYPES = {".html": "text/html; charset=utf-8", ".js": "text/javascript; charset=utf-8",
         ".css": "text/css; charset=utf-8", ".md": "text/markdown; charset=utf-8"}


def serve(route, request, todo):
    path = request.url.removeprefix(ORIGIN).split("?")[0]
    source = None
    if path == "/game-fake/test-todo.md":
        source = FIXTURES / "test-todo.md" if todo else None
    elif path == "/game-fake/":
        source = FIXTURES / "fake-game.html"
    elif path == "/testhub/":
        source = ROOT / "testhub" / "index.html"
    elif path.startswith("/testhub/") and ".." not in path:
        source = ROOT / path.lstrip("/")
    if source is None or not source.is_file():
        return route.fulfill(status=404, body="not found")
    route.fulfill(status=200, body=source.read_bytes(), content_type=TYPES.get(source.suffix, "application/octet-stream"))


def new_context(browser, todo=True, **kwargs):
    ctx = browser.new_context(locale="en-GB", timezone_id=TZ, accept_downloads=True,
                              permissions=["clipboard-read", "clipboard-write"], **kwargs)
    ctx.route(f"{ORIGIN}/**", lambda route, request: serve(route, request, todo))
    return ctx


def open_game(ctx):
    game = ctx.new_page()
    game.goto(f"{ORIGIN}/game-fake/")
    return game


def open_hub(ctx, errors=None, init_script=None):
    hub = ctx.new_page()
    if errors is not None:
        hub.on("pageerror", lambda e: errors.append(str(e)))
    if init_script:
        hub.add_init_script(init_script)
    hub.goto(f"{ORIGIN}/testhub/?game=fake")
    expect(hub.locator(".status")).to_be_visible()
    return hub


def item(hub, text):
    return hub.locator(".item", has_text=text)


@pytest.fixture(scope="module")
def browser():
    with sync_playwright() as p:
        b = p.chromium.launch()
        yield b
        b.close()


@pytest.fixture
def ctx(browser):
    c = new_context(browser)
    yield c
    c.close()


def test_list_showsOpenItemsOnly_tagsStripped_noGameIsRed(ctx):
    errors = []
    hub = open_hub(ctx, errors)
    expect(hub.locator(".item")).to_have_count(4)
    expect(item(hub, "Second item has its own tag")).to_have_text(re.compile(r"^\s*☐ Second item has its own tag\s*Go"))
    expect(hub.locator(".block", has_text="Alpha block").locator(".progress")).to_have_text("0 / 2 ✓")
    expect(hub.locator(".status.off")).to_contain_text("No game window")
    expect(hub.locator(".status a")).to_have_attribute("href", "/game-fake/?dev=1")
    expect(item(hub, "First item").locator("button.go")).to_be_disabled()
    assert errors == []


def test_missingTodo_showsMessage_hubStillOpens(browser):
    ctx = new_context(browser, todo=False)
    try:
        hub = open_hub(ctx)
        expect(hub.locator(".load-error")).to_contain_text("Could not load test-todo.md for fake")
        expect(hub.locator(".toolbar")).to_be_visible()
    finally:
        ctx.close()


def test_storageUnavailable_warnsAndStillRenders(ctx):
    hub = open_hub(ctx, init_script="Object.defineProperty(window,'localStorage',{get(){throw new Error('denied')}})")
    expect(hub.locator(".notice.warn")).to_contain_text("notes are kept for this session only")
    expect(hub.locator(".item")).to_have_count(4)
