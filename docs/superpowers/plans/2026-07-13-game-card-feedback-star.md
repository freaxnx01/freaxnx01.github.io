# Game card feedback & star Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Produce a copy-paste-ready `#game-nav` snippet (adding Feedback link + GitHub star widget to the existing "More Games… · Source" bar) and a rollout checklist for propagating it to each `game-<name>` repo, without touching any of those repos in this session.

**Architecture:** Two static deliverables live in this hub repo (`freaxnx01.github.io`) only: (1) an HTML template file containing the finalized 4-item nav bar markup with a `{{REPO}}` placeholder for the per-repo substitution, and (2) a Markdown rollout checklist enumerating every known `game-<name>` repo with the exact find/replace + verification steps to apply later. No other repo is cloned, edited, or pushed to in this session.

**Tech Stack:** Static HTML/CSS (inline styles, no build step), GitHub's `buttons.github.io` star-button embed, Markdown for the checklist. No test framework — this is markup with no runtime logic, so verification is structural (HTML parses/balances, placeholder present, links well-formed) plus a manual browser check, per the spec's own "Testing" section.

## Global Constraints

- The feature lives entirely in each `game-<name>` repo, not this hub repo — this session produces the snippet + rollout notes only; no other repo is touched. (spec: Scope)
- Final nav bar order: `More Games…` · `Source` · `Feedback` · `[★ Star N]`. (spec: Final nav bar order)
- Feedback link text/style matches existing links exactly: `color:#8fd8e8; text-decoration:none`, opens in a new tab (`target="_blank" rel="noopener"`). (spec: Feedback link)
- Feedback URL format: `https://github.com/freaxnx01/game-<name>/issues/new?title=%5BFeedback%5D%20game-<name>&labels=feedback`. (spec: Feedback link)
- Star widget uses GitHub's official iframe button (`buttons.github.io/buttons.js`), small size, `data-show-count="true"`, pointed at `freaxnx01/game-<name>`, no SRI hash pinned, `crossorigin="anonymous"` kept. (spec: Star widget)
- Visual seam between the iframe's light chrome and the dark pill is accepted as-is — no custom star widget. (spec: Star widget)
- Separator style matches existing `·` spans (`color:#5a6072; aria-hidden="true"`). (spec: Final nav bar order)
- Known repo list for rollout: game-barrel-shooter, game-battleship-toys, game-stack-duel, game-tank-toys, game-plod, game-moon-lander, game-dustline, game-bmx-beach-jam, game-beach-buggy-racer, game-space-invaders (from spec's Rollout section) plus any additional existing hub repos discovered in `games/index.html` at rollout time — `game-splashdown` and `game-tschau-sepp` also currently ship the 2-item nav per `docs/superpowers/specs/2026-07-07-publish-game-batch-design.md` and need the same upgrade. (spec: Rollout)

---

### Task 1: Finalized snippet template file

**Files:**
- Create: `docs/superpowers/specs/2026-07-13-game-card-feedback-star-snippet.html`
- Test: none (static file) — verified via a one-off Python structural check, not a persisted test file

**Interfaces:**
- Produces: the canonical `#game-nav` markup block, with the literal placeholder token `{{REPO}}` used everywhere a repo name is needed (feedback URL path, feedback URL title/query params, star widget `href`, star widget `aria-label`). Task 2's rollout checklist consumes this file by referencing its path and describing the `{{REPO}}` → `game-<name>` substitution.

- [ ] **Step 1: Write the template file**

Create `docs/superpowers/specs/2026-07-13-game-card-feedback-star-snippet.html` with exactly this content:

```html
<!-- game-nav: copy-paste template. Replace every {{REPO}} with the target
     repo name (e.g. game-stack-duel) before pasting into a game's index.html,
     just before </body>. See docs/superpowers/specs/2026-07-13-game-card-feedback-star-design.md
     for design rationale. -->
<nav id="game-nav" aria-label="Game navigation" style="position:fixed;right:10px;bottom:8px;z-index:2147483647;display:flex;gap:12px;align-items:center;font:600 13px/1.4 system-ui,-apple-system,sans-serif;padding:6px 11px;border-radius:8px;background:rgba(15,17,26,.55);backdrop-filter:blur(4px);-webkit-backdrop-filter:blur(4px);opacity:.55;transition:opacity .2s" onmouseover="this.style.opacity=1" onmouseout="this.style.opacity=.55">
  <a href="https://github.freaxnx01.ch/games/" style="color:#8fd8e8;text-decoration:none">More Games…</a>
  <span style="color:#5a6072" aria-hidden="true">·</span>
  <a href="https://github.com/freaxnx01/{{REPO}}" target="_blank" rel="noopener" style="color:#8fd8e8;text-decoration:none">Source</a>
  <span style="color:#5a6072" aria-hidden="true">·</span>
  <a href="https://github.com/freaxnx01/{{REPO}}/issues/new?title=%5BFeedback%5D%20{{REPO}}&labels=feedback" target="_blank" rel="noopener" style="color:#8fd8e8;text-decoration:none">Feedback</a>
  <span style="color:#5a6072" aria-hidden="true">·</span>
  <a class="github-button" href="https://github.com/freaxnx01/{{REPO}}" data-icon="octicon-star" data-size="small" data-show-count="true" aria-label="Star freaxnx01/{{REPO}} on GitHub">Star</a>
</nav>
<script async defer crossorigin="anonymous" src="https://buttons.github.io/buttons.js"></script>
```

- [ ] **Step 2: Structural verification — placeholder count and tag balance**

Run:

```bash
python3 - <<'EOF'
from html.parser import HTMLParser

path = "docs/superpowers/specs/2026-07-13-game-card-feedback-star-snippet.html"
with open(path) as f:
    content = f.read()

assert content.count("{{REPO}}") == 5, f"expected 5 {{{{REPO}}}} placeholders, found {content.count('{{REPO}}')}"
assert content.count('href="https://github.freaxnx01.ch/games/"') == 1
assert content.count("data-show-count=\"true\"") == 1
assert "integrity=" not in content, "no SRI hash should be pinned on buttons.js"
assert content.count("target=\"_blank\"") == 2, "Source and Feedback links must both open in a new tab"

class Balanced(HTMLParser):
    def __init__(self):
        super().__init__()
        self.stack = []
    def handle_starttag(self, tag, attrs):
        if tag not in ("br", "img", "input", "meta", "link"):
            self.stack.append(tag)
    def handle_endtag(self, tag):
        assert self.stack and self.stack[-1] == tag, f"mismatched closing tag: {tag}"
        self.stack.pop()

p = Balanced()
p.feed(content)
assert not p.stack, f"unclosed tags: {p.stack}"
print("OK: snippet structurally valid")
EOF
```

Expected output: `OK: snippet structurally valid`

- [ ] **Step 3: Manual browser sanity check**

Run: `python3 -m http.server 8000 --directory docs/superpowers/specs` and open
`http://localhost:8000/2026-07-13-game-card-feedback-star-snippet.html` in a
browser. Confirm:
- The nav bar renders bottom-right as a translucent dark pill.
- Hovering raises opacity to fully opaque.
- The literal text `{{REPO}}` is visible in the Feedback/Star link targets when
  hovering over them (expected — this is the raw template, not a substituted
  instance). Stop the server (Ctrl+C) once confirmed.

- [ ] **Step 4: Commit**

```bash
git add docs/superpowers/specs/2026-07-13-game-card-feedback-star-snippet.html
git commit -m "Add game-nav feedback+star snippet template"
```

---

### Task 2: Rollout checklist

**Files:**
- Create: `docs/superpowers/specs/2026-07-13-game-card-feedback-star-rollout.md`
- Test: none (static doc) — verified via a Markdown structural check

**Interfaces:**
- Consumes: `docs/superpowers/specs/2026-07-13-game-card-feedback-star-snippet.html` from Task 1 (referenced by path; describes substituting `{{REPO}}` with each repo's name).
- Produces: a standalone checklist doc that a future session can execute against each `game-<name>` repo without re-deriving the design.

- [ ] **Step 1: Write the rollout checklist**

Create `docs/superpowers/specs/2026-07-13-game-card-feedback-star-rollout.md` with exactly this content:

```markdown
# Game-nav feedback + star — rollout checklist

**Source design:** `docs/superpowers/specs/2026-07-13-game-card-feedback-star-design.md`
**Source snippet:** `docs/superpowers/specs/2026-07-13-game-card-feedback-star-snippet.html`

This session (2026-07-13) produced the design + snippet only. Applying the
snippet to each existing `game-<name>` repo is separate follow-up work, not
yet done. Use this checklist when that follow-up happens.

## Per-repo steps

For each repo `game-<name>` below:

1. Clone the repo locally (or open it in an existing worktree).
2. Open `index.html` and find the existing `<!-- game-nav -->` block (a
   `<nav id="game-nav">` with 2 links: "More Games…" and "Source").
3. Replace that whole block (through its closing `</nav>`, and any trailing
   `<script>` tag for `buttons.js` if one already exists from a prior partial
   rollout) with the contents of
   `docs/superpowers/specs/2026-07-13-game-card-feedback-star-snippet.html`,
   substituting every `{{REPO}}` with this repo's exact name (e.g. `game-stack-duel`).
4. Save, then open `index.html` locally in a browser (or via a local static
   server) and confirm:
   - All four items render: `More Games…` · `Source` · `Feedback` · `★ Star N`.
   - `Feedback` opens `https://github.com/freaxnx01/<repo>/issues/new?title=%5BFeedback%5D%20<repo>&labels=feedback`
     in a new tab, with that title pre-filled in GitHub's new-issue form.
   - The star button shows a live star count and, when logged into GitHub,
     starring the repo on click.
5. Commit with message `Add Feedback link and star widget to game-nav` and push.
6. (Optional, nice-to-have per design) Create a `feedback` label in the repo
   via GitHub's Labels UI, so the pre-applied `labels=feedback` query param
   actually attaches a label instead of being silently ignored.
7. Check this repo off below.

## Repos

- [ ] game-barrel-shooter
- [ ] game-battleship-toys
- [ ] game-stack-duel
- [ ] game-tank-toys
- [ ] game-plod
- [ ] game-moon-lander
- [ ] game-dustline
- [ ] game-bmx-beach-jam
- [ ] game-beach-buggy-racer
- [ ] game-space-invaders
- [ ] game-splashdown
- [ ] game-tschau-sepp

Before starting, cross-check this list against the current `games/index.html`
in this hub repo — new games may have been added to the hub since this
checklist was written, and those repos need the same rollout.

## New games going forward

Any new `game-<name>` repo created after this rollout should ship the full
4-item nav bar from the start (paste the Task 1 snippet directly, substituting
`{{REPO}}`), not the old 2-item version.
```

- [ ] **Step 2: Structural verification**

Run:

```bash
python3 - <<'EOF'
path = "docs/superpowers/specs/2026-07-13-game-card-feedback-star-rollout.md"
with open(path) as f:
    content = f.read()

expected_repos = [
    "game-barrel-shooter", "game-battleship-toys", "game-stack-duel",
    "game-tank-toys", "game-plod", "game-moon-lander", "game-dustline",
    "game-bmx-beach-jam", "game-beach-buggy-racer", "game-space-invaders",
    "game-splashdown", "game-tschau-sepp",
]
for repo in expected_repos:
    assert f"- [ ] {repo}" in content, f"missing checklist line for {repo}"

assert content.count("- [ ]") == len(expected_repos), "unexpected extra/missing checkbox lines"
assert "docs/superpowers/specs/2026-07-13-game-card-feedback-star-snippet.html" in content
print("OK: rollout checklist complete and well-formed")
EOF
```

Expected output: `OK: rollout checklist complete and well-formed`

- [ ] **Step 3: Commit**

```bash
git add docs/superpowers/specs/2026-07-13-game-card-feedback-star-rollout.md
git commit -m "Add game-nav feedback+star rollout checklist"
```
