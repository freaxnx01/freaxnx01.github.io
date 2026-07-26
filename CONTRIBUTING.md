# Contributing

This repo is a personal [GitHub Pages](https://pages.github.com/) site, built
with [Jekyll](https://jekyllrb.com/) using `jekyll-theme-hacker`, served from
the `master` branch at a custom domain configured via `CNAME`.

## Local preview

There is no build step or dependency manifest committed to this repo. To
preview changes locally, use Jekyll directly as documented at
[jekyllrb.com/docs](https://jekyllrb.com/docs/), pointing it at this
directory. There is no test suite.

## Layout

- `index.md` — the site's landing page (there is no `README.md` by design).
- `games/` — the Browser Games Hub, a static page (`index.html`, `style.css`,
  `lightbox.js`, `filter.js`, and `assets/`) linking out to individual
  `game-<name>` repos.
- `docs/superpowers/specs/` — design specs for features on this site.
- `docs/superpowers/plans/` — implementation plans for features on this site.

## Making changes

Keep changes minimal and consistent with the existing style of the file
you're editing. This is a small, low-traffic personal site, so favor simple,
additive changes over restructuring.
