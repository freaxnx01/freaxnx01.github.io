"""Where the hub and its games live (game-subdomains spec, 2026-11-08)."""
import re

SITE = "https://freax.games"
GAME_DOMAIN = "freax.games"
# Subdomains of freax.games that are not hub games.
NOT_GAMES = {"www", "rhyflitzer"}
# Play links in three forms: old host path, freax.games path, own subdomain.
_PATH_RE = re.compile(r'href="https://(?:github\.freaxnx01\.ch|freax\.games)/(game-[a-z0-9-]+)/"')
_SUB_RE = re.compile(r'href="https://([a-z0-9-]+)\.freax\.games/"')


def play_repo(block: str) -> str | None:
    """Repo name (game-<name>) of the play link in a card, or None for other links."""
    m = _PATH_RE.search(block)
    if m:
        return m.group(1)
    m = _SUB_RE.search(block)
    if m and m.group(1) not in NOT_GAMES:
        return f"game-{m.group(1)}"
    return None


def subdomain(repo: str) -> str:
    return f"{repo.removeprefix('game-')}.{GAME_DOMAIN}"


def game_url(repo: str) -> str:
    return f"https://{subdomain(repo)}/"
