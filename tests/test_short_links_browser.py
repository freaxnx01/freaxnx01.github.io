"""A generated stub forwards to the game and keeps query and hash. Serves the repo locally."""
import functools
import http.server
import threading
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).parent.parent
STUB = "<!doctype html><title>landed</title>"


def test_short_link_keeps_query_and_hash():
    handler = functools.partial(http.server.SimpleHTTPRequestHandler, directory=str(ROOT))
    httpd = http.server.ThreadingHTTPServer(("127.0.0.1", 0), handler)
    threading.Thread(target=httpd.serve_forever, daemon=True).start()
    base = f"http://127.0.0.1:{httpd.server_port}"
    try:
        with sync_playwright() as p:
            b = p.chromium.launch()
            page = b.new_page()
            page.route(f"{base}/game-wipfelkratzer/**",
                       lambda r: r.fulfill(status=200, content_type="text/html", body=STUB))
            page.goto(f"{base}/wipfelkratzer/?lang=de#x")
            page.wait_for_function("() => document.title === 'landed'", timeout=15000)
            assert page.url == f"{base}/game-wipfelkratzer/?lang=de#x"
            b.close()
    finally:
        httpd.shutdown()
