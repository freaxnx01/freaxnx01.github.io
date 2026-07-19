---
name: feedback-subagent-branch-verification
description: "Always verify an implementer subagent's commit landed on the intended worktree branch, not main"
metadata: 
  node_type: memory
  type: feedback
  originSessionId: 30ca226d-80cd-4490-98f6-7db7d0df9d2e
---

After dispatching an implementer subagent with `Work from: <worktree-path>`, do not
assume its commit landed on the worktree's branch — verify with
`git for-each-ref refs/heads` (or `git log --oneline --all` plus `git branch --contains <sha>`)
before generating the review package.

**Why:** In a subagent-driven-development run against `game-acronym-quiz`, an
implementer subagent was told to work from
`.worktrees/issue-1-suggest-acronym`, but its commit landed directly on `main`
instead (likely ran `git commit` from the repo root rather than the worktree
subdirectory). This wasn't caught until `review-package` reported "0 commits" between
BASE and HEAD in the worktree. Had to `git branch -f <branch> <sha>` and
`git reset --hard <base>` on `main` to move the commit onto the correct branch without
losing it — full working-tree/history surgery that a branch check up front would have
prevented entirely.

**How to apply:** After every implementer subagent reports DONE, before running
`review-package`: check `git branch --show-current` inside the worktree matches the
expected branch, and confirm the reported commit SHA is reachable from that branch
(not from `main`/`master`). Also worth telling implementer subagents explicitly in the
dispatch prompt to confirm their branch with `git branch --show-current` right before
committing — this caught the same class of mistake on a follow-up fix dispatch in the
same session.

See also [[feedback-worktree-tool-scope]].
