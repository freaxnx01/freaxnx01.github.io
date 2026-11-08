"""Where the hub lives. Flip SITE at the domain switch (short-domains plan, Task 4)."""
import re

SITE = "https://freax.games"
# Both hostnames are accepted when reading play links, so scripts work before and after the switch.
SITE_HOSTS = ("github.freaxnx01.ch", "freax.games")
PLAY_RE = re.compile(
    r'href="https://(?:' + "|".join(re.escape(h) for h in SITE_HOSTS) + r')/(game-[^/"]+)/"'
)


def game_url(repo: str) -> str:
    return f"{SITE}/{repo}/"
