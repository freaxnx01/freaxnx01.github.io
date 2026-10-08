"""Tests for scripts/umami_rounds.py — the pure row-building part, no network."""
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

from umami_rounds import props_from_event_data, round_row, format_row, to_csv


def item(key, value, data_type=1):
    """One entry as /api/websites/<id>/event-data/<eventId> returns it."""
    if data_type == 2:
        return {"dataKey": key, "stringValue": f"{value}.0000", "numberValue": str(value), "dataType": 2}
    return {"dataKey": key, "stringValue": value, "numberValue": None, "dataType": 1}


EVENT = {
    "id": "e1",
    "sessionId": "s1",
    "createdAt": "2026-10-08T14:07:43.687Z",
    "eventName": "round-end",
}

ONLINE = [
    item("game", "tschau-sepp"),
    item("mode", "host"),
    item("round", 3, 2),
    item("result", "loss"),
    item("durationSec", 31, 2),
    item("players", 2, 2),
    item("p1Name", "Schälle-Ueli"),
    item("p1Score", 0, 2),
    item("p2Name", "Turbo-Sepp"),
    item("p2Score", 20, 2),
]


def test_props_numbers_become_ints():
    props = props_from_event_data(ONLINE)
    assert props["round"] == 3
    assert props["p2Score"] == 20
    assert props["mode"] == "host"


def test_round_row_online_collects_players_in_seat_order():
    row = round_row(EVENT, props_from_event_data(ONLINE), tz="Europe/Zurich")
    assert row["time"] == "2026-10-08 16:07"
    assert row["session"] == "s1"
    assert row["mode"] == "host"
    assert row["round"] == 3
    assert row["players"] == [("Schälle-Ueli", 0), ("Turbo-Sepp", 20)]
    assert row["result"] == "loss"
    assert row["durationSec"] == 31


def test_round_row_local_has_no_players():
    local = [item("mode", "bot"), item("round", 1, 2), item("result", "win"), item("durationSec", 40, 2)]
    row = round_row(EVENT, props_from_event_data(local), tz="Europe/Zurich")
    assert row["players"] == []


def test_format_row_one_line_per_round():
    row = round_row(EVENT, props_from_event_data(ONLINE), tz="Europe/Zurich")
    assert format_row(row) == "2026-10-08 16:07  host  R3  Schälle-Ueli 0 · Turbo-Sepp 20  loss  31s"


def test_format_row_local_round_shows_dash():
    local = [item("mode", "bot"), item("round", 1, 2), item("result", "win"), item("durationSec", 40, 2)]
    row = round_row(EVENT, props_from_event_data(local), tz="Europe/Zurich")
    assert format_row(row) == "2026-10-08 16:07  bot  R1  —  win  40s"


def test_to_csv_flattens_players():
    row = round_row(EVENT, props_from_event_data(ONLINE), tz="Europe/Zurich")
    lines = to_csv([row]).strip().splitlines()
    assert lines[0] == "time,session,mode,round,result,durationSec,p1Name,p1Score,p2Name,p2Score,p3Name,p3Score,p4Name,p4Score"
    assert lines[1] == "2026-10-08 16:07,s1,host,3,loss,31,Schälle-Ueli,0,Turbo-Sepp,20,,,,"
