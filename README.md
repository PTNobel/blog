# Meditations by Parth

> a blog on cooking, mathematics, and whatever passes my fancy

A tiny static blog generator: Markdown files in `posts/` become HTML in `_site/`,
built by a single Python script and deployed to GitHub Pages via GitHub Actions.

## Writing a post

Add a Markdown file to `posts/` with a unique counter and a short description,
such as `003-my-great-post.md`. The `published` flag is required — the build
errors if it's missing, so you never accidentally publish (or hide) a post by
forgetting it.

```markdown
---
title: My Great Post
published: true
---

Your content here, in **Markdown**.
```

The counter is replaced in the rendered URL by the date of the first Git commit
that sets `published: true`. Dates use Baker Island time (`Etc/GMT+12`), and
published posts are listed newest-first. Because dates come from Git history,
the post must be committed before a published build can succeed.

Supported Markdown: fenced code blocks, tables, footnotes, smart quotes, and
TeX math. Use `$...$` for inline math and `$$...$$` on its own line for display
math:

```markdown
Euler's identity is $e^{i\pi} + 1 = 0$.

$$
\sum_{k=1}^n k = \frac{n(n+1)}{2}
$$
```

TeX is converted to native MathML when the site is built, so rendering does not
require JavaScript.

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
published: false
---
```

The post is still built and deployed at its numbered URL (for example,
`003-work-in-progress/`), so you can share that link for feedback. It isn't
linked from the home page and is tagged `noindex` so search engines skip it.
When a commit changes the flag to `true`, the numbered prefix is replaced by
that commit's Baker Island date.

## Build locally

```sh
uv run build.py      # writes the site to _site/
```

Preview it:

```sh
uv run python -m http.server -d _site 8000   # then open http://localhost:8000
```

`build.py` uses [uv](https://docs.astral.sh/uv/)'s inline script dependencies, so
there's nothing to install first — `uv run` fetches everything automatically.

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
