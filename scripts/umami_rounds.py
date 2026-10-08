#!/usr/bin/env python3
"""One row per played round, from the self-hosted Umami (stats.freaxnx01.ch).

Umami's dashboard tallies each event property on its own, so it can't show a
round's players and scores side by side. This lists the `round-end` events of
one game's website and prints each with all its properties on one line,
grouped by session (one block = one browser session).

Login: UMAMI_USER / UMAMI_PASSWORD from the environment, else the Passbolt
entry "Umami admin stats.freaxnx01.ch" via the `passbolt` CLI. Nothing secret
lives in this repo.

Usage:
    python3 scripts/umami_rounds.py                       # Tschau Sepp, last 7 days
    python3 scripts/umami_rounds.py --since 30d --online  # only online rounds
    python3 scripts/umami_rounds.py --game "Tschau Sepp" --csv > rounds.csv
"""
import argparse
import csv
import io
import json
import os
import re
import subprocess
import sys
import time
import urllib.parse
import urllib.request
from datetime import datetime
from zoneinfo import ZoneInfo

BASE = "https://stats.freaxnx01.ch"
PASSBOLT_NAME = "Umami admin stats.freaxnx01.ch"
MAX_SEATS = 4


# ---------- pure part (tested) ----------

def props_from_event_data(items):
    """Turn /event-data/<eventId> entries into {key: value}; numbers become ints."""
    props = {}
    for it in items:
        if it.get("dataType") == 2 and it.get("numberValue") is not None:
            n = float(it["numberValue"])
            props[it["dataKey"]] = int(n) if n.is_integer() else n
        else:
            props[it["dataKey"]] = it.get("stringValue")
    return props


def round_row(event, props, tz):
    when = datetime.fromisoformat(event["createdAt"].replace("Z", "+00:00")).astimezone(ZoneInfo(tz))
    players = []
    for i in range(1, MAX_SEATS + 1):
        if f"p{i}Name" in props:
            players.append((props[f"p{i}Name"], props.get(f"p{i}Score")))
    return {
        "time": when.strftime("%Y-%m-%d %H:%M"),
        "session": event.get("sessionId"),
        "mode": props.get("mode"),
        "round": props.get("round"),
        "players": players,
        "result": props.get("result"),
        "durationSec": props.get("durationSec"),
    }


def format_row(row):
    who = " · ".join(f"{n} {s}" for n, s in row["players"]) or "—"
    return f"{row['time']}  {row['mode']}  R{row['round']}  {who}  {row['result']}  {row['durationSec']}s"


def to_csv(rows):
    out = io.StringIO()
    w = csv.writer(out, lineterminator="\n")
    head = ["time", "session", "mode", "round", "result", "durationSec"]
    for i in range(1, MAX_SEATS + 1):
        head += [f"p{i}Name", f"p{i}Score"]
    w.writerow(head)
    for r in rows:
        line = [r["time"], r["session"], r["mode"], r["round"], r["result"], r["durationSec"]]
        for i in range(MAX_SEATS):
            line += list(r["players"][i]) if i < len(r["players"]) else ["", ""]
        w.writerow(line)
    return out.getvalue()


# ---------- Umami API ----------

def credentials():
    user, pw = os.environ.get("UMAMI_USER"), os.environ.get("UMAMI_PASSWORD")
    if user and pw:
        return user, pw
    listing = subprocess.run(["passbolt", "list", "resource", "--json"], capture_output=True, text=True, timeout=60, check=True)
    match = next((r for r in json.loads(listing.stdout) if r.get("name") == PASSBOLT_NAME), None)
    if not match:
        sys.exit(f"Passbolt entry '{PASSBOLT_NAME}' not found; set UMAMI_USER / UMAMI_PASSWORD instead.")
    res = subprocess.run(["passbolt", "get", "resource", "--id", match["id"], "--json"], capture_output=True, text=True, timeout=60, check=True)
    data = json.loads(res.stdout)
    return data.get("username") or "admin", data["password"]


def api(path, token=None, body=None):
    req = urllib.request.Request(BASE + path, data=json.dumps(body).encode() if body is not None else None)
    req.add_header("Content-Type", "application/json")
    if token:
        req.add_header("Authorization", f"Bearer {token}")
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.load(r)


def parse_since(s):
    m = re.fullmatch(r"(\d+)([hd])", s)
    if not m:
        raise argparse.ArgumentTypeError("use e.g. 24h or 7d")
    return int(m.group(1)) * (3600 if m.group(2) == "h" else 86400)


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--game", default="Tschau Sepp", help="Umami website name (default: Tschau Sepp)")
    ap.add_argument("--since", type=parse_since, default=parse_since("7d"), help="time range, e.g. 24h, 7d (default 7d)")
    ap.add_argument("--online", action="store_true", help="only online rounds (with player data)")
    ap.add_argument("--csv", action="store_true", help="CSV instead of text")
    ap.add_argument("--tz", default="Europe/Zurich")
    args = ap.parse_args()

    user, pw = credentials()
    token = api("/api/auth/login", body={"username": user, "password": pw})["token"]

    sites = api("/api/websites?pageSize=200", token)
    sites = sites.get("data", sites) if isinstance(sites, dict) else sites
    site = next((s for s in sites if s["name"].lower() == args.game.lower()), None)
    if not site:
        sys.exit(f"No Umami website named '{args.game}'. Known: {', '.join(s['name'] for s in sites)}")

    end = int(time.time() * 1000)
    q = {"startAt": end - args.since * 1000, "endAt": end, "pageSize": 200}
    events, page = [], 1
    while True:
        res = api(f"/api/websites/{site['id']}/events?" + urllib.parse.urlencode({**q, "page": page}), token)
        batch = res.get("data", [])
        events += [e for e in batch if e.get("eventName") == "round-end"]
        if len(batch) < q["pageSize"]:
            break
        page += 1

    rows = []
    for e in sorted(events, key=lambda e: e["createdAt"]):
        props = props_from_event_data(api(f"/api/websites/{site['id']}/event-data/{e['id']}", token))
        row = round_row(e, props, args.tz)
        if args.online and not row["players"]:
            continue
        rows.append(row)

    if args.csv:
        sys.stdout.write(to_csv(rows))
        return
    if not rows:
        print("No rounds in this range.")
        return
    last = None
    for r in rows:
        if r["session"] != last:
            if last is not None:
                print()
            last = r["session"]
        print(format_row(r))
    print(f"\n{len(rows)} round(s), {len({r['session'] for r in rows})} session(s)")


if __name__ == "__main__":
    main()
