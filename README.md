# Meditations by Parth

> a blog on cooking, mathematics, and whatever passes my fancy

A tiny static blog generator: Markdown files in `posts/` become HTML in `_site/`,
built by a single Python script and deployed to GitHub Pages via GitHub Actions.

## Writing a post

Add a Markdown file to `posts/`, named `YYYY-MM-DD-slug.md`, with frontmatter.
The `published` flag is required — the build errors if it's missing, so you never
accidentally publish (or hide) a post by forgetting it.

```markdown
---
title: My Great Post
date: 2026-06-01
published: true
---

Your content here, in **Markdown**.
```

Posts are listed on the home page newest-first. Supported Markdown: fenced code
blocks, tables, footnotes, and smart quotes.

## RSS feed

The build writes an RSS 2.0 feed to `_site/feed.xml`, listing every published
post newest-first with its full rendered content. Every page links to it (in the
`<head>` for reader autodiscovery and in the footer), so feed readers find it
automatically. Only published posts appear — drafts are excluded.

The feed needs absolute URLs, so set `SITE_URL` in `build.py` to the site's
base URL (no trailing slash); it defaults to `https://ptnobel.github.io/blog`.

## Drafts / unlisted posts

Add `published: false` to a post's frontmatter to keep it off the home page:

```markdown
---
title: Work in Progress
date: 2026-06-01
published: false
---
```

The post is still built and deployed at its own URL (e.g.
`https://you.github.io/repo/work-in-progress/`), so you can share that link
for feedback — it just isn't linked from the home page, and it's tagged
`noindex` so search engines skip it. Set it to `true` to publish.

## Build locally

```sh
uv run build.py      # writes the site to _site/
```

Preview it:

```sh
uv run python -m http.server -d _site 8000   # then open http://localhost:8000
```

`build.py` uses [uv](https://docs.astral.sh/uv/)'s inline script dependencies, so
there's nothing to install first — `uv run` fetches `markdown` and
`python-frontmatter` automatically.

## Deploying

Pushes to `main` trigger `.github/workflows/deploy.yml`, which builds the site and
publishes it to GitHub Pages.

One-time setup on GitHub: **Settings → Pages → Build and deployment → Source:
GitHub Actions**.

## Customizing

- Site title and subtitle: `SITE_TITLE` / `SITE_DESCRIPTION` in `build.py`
- Site base URL (for the RSS feed): `SITE_URL` in `build.py`
- Styling: `static/style.css`
- Page layout: the `page()` function in `build.py`
