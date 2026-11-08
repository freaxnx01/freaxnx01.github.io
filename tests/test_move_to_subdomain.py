"""Tests for scripts/move_to_subdomain.py (no network: fake clients)."""
from pathlib import Path
import sys

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

import move_to_subdomain as m  # noqa: E402


class FakeCF:
    def __init__(self, records=None):
        self.records = dict(records or {})
        self.created = []

    def find(self, host):
        return self.records.get(host)

    def create_cname(self, host, target):
        self.created.append(host)
        self.records[host] = {"type": "CNAME", "content": target, "proxied": False}


class FakeGH:
    def __init__(self, cname=None, cert="approved"):
        self.cname, self.cert, self.enforced, self.calls = cname, cert, False, []

    def pages(self, repo):
        return {"cname": self.cname, "https_enforced": self.enforced,
                "https_certificate": {"state": self.cert}}

    def set_cname(self, repo, cname):
        self.calls.append(("cname", cname))
        self.cname = cname

    def enforce_https(self, repo, cname):
        self.calls.append(("https", cname))
        self.enforced = True


def test_dns_is_created_before_the_pages_domain():
    cf, gh = FakeCF(), FakeGH()
    assert m.move("game-wipfelkratzer", cf, gh) == "moved"
    assert cf.created == ["wipfelkratzer.freax.games"]
    assert gh.calls == [("cname", "wipfelkratzer.freax.games")]


def test_second_run_changes_nothing():
    cf = FakeCF({"nibbles.freax.games": {"type": "CNAME", "content": "freaxnx01.github.io", "proxied": False}})
    gh = FakeGH(cname="nibbles.freax.games")
    assert m.move("game-nibbles", cf, gh) == "already moved"
    assert cf.created == [] and gh.calls == []


@pytest.mark.parametrize("rec", [
    {"type": "CNAME", "content": "elsewhere.example", "proxied": False},
    {"type": "CNAME", "content": "freaxnx01.github.io", "proxied": True},
    {"type": "A", "content": "1.2.3.4", "proxied": False},
])
def test_foreign_dns_record_stops_the_move(rec):
    cf, gh = FakeCF({"nibbles.freax.games": rec}), FakeGH()
    with pytest.raises(m.MoveError, match="nibbles.freax.games"):
        m.move("game-nibbles", cf, gh)
    assert gh.calls == []


def test_https_is_enforced_only_with_an_approved_certificate():
    gh = FakeGH(cname="nibbles.freax.games", cert="approved")
    assert m.finish("game-nibbles", gh, deadline=0) == "https on"
    gh2 = FakeGH(cname="nibbles.freax.games", cert="authorization_pending")
    assert m.finish("game-nibbles", gh2, deadline=0) == "certificate not ready"
    assert gh2.calls == []


def test_hub_repos_lists_movable_games_only():
    page = "".join(f'<article class="card"><a class="card__play" href="{h}">Play</a></article>'
                   for h in ("https://freax.games/game-nibbles/", "https://zen-sudoku.freax.games/",
                             "https://rhyflitzer.ch/", "https://julia-hase.github.io/dogwash/"))
    assert m.hub_repos(page) == ["game-nibbles", "game-zen-sudoku"]
