---
name: feedback-screenshot-capture-recipes
description: "When a game's hub screenshot looks wrong, verify the action recipe against actual gameplay rather than guessing from the game's control scheme"
metadata: 
  node_type: memory
  type: feedback
  originSessionId: 30ca226d-80cd-4490-98f6-7db7d0df9d2e
---

For `scripts/capture_screenshots.py` ACTIONS recipes, don't assume the "obvious"
control input produces a good screenshot — verify visually with an ad hoc Playwright
run against the live URL before editing the recipe.

**Why:** `game-dustline`'s recipe held `ArrowUp` after launch, assuming that would
advance the helicopter up the battlefield into view. In reality the game is
screen-locked (the world scrolls under a player sprite whose *screen* position is what
the arrow keys move), so holding `ArrowUp` drove the helicopter to the top of the
screen, into/under the wave-banner HUD — the opposite of the intended effect. Fixed by
testing several `wait`/nudge combinations live (via a throwaway Python+Playwright
script hitting the real deployed URL, not the recipe file blind) until the sprite
stayed centered with visible tracer fire and an enemy in frame, *then* writing that
back into the recipe.

**How to apply:** When asked to fix or add a screenshot recipe, always do a quick
live Playwright probe against the deployed game first (screenshot after each
candidate action sequence) rather than editing the recipe from reading the game's
control scheme alone. Read the game's source (search for how player position is
clamped/updated) if the visual result is surprising — it often reveals the camera
model (screen-locked vs. world-locked) that explains why an "obvious" key produces
the wrong shot.

See also [[project-game-hub-conventions]].
