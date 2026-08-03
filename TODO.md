# TODO

## Session follow-ups (2026-08-03)

- [ ] `game-iron-valhalla` was freshly onboarded onto agent-workflow this
      session (secrets, labels, consumer stub with `pre-preview: true`) but
      never smoke-tested — per `agent-workflow`'s `CONSUMER-SETUP.md` §3,
      label a trivial issue `ai-implement` there to confirm the pipeline
      actually works before trusting it with real work.
- [ ] `game-gorillazz` has no root `index.html` (build-based repo), so it was
      correctly excluded from PR #18's favicon rollout and still has no
      favicon. Needs its own approach if it should get one — worth an issue.

## Games Hub

- [ ] Check all games if MP P2P Co-op mode would make sense
- [ ] Onboard game-maze-muncher, game-moki-racer, game-neon-pong, game-nibbles,
      and game-zen-sudoku to the browser-game versioning convention (version.js,
      CHANGELOG.md, cliff.toml, git tag) — they don't have it yet
