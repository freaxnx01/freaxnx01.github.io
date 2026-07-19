---
name: feedback-worktree-tool-scope
description: "EnterWorktree only creates worktrees in the current session's primary repo, not sibling nested repos"
metadata: 
  node_type: memory
  type: feedback
  originSessionId: 30ca226d-80cd-4490-98f6-7db7d0df9d2e
---

The `EnterWorktree` native tool creates worktrees under `.claude/worktrees/` of the
session's *primary* repo (the one the session's cwd is inside). It cannot target a
different, separately-cloned git repo that merely lives as a sibling/nested directory
on disk (e.g. `public/game-acronym-quiz` next to `public/freaxnx01.github.io`) — that
repo is not "nested inside" the primary repo's git tree even though it's nested in the
filesystem path.

**Why:** Discovered when running subagent-driven-development against a plan scoped to
`game-acronym-quiz`. Calling `EnterWorktree({name: ...})` while the session cwd was the
hub repo (`freaxnx01.github.io`) silently created the worktree in the *hub* repo instead
of the target game repo. Had to `ExitWorktree({action: "remove"})` and fall back to a
manual `git worktree add` inside the actual target repo.

**How to apply:** When the plan/task targets a different git repo than the session's
primary one (common in this multi-repo workspace under `public/`), skip `EnterWorktree`
and use the manual git-worktree fallback (`git worktree add <target-repo>/.worktrees/<branch> -b <branch>`)
directly in that repo. Verify with `git rev-parse --git-dir` / `--git-common-dir` inside
the created worktree before dispatching any implementer.

See also [[project-game-repo-publishing]].
