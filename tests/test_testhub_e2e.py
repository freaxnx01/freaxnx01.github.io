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


def mmdd():
    return datetime.now(ZoneInfo(TZ)).strftime("%m%d")


def test_connected_greyTag_lateTarget_goRunsInGame(ctx):
    game = open_game(ctx)
    hub = open_hub(ctx)
    expect(hub.locator(".status.on")).to_contain_text("v1.2.3 · 2 targets")  # fake.beta registers 200 ms late
    expect(item(hub, "Typo tag item").locator(".go-unknown")).to_have_text("fake.typo")
    item(hub, "First item inherits").locator("button.go").click()
    game.wait_for_function("window.__at === 'alpha'")
    item(hub, "Second item").locator("button.go").click()
    game.wait_for_function("window.__at === 'beta'")


def test_screenshot_downloadsNumberedFiles(ctx):
    open_game(ctx)
    hub = open_hub(ctx)
    expect(hub.locator(".status.on")).to_be_visible()
    row = item(hub, "First item inherits")
    row.locator("button.text").click()
    with hub.expect_download() as first:
        row.locator("button.shot").click()
    assert first.value.suggested_filename == f"fb-fake-{mmdd()}-1.png"
    expect(row.locator(".chip")).to_have_text(f"📷 fb-fake-{mmdd()}-1.png ✓")
    with hub.expect_download() as second:
        row.locator("button.shot").click()
    assert second.value.suggested_filename == f"fb-fake-{mmdd()}-2.png"


def test_screenshot_withoutAnswer_showsTimeoutError(ctx):
    game = open_game(ctx)
    game.evaluate("window.__shot = 'hang'")
    hub = ctx.new_page()
    hub.clock.install()
    hub.goto(f"{ORIGIN}/testhub/?game=fake")
    expect(hub.locator(".status.on")).to_be_visible()
    row = item(hub, "First item inherits")
    row.locator("button.text").click()
    row.locator("button.shot").click()
    hub.clock.run_for(11000)
    expect(row.locator(".error")).to_contain_text("No answer from the game within 10 s")


def test_screenshot_rejected_showsGameMessage_andStoresNothing(ctx):
    game = open_game(ctx)
    game.evaluate("window.__shot = 'reject'")
    hub = open_hub(ctx)
    expect(hub.locator(".status.on")).to_be_visible()
    row = item(hub, "First item inherits")
    row.locator("button.text").click()
    row.locator("button.shot").click()
    expect(row.locator(".error")).to_have_text("photo failed")


def add_note(hub, text, note):
    row = item(hub, text)
    row.locator("button.text").click()
    row.locator("textarea.note").fill(note)
    row.locator("button.save").click()


def test_noteAndDone_copyAllExportsExactBlock_andMarksSent(ctx):
    open_game(ctx)
    hub = open_hub(ctx)
    expect(hub.locator(".status.on")).to_be_visible()
    add_note(hub, "First item inherits", "Turm zu dunkel")
    typo = item(hub, "Typo tag item")
    typo.locator("button.text").click()
    typo.locator("button.done").click()
    expect(hub.locator("button.copy-all")).to_have_text("Copy all 2")
    hub.bring_to_front()
    hub.locator("button.copy-all").click()
    expect(hub.locator(".notice.ok")).to_contain_text("Copied 2 entries")
    date = datetime.now(ZoneInfo(TZ)).strftime("%Y-%m-%d")
    assert hub.evaluate("navigator.clipboard.readText()") == "\n".join([
        f"Testhub feedback — fake v1.2.3 — {date}",
        '- [Alpha block · "First item inherits the block tag" · go:fake.alpha] Turm zu dunkel',
        '- ✓ tested: [Beta block · "Typo tag item"]',
    ])
    expect(hub.locator("button.copy-all")).to_have_text("Copy all 0")
    expect(hub.locator("button.copy-all")).to_be_disabled()


def test_stateSurvivesReload_doneHiddenUnderOpen_search(ctx):
    hub = open_hub(ctx)
    add_note(hub, "Plain item", "findme")
    typo = item(hub, "Typo tag item")
    typo.locator("button.text").click()
    typo.locator("button.done").click()
    expect(item(hub, "Typo tag item")).to_have_count(0)
    hub.reload()
    expect(hub.locator(".item")).to_have_count(3)
    hub.locator("input.search").fill("findme")
    expect(hub.locator(".item")).to_have_count(1)
    hub.locator("input.search").fill("")
    hub.locator("input[value=done]").check()
    expect(hub.locator(".block", has_text="Beta block").locator(".progress")).to_have_text("1 / 2 ✓")


def test_clipboardRefused_showsTextareaWithBlock(ctx):
    hub = open_hub(ctx, init_script="Object.defineProperty(navigator,'clipboard',{value:{writeText:()=>Promise.reject(new Error('no'))}})")
    add_note(hub, "Plain item", "x")
    hub.locator("button.copy-all").click()
    expect(hub.locator("textarea.export-box")).to_have_value(
        re.compile(r"^Testhub feedback — fake .* — \d{4}-\d\d-\d\d\n- \[Beta block · \"Plain item without tag\"\] x$"))
    expect(hub.locator("button.copy-all")).to_have_text("Copy all 0")
