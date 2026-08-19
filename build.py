# /// script
# requires-python = ">=3.11"
# dependencies = [
#     "latex2mathml>=3.81",
#     "markdown-it-py>=4.2",
#     "mdit-py-plugins>=0.6.1",
#     "python-frontmatter>=1.1",
# ]
# ///
"""Build a static blog from markdown files in posts/ into _site/.

Run locally with:  uv run build.py
"""

from __future__ import annotations

import datetime as dt
import html
import shutil
from email.utils import format_datetime
from pathlib import Path

import frontmatter
from latex2mathml.converter import convert
from markdown_it import MarkdownIt
from mdit_py_plugins.dollarmath import dollarmath_plugin
from mdit_py_plugins.footnote import footnote_plugin

# --- Site configuration ------------------------------------------------------

SITE_TITLE = "Meditations by Parth"
SITE_DESCRIPTION = "a blog on cooking, mathematics, and whatever passes my fancy"
# Absolute base URL where the site is published (no trailing slash). Used to
# build the absolute links the RSS feed requires.
SITE_URL = "https://ptnobel.github.io/blog"

ROOT = Path(__file__).parent
POSTS_DIR = ROOT / "posts"
STATIC_DIR = ROOT / "static"
OUTPUT_DIR = ROOT / "_site"


def render_math(tex: str, options: dict[str, object]) -> str:
    """Render a parsed TeX expression as native MathML."""
    display = "block" if options["display_mode"] else "inline"
    return convert(tex, display=display)


MD = (
    MarkdownIt("commonmark", {"typographer": True})
    .enable(["table", "replacements", "smartquotes"])
    .use(footnote_plugin)
    .use(
        dollarmath_plugin,
        renderer=render_math,
        allow_space=False,
        allow_digits=True,
    )
)


# --- Helpers -----------------------------------------------------------------


def parse_date(value: object) -> dt.date:
    """Coerce a frontmatter date (date, datetime, or ISO string) to a date."""
    if isinstance(value, dt.datetime):
        return value.date()
    if isinstance(value, dt.date):
        return value
    if isinstance(value, str):
        return dt.date.fromisoformat(value.strip())
    raise ValueError(f"Unsupported date value: {value!r}")


def parse_published(metadata: dict, path: Path) -> bool:
    """Require an explicit boolean 'published' flag in the frontmatter."""
    if "published" not in metadata:
        raise ValueError(
            f"{path.name}: frontmatter is missing 'published' "
            f"(set 'published: true' to list it, or 'published: false' for a draft)"
        )
    value = metadata["published"]
    if not isinstance(value, bool):
        raise ValueError(
            f"{path.name}: 'published' must be true or false, got {value!r}"
        )
    return value


class Post:
    def __init__(self, path: Path):
        doc = frontmatter.load(path)
        self.title = doc.get("title") or path.stem
        self.date = parse_date(doc.get("date", dt.date.today()))
        self.published = parse_published(doc.metadata, path)
        self.slug = path.stem
        self.body_html = MD.render(doc.content)

    @property
    def url(self) -> str:
        return f"{self.slug}/"

    @property
    def date_iso(self) -> str:
        return self.date.isoformat()

    @property
    def date_human(self) -> str:
        return self.date.strftime("%B %-d, %Y")


def page(title: str, body: str, *, rel: str = "./", is_home: bool = False, noindex: bool = False) -> str:
    """Wrap body content in the shared HTML layout.

    `rel` is the relative path from the page back to the site root (e.g. "../"
    for a post at <slug>/index.html, "" for the root index).
    """
    home_link = "" if is_home else f'<p><a href="{rel}">&larr; All posts</a></p>'
    robots = '\n  <meta name="robots" content="noindex">' if noindex else ""
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">{robots}
  <title>{html.escape(title)}</title>
  <link rel="stylesheet" href="{rel}style.css">
  <link rel="alternate" type="application/rss+xml" title="{html.escape(SITE_TITLE)}" href="{rel}feed.xml">
</head>
<body>
  <header>
    <a class="site-title" href="{rel}">{html.escape(SITE_TITLE)}</a>
  </header>
  <main>
{home_link}
{body}
  </main>
  <footer>
    <p><a href="{rel}feed.xml">RSS</a></p>
  </footer>
</body>
</html>
"""


# --- Build steps -------------------------------------------------------------


def load_posts() -> list[Post]:
    posts = [Post(p) for p in POSTS_DIR.glob("*.md")]
    posts.sort(key=lambda p: p.date, reverse=True)
    return posts


def render_post(post: Post) -> str:
    draft = "" if post.published else '  <p class="draft-notice">Draft &mdash; unlisted</p>\n'
    body = f"""<article>
  <h1>{html.escape(post.title)}</h1>
  <p class="meta"><time datetime="{post.date_iso}">{post.date_human}</time></p>
{draft}{post.body_html}
</article>"""
    return page(post.title, body, rel="../", noindex=not post.published)


def render_index(posts: list[Post]) -> str:
    items = "\n".join(
        f'    <li><time datetime="{p.date_iso}">{p.date_human}</time>'
        f' &mdash; <a href="{p.url}">{html.escape(p.title)}</a></li>'
        for p in posts
        if p.published
    )
    body = f"""<p class="lead">{html.escape(SITE_DESCRIPTION)}</p>
  <ul class="post-list">
{items}
  </ul>"""
    return page(SITE_TITLE, body, is_home=True)


def render_feed(posts: list[Post]) -> str:
    """Render an RSS 2.0 feed of the published posts."""
    now = format_datetime(dt.datetime.now(dt.timezone.utc))

    items = []
    for post in posts:
        if not post.published:
            continue
        link = f"{SITE_URL}/{post.url}"
        # RSS wants an RFC 822 date; posts only carry a date, so anchor at
        # midnight UTC.
        pub = format_datetime(
            dt.datetime.combine(post.date, dt.time(), tzinfo=dt.timezone.utc)
        )
        # Wrap the rendered HTML in CDATA; guard against an accidental "]]>".
        content = post.body_html.replace("]]>", "]]&gt;")
        items.append(
            f"""    <item>
      <title>{html.escape(post.title)}</title>
      <link>{html.escape(link)}</link>
      <guid isPermaLink="true">{html.escape(link)}</guid>
      <pubDate>{pub}</pubDate>
      <description><![CDATA[{content}]]></description>
    </item>"""
        )

    items_xml = "\n".join(items)
    return f"""<?xml version="1.0" encoding="utf-8"?>
<rss version="2.0" xmlns:atom="http://www.w3.org/2005/Atom">
  <channel>
    <title>{html.escape(SITE_TITLE)}</title>
    <link>{html.escape(SITE_URL)}/</link>
    <atom:link href="{html.escape(SITE_URL)}/feed.xml" rel="self" type="application/rss+xml"/>
    <description>{html.escape(SITE_DESCRIPTION)}</description>
    <language>en</language>
    <lastBuildDate>{now}</lastBuildDate>
{items_xml}
  </channel>
</rss>
"""


def main() -> None:
    if OUTPUT_DIR.exists():
        shutil.rmtree(OUTPUT_DIR)
    OUTPUT_DIR.mkdir(parents=True)

    posts = load_posts()
    for post in posts:
        out_path = OUTPUT_DIR / post.slug / "index.html"
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(render_post(post), encoding="utf-8")

    (OUTPUT_DIR / "index.html").write_text(render_index(posts), encoding="utf-8")
    (OUTPUT_DIR / "feed.xml").write_text(render_feed(posts), encoding="utf-8")

    if STATIC_DIR.exists():
        for item in STATIC_DIR.iterdir():
            dest = OUTPUT_DIR / item.name
            if item.is_dir():
                shutil.copytree(item, dest)
            else:
                shutil.copy2(item, dest)

    drafts = sum(1 for p in posts if not p.published)
    suffix = f" ({drafts} unlisted)" if drafts else ""
    print(f"Built {len(posts)} post(s){suffix} into {OUTPUT_DIR.relative_to(ROOT)}/")


if __name__ == "__main__":
    main()
