"""Headless tests for scripts/buildtime_snippet.html: the version badge tooltip says when the page was last deployed."""
from pathlib import Path

import pytest
from playwright.sync_api import sync_playwright

SNIPPET = (Path(__file__).parent.parent / "scripts" / "buildtime_snippet.html").read_text()
URL = "http://game.test/index.html"
BUILT = "Sun, 11 Oct 2026 06:59:45 GMT"
NOW = "2026-10-11T08:34:45Z"   # 1 h 35 min after BUILT

BADGE_WITH_LINK = '<nav id="game-nav"><span id="version-badge" title="Version"><a title="Changelog">v0.3.1</a></span></nav>'
BADGE_IS_LINK = '<nav id="game-nav"><a id="version-badge" title="Changelog">v0.3.1</a></nav>'
NO_BADGE = '<nav id="game-nav"><a id="more" href="#">More Games…</a></nav>'


@pytest.fixture(scope="module")
def browser():
    with sync_playwright() as p:
        b = p.chromium.launch()
        yield b
        b.close()


def open_page(browser, body, locale="en-GB", tz="Europe/Zurich", init_script=None):
    ctx = browser.new_context(locale=locale, timezone_id=tz)
    page = ctx.new_page()
    errors = []
    page.on("pageerror", lambda e: errors.append(str(e)))
    page.clock.set_fixed_time(NOW)
    if init_script:
        page.add_init_script(init_script)
    html = f"<!doctype html><html><head><meta charset='utf-8'></head><body>{body}{SNIPPET}</body></html>"
    # document.lastModified comes from the response header, so the page has to be navigated to, not set_content().
    page.route(URL, lambda route: route.fulfill(status=200, content_type="text/html; charset=utf-8", body=html,
                                                headers={"last-modified": BUILT}))
    page.goto(URL)
    return page, errors


def title(page, selector):
    return page.get_attribute(selector, "title").replace(" ", " ")


@pytest.mark.parametrize("locale,tz,expected", [
    ("de-CH", "Europe/Zurich", "Build: 11.10.2026, 08:59 (vor 1 Stunde 35 Minuten) · Changelog"),
    ("en-US", "America/New_York", "Build: Oct 11, 2026, 2:59 AM (1 hour 35 minutes ago) · Changelog"),
])
def test_hover_sets_build_time_in_the_visitors_zone_and_language(browser, locale, tz, expected):
    page, errors = open_page(browser, BADGE_WITH_LINK, locale, tz)
    page.hover("#version-badge a")
    assert title(page, "#version-badge") == expected
    assert title(page, "#version-badge a") == expected
    assert errors == []


def test_titles_are_untouched_until_hovered(browser):
    page, errors = open_page(browser, BADGE_WITH_LINK)
    assert title(page, "#version-badge") == "Version"
    assert title(page, "#version-badge a") == "Changelog"
    assert errors == []


def test_badge_that_is_itself_the_link(browser):
    page, errors = open_page(browser, BADGE_IS_LINK)
    page.hover("#version-badge")
    assert title(page, "#version-badge") == "Build: 11 Oct 2026, 08:59 (1 hour 35 minutes ago) · Changelog"
    assert errors == []


def test_game_language_wins_over_the_browser_language(browser):
    page, errors = open_page(browser, BADGE_WITH_LINK, locale="en-US", init_script="window.GG_LANG = 'de';")
    page.hover("#version-badge a")
    assert title(page, "#version-badge a") == "Build: 11.10.2026, 08:59 (vor 1 Stunde 35 Minuten) · Changelog"
    assert errors == []


def test_recreated_badge_keeps_the_tooltip(browser):
    page, errors = open_page(browser, BADGE_WITH_LINK)
    page.evaluate("document.getElementById('game-nav').innerHTML = "
                  "'<span id=\"version-badge\"><a>v0.3.1</a></span>'")
    page.hover("#version-badge a")
    assert title(page, "#version-badge a").startswith("Build: ")
    assert errors == []


@pytest.mark.parametrize("now,age", [
    ("2026-10-11T06:59:50Z", "just now"),
    ("2026-10-11T07:00:45Z", "1 minute ago"),
    ("2026-10-11T08:59:45Z", "2 hours ago"),
    ("2026-10-12T08:59:45Z", "1 day 2 hours ago"),
    ("2026-10-13T07:20:45Z", "2 days ago"),
    ("2026-10-11T06:00:00Z", "just now"),   # visitor's clock behind the server's
])
def test_age_is_recomputed_on_every_hover(browser, now, age):
    page, errors = open_page(browser, BADGE_WITH_LINK)
    page.clock.set_fixed_time(now)
    page.dispatch_event("#version-badge a", "mouseover")
    assert title(page, "#version-badge a").split("(")[1].split(")")[0] == age
    assert errors == []


def test_page_without_badge_is_left_alone(browser):
    page, errors = open_page(browser, NO_BADGE)
    page.hover("#more")
    assert page.get_attribute("#more", "title") is None
    assert errors == []
