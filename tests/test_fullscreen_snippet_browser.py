"""Headless tests for scripts/fullscreen_snippet.html (issue #25)."""
from pathlib import Path

import pytest
from playwright.sync_api import sync_playwright

SNIPPET = (Path(__file__).parent.parent / "scripts" / "fullscreen_snippet.html").read_text()

NAV_WITH_BADGE = """
<nav id="game-nav">
  <span id="version-badge"><a>v0.3.1</a></span>
  <span aria-hidden="true">·</span>
  <a id="more" href="#">More Games…</a>
</nav>"""

NAV_NO_BADGE = """
<nav id="game-nav">
  <a id="more" href="#">More Games…</a>
</nav>"""

FS_SUPPORTED = """
Object.defineProperty(Document.prototype, 'fullscreenEnabled', {get: () => true, configurable: true});
window.__fsCalls = 0;
Element.prototype.requestFullscreen = function () { window.__fsCalls++; return Promise.resolve(); };
"""

FS_UNSUPPORTED = """
Object.defineProperty(Document.prototype, 'fullscreenEnabled', {get: () => false, configurable: true});
Object.defineProperty(Document.prototype, 'webkitFullscreenEnabled', {get: () => false, configurable: true});
"""


def page_html(body: str) -> str:
    return f"<!doctype html><html><head><meta charset='utf-8'></head><body>{body}{SNIPPET}</body></html>"


@pytest.fixture(scope="module")
def browser():
    with sync_playwright() as p:
        b = p.chromium.launch()
        yield b
        b.close()


def open_page(browser, body, init_script):
    page = browser.new_page()
    errors = []
    page.on("pageerror", lambda e: errors.append(str(e)))
    page.add_init_script(init_script)
    # Init scripts only run on navigation, and set_content() rewrites the
    # current document without navigating — so goto() first, or the Fullscreen
    # API stubs below never apply and the tests silently see real Chromium.
    page.goto("about:blank")
    page.set_content(page_html(body))
    return page, errors


def test_button_sits_right_after_badge_separator(browser):
    page, errors = open_page(browser, NAV_WITH_BADGE, FS_SUPPORTED)
    order = page.evaluate(
        "Array.from(document.getElementById('game-nav').children).map(e => e.id || e.textContent.trim())"
    )
    assert order[:4] == ["version-badge", "·", "fs-toggle", "·"]
    btn = page.locator("#fs-toggle")
    assert btn.text_content() == "⛶"
    assert btn.get_attribute("aria-label") == "Fullscreen"
    assert btn.get_attribute("title") == "Fullscreen"
    assert btn.get_attribute("aria-pressed") == "false"
    assert btn.get_attribute("type") == "button"
    assert errors == []


def test_button_is_first_when_no_badge(browser):
    page, errors = open_page(browser, NAV_NO_BADGE, FS_SUPPORTED)
    order = page.evaluate(
        "Array.from(document.getElementById('game-nav').children).map(e => e.id || e.textContent.trim())"
    )
    assert order[:3] == ["fs-toggle", "·", "more"]
    assert errors == []


def test_hidden_when_fullscreen_unsupported(browser):
    page, errors = open_page(browser, NAV_WITH_BADGE, FS_UNSUPPORTED)
    page.wait_for_timeout(600)
    assert page.locator("#fs-toggle").count() == 0
    assert page.evaluate("document.getElementById('game-nav').children.length") == 3
    assert errors == []


def test_click_requests_fullscreen_once_and_blurs(browser):
    page, errors = open_page(browser, NAV_WITH_BADGE, FS_SUPPORTED)
    page.locator("#fs-toggle").click()
    assert page.evaluate("window.__fsCalls") == 1
    assert page.evaluate("document.activeElement && document.activeElement.id") != "fs-toggle"
    assert errors == []


def test_state_flips_on_fullscreenchange(browser):
    page, errors = open_page(browser, NAV_WITH_BADGE, FS_SUPPORTED)
    page.evaluate("""
        Object.defineProperty(Document.prototype, 'fullscreenElement',
            {get: () => document.documentElement, configurable: true});
        document.dispatchEvent(new Event('fullscreenchange'));
    """)
    btn = page.locator("#fs-toggle")
    assert btn.text_content() == "✕"
    assert btn.get_attribute("aria-label") == "Exit fullscreen"
    assert btn.get_attribute("aria-pressed") == "true"
    assert errors == []


def test_readded_after_nav_is_recreated(browser):
    page, errors = open_page(browser, NAV_WITH_BADGE, FS_SUPPORTED)
    page.evaluate("""
        document.getElementById('game-nav').remove();
        const nav = document.createElement('nav');
        nav.id = 'game-nav';
        nav.innerHTML = '<span id="version-badge">v1</span><span aria-hidden="true">·</span><a>More</a>';
        document.body.appendChild(nav);
    """)
    page.wait_for_selector("#game-nav #fs-toggle", timeout=1000)
    assert page.locator("#fs-toggle").count() == 1
    assert errors == []


def test_no_nav_no_button_no_error(browser):
    page, errors = open_page(browser, "<main>game</main>", FS_SUPPORTED)
    page.wait_for_timeout(600)
    assert page.locator("#fs-toggle").count() == 0
    assert errors == []
