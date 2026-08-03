# Individual favicons for each game

Related: [issue #13](https://github.com/freaxnx01/freaxnx01.github.io/issues/13)

## Problem

Each game lives in its own `game-<name>` GitHub Pages repo (root-only,
single `index.html`, no build step), served at
`https://github.freaxnx01.ch/<repo>/`. None of the 36 `game-<name>` repos
currently set a `<link rel="icon">` — visiting any game's own page shows the
browser's default/generic tab icon. The hub page itself
(`freaxnx01.github.io/games/index.html`) already has its own
`favicon.svg` / `favicon-32.png` and is out of scope here.

The hub repo already has a per-game card thumbnail at
`games/assets/game-<name>-icon.png` (400×250 PNG) for every game listed in
`games/index.html`.

## Scope

All 36 `game-<name>` repos currently linked from `games/index.html`.

Deriving the asset list: parse `games/index.html` for
`https://github.freaxnx01.ch/<repo>/` play links, matched against the
corresponding `games/assets/<slug>-icon.png` (the `data-full` /
`data-title` img already on each card).

Out of scope: the hub page's own favicon, and any game not currently listed
in the hub (e.g. games in private backlog repos that haven't graduated yet).

## Asset generation

A Python script (Pillow, already available) derives each game's favicon from
its existing card icon — no new art:

1. Load `games/assets/<slug>-icon.png` (400×250).
2. Center-crop horizontally to a 250×250 square (crop `x = (400-250)/2 = 75`
   to `325`, full height).
3. Resize to 32×32 (`Image.LANCZOS`).
4. Save as `favicon.png` (PNG, no alpha requirements beyond what the source
   has).

Single size, matching the hub's own `favicon-32.png` convention — no
16×16 or apple-touch-icon variants.

## Per-repo change

Two things land in each `game-<name>` repo:

- `favicon.png` at repo root (32×32 PNG generated above).
- `<link rel="icon" href="favicon.png" sizes="32x32" type="image/png">`
  inserted immediately after the `<head>` opening tag.

Insertion point is deliberately `<head>\n` → `<head>\n<link ...>\n` via a
simple string/regex replace, not a full HTML parse — head contents vary
significantly across these 36 repos (some minimal, some bundler-generated
with a `<title>Bundled Page</title>` placeholder), and "right after `<head>`"
is the one insertion point that's valid regardless of what else is in there.

These repos have no build step — `index.html` in the repo root *is* the
deployed page — so editing it directly and pushing is the complete, permanent
change; nothing will overwrite it on a subsequent deploy.

## Rollout mechanism

One script, run from the hub repo (`freaxnx01.github.io`), drives all 36
repos. Location: `scripts/add_game_favicons.py`, alongside the existing
`scripts/capture_screenshots.py` convention.

For each game:

1. **Get a local clone.** If `~/repos/github/freaxnx01/public/game-<name>`
   already exists, `git pull` on `main`. Otherwise `git clone` it there
   (matches where the other game repos already live on this machine).
2. **Generate `favicon.png`** per the steps above, into the repo root.
3. **Idempotency check.** If `favicon.png` already exists in the repo with
   identical bytes to the freshly generated one, *and* the `<link
   rel="icon">` tag is already present in `index.html`, skip this repo
   entirely (no commit). Makes the script safe to re-run later for newly
   published games without re-touching the other 35.
4. **Insert the link tag** into `index.html` if not already present.
5. **Commit** (`feat: add favicon`) and **push directly to `main`.**
6. Any failure at any step (clone fails, push rejected, etc.) is caught,
   logged, and the script moves on to the next repo — one bad repo must not
   abort the batch.

At the end, print a per-repo summary table: `succeeded` / `skipped
(already done)` / `failed` with the reason for failures.

## Testing

No automated tests (one-shot content-generation script over static repos).
Verification is manual after the run:

- The summary table shows 36/36 accounted for (succeeded + skipped, ideally
  0 failed).
- Spot-check 2-3 games by loading `https://github.freaxnx01.ch/<repo>/` in a
  browser and confirming the tab icon is the game's own crop, not the
  default.
- `git log -1 --stat` on a couple of the local game clones to confirm the
  commit + `favicon.png` landed as expected.

## Out of scope / explicitly not doing

- No new hand-drawn favicon art — pure derivation from existing card icons.
- No 16×16 or apple-touch-icon variants.
- No change to the hub page's own favicon.
- No PR workflow — direct push to `main` per repo (all are personal,
  low-traffic static game repos with no CI gate on `main`).
