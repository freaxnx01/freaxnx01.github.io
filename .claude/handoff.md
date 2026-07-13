The "Game card feedback & star" design/build phase is fully complete and pushed
(commits e6075e0..174562f on master): design spec, snippet template, rollout
checklist, and the plan itself are all committed. Nothing is in-flight.

The next phase — not yet started — is the rollout: applying the snippet
template to each of the 12 known `game-<name>` repos. Its artifact is:
`docs/superpowers/specs/2026-07-13-game-card-feedback-star-rollout.md`
(self-contained: lists all 12 repos as unchecked boxes, with exact per-repo
steps referencing the snippet at
`docs/superpowers/specs/2026-07-13-game-card-feedback-star-snippet.html`).

Next step: pick the checklist's first unchecked repo, clone it (or open its
worktree), and apply the snippet per the checklist's per-repo steps. Each repo
is independent, so use `superpowers:subagent-driven-development` to dispatch
rollout work — but note this touches OTHER repos (`game-<name>`), not this hub
repo, so each dispatched task needs its own clone/worktree setup first.
