"""Load content, render pages, write the output folder.

Site layout:

    content/     one .md file per page, with a front matter block at the top
    templates/   page.html and index.html, using $placeholders
    static/      copied as-is into the output
    _site/       the generated site (output)

Front matter is a few `key: value` lines between two `---` lines. `title` is
required; `date` (YYYY-MM-DD) marks a page as a post so it shows up in the
index and feed. Everything else is passed through to the template as-is.
"""

import re
import shutil
from dataclasses import dataclass, field
from datetime import date
from email.utils import format_datetime
from datetime import datetime, timezone
from pathlib import Path
from string import Template
from html import escape

from . import markdown

DEFAULT_PAGE = """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>$title - $site_title</title>
<link rel="stylesheet" href="/style.css">
<link rel="alternate" type="application/rss+xml" title="$site_title" href="/feed.xml">
</head>
<body>
<header><a href="/">$site_title</a></header>
<main>
<h1>$title</h1>
$date_line
$content
</main>
<footer>built with tinysite</footer>
</body>
</html>
"""

DEFAULT_INDEX = """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>$site_title</title>
<link rel="stylesheet" href="/style.css">
<link rel="alternate" type="application/rss+xml" title="$site_title" href="/feed.xml">
</head>
<body>
<header><a href="/">$site_title</a></header>
<main>
<h1>$site_title</h1>
$content
<ul class="posts">
$post_list
</ul>
</main>
<footer>built with tinysite</footer>
</body>
</html>
"""

DEFAULT_CSS = """body { max-width: 42rem; margin: 2rem auto; padding: 0 1rem;
  font: 1.05rem/1.6 system-ui, sans-serif; color: #222; }
header a { font-weight: bold; text-decoration: none; color: inherit; }
pre { background: #f4f4f4; padding: 1rem; overflow-x: auto; }
code { background: #f4f4f4; padding: 0 .2em; }
pre code { padding: 0; }
.posts { list-style: none; padding: 0; }
.posts li { margin: .4rem 0; }
.posts time { color: #777; margin-right: .6rem; font-variant-numeric: tabular-nums; }
footer { margin-top: 3rem; color: #999; font-size: .9rem; }
"""

_FRONT = re.compile(r"^---\s*\n(.*?)\n---\s*\n?", re.DOTALL)


class SiteError(Exception):
    pass


@dataclass
class Page:
    slug: str
    title: str
    body_md: str
    date: str = ""
    meta: dict = field(default_factory=dict)

    @property
    def is_post(self):
        return bool(self.date)

    @property
    def url(self):
        return "/" if self.slug == "index" else f"/{self.slug}/"


def parse_front_matter(text):
    m = _FRONT.match(text)
    if not m:
        return {}, text
    meta = {}
    for line in m.group(1).splitlines():
        if ":" in line:
            k, v = line.split(":", 1)
            meta[k.strip()] = v.strip()
    return meta, text[m.end() :]


def load_page(path):
    meta, body = parse_front_matter(Path(path).read_text(encoding="utf-8"))
    if "title" not in meta:
        raise SiteError(f"{path}: front matter needs a 'title' line")
    d = meta.get("date", "")
    if d:
        try:
            date.fromisoformat(d)
        except ValueError:
            raise SiteError(f"{path}: date must be YYYY-MM-DD, got '{d}'")
    return Page(slug=Path(path).stem, title=meta["title"], body_md=body, date=d, meta=meta)


def load_site(root):
    root = Path(root)
    content = root / "content"
    if not content.is_dir():
        raise SiteError(f"no content/ folder in {root}")
    pages = [load_page(p) for p in sorted(content.glob("*.md"))]
    return pages


def _template(root, name, default):
    path = Path(root) / "templates" / name
    return Template(path.read_text(encoding="utf-8") if path.exists() else default)


def _site_title(root):
    cfg = Path(root) / "site.txt"
    return cfg.read_text(encoding="utf-8").strip() if cfg.exists() else "My site"


def render_page(page, tpl, site_title):
    date_line = f'<p class="date"><time datetime="{page.date}">{page.date}</time></p>' if page.date else ""
    values = {
        "title": escape(page.title),
        "site_title": escape(site_title),
        "date": page.date,
        "date_line": date_line,
        "content": markdown.convert(page.body_md),
        "url": page.url,
    }
    values.update({k: escape(v) for k, v in page.meta.items() if k not in values})
    return tpl.safe_substitute(values)


def render_index(pages, tpl, site_title, index_page=None):
    posts = sorted((p for p in pages if p.is_post), key=lambda p: p.date, reverse=True)
    items = "\n".join(
        f'<li><time datetime="{p.date}">{p.date}</time> <a href="{p.url}">{escape(p.title)}</a></li>'
        for p in posts
    )
    content = markdown.convert(index_page.body_md) if index_page else ""
    return tpl.safe_substitute(site_title=escape(site_title), post_list=items, content=content)


def render_feed(pages, site_title, base_url):
    posts = sorted((p for p in pages if p.is_post), key=lambda p: p.date, reverse=True)
    base = base_url.rstrip("/")
    items = []
    for p in posts:
        pub = datetime.fromisoformat(p.date).replace(tzinfo=timezone.utc)
        items.append(
            "<item>"
            f"<title>{escape(p.title)}</title>"
            f"<link>{base}{p.url}</link>"
            f"<guid>{base}{p.url}</guid>"
            f"<pubDate>{format_datetime(pub)}</pubDate>"
            f"<description>{escape(markdown.convert(p.body_md))}</description>"
            "</item>"
        )
    return (
        '<?xml version="1.0" encoding="UTF-8"?>'
        '<rss version="2.0"><channel>'
        f"<title>{escape(site_title)}</title><link>{base}/</link>"
        f"<description>{escape(site_title)}</description>"
        + "".join(items)
        + "</channel></rss>"
    )


def build(root, out=None, base_url="https://example.com"):
    root = Path(root)
    out = Path(out) if out else root / "_site"
    pages = load_site(root)
    site_title = _site_title(root)
    page_tpl = _template(root, "page.html", DEFAULT_PAGE)
    index_tpl = _template(root, "index.html", DEFAULT_INDEX)

    if out.exists():
        shutil.rmtree(out)
    out.mkdir(parents=True)

    index_page = next((p for p in pages if p.slug == "index"), None)
    written = []
    for p in pages:
        if p.slug == "index":
            continue
        dest = out / p.slug / "index.html"
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_text(render_page(p, page_tpl, site_title), encoding="utf-8")
        written.append(dest)

    (out / "index.html").write_text(render_index(pages, index_tpl, site_title, index_page), encoding="utf-8")
    (out / "feed.xml").write_text(render_feed(pages, site_title, base_url), encoding="utf-8")
    written += [out / "index.html", out / "feed.xml"]

    static = root / "static"
    if static.is_dir():
        shutil.copytree(static, out, dirs_exist_ok=True)
    if not (out / "style.css").exists():
        (out / "style.css").write_text(DEFAULT_CSS, encoding="utf-8")

    return written


def init(root):
    """Create a starter site in `root`."""
    root = Path(root)
    if (root / "content").exists():
        raise SiteError(f"{root} already has a content/ folder")
    (root / "content").mkdir(parents=True)
    (root / "templates").mkdir()
    (root / "static").mkdir()
    (root / "site.txt").write_text("My site\n", encoding="utf-8")
    (root / "templates" / "page.html").write_text(DEFAULT_PAGE, encoding="utf-8")
    (root / "templates" / "index.html").write_text(DEFAULT_INDEX, encoding="utf-8")
    (root / "static" / "style.css").write_text(DEFAULT_CSS, encoding="utf-8")
    (root / "content" / "index.md").write_text(
        "---\ntitle: Home\n---\nWelcome. Posts are listed below.\n", encoding="utf-8"
    )
    today = date.today().isoformat()
    (root / "content" / "hello.md").write_text(
        f"---\ntitle: Hello, world\ndate: {today}\n---\n"
        "This is the first post. Edit `content/hello.md` or add another file.\n\n"
        "## Things that work\n\n- **bold** and *italic*\n- `inline code`\n- [links](https://example.com)\n\n"
        "```python\nprint('and code blocks')\n```\n",
        encoding="utf-8",
    )
