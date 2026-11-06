# tinysite

A very small static site generator. Markdown files in, a folder of HTML out,
nothing else. No plugins, no themes marketplace, no JavaScript build step.

I built it because every time I wanted to put a few notes online I ended up
fighting a generator with more features than my site had pages. This one
fits in your head: a `content/` folder, two templates, and a `build` command.

## Who it's for

Me, for a personal notes site. Also anyone who wants a blog or a handful of
pages on GitHub Pages and would rather read 400 lines of Python than a
plugin API.

## Built with

- Python 3.9+, standard library only (its own small Markdown converter,
  `string.Template` for templates, `http.server` for previewing).
- `pytest` for the tests.

## Install

```sh
git clone https://github.com/ksliu0307us-ua/tinysite.git
cd tinysite
pip install -e .
```

Or run it without installing: `python -m tinysite.cli ...` from the repo folder.

## Quick start

```sh
tinysite init myblog        # starter site: a home page, one post, a stylesheet
cd myblog
tinysite new "First real post"
#   -> content/first-real-post.md, open it and write
tinysite build              # renders into _site/
tinysite serve              # http://127.0.0.1:8000/
```

## How a site is laid out

```
myblog/
  site.txt          the site title, one line
  content/          one .md file per page
    index.md        the home page body (optional)
    hello.md        a post
  templates/        page.html and index.html (optional, defaults are built in)
  static/           copied as-is into the output (css, images)
  _site/            the generated site; don't edit, it's wiped on every build
```

A content file starts with a small front matter block:

```markdown
---
title: Hello, world
date: 2026-11-06
---
Body in Markdown.
```

`title` is required. A `date` makes it a **post**, which gets listed on the
home page and in `feed.xml`; without one it's a plain **page** (an About
page, say). Any other `key: value` line is available to templates as
`$key`.

## Templates

Templates are plain HTML with `$placeholders` (Python's `string.Template`).
`page.html` gets `$title`, `$date`, `$date_line`, `$content`, `$url`,
`$site_title` and any extra front matter keys. `index.html` gets
`$site_title`, `$content` (from `content/index.md`) and `$post_list`.

Run `tinysite init` to get the default templates written out, then edit them.

## Markdown support

Headings, paragraphs, **bold**, *italic*, `inline code`, links, images,
bullet and numbered lists, blockquotes and fenced code blocks. That's the
subset I use; anything else falls through as a paragraph. HTML in content is
escaped. See [`tinysite/markdown.py`](tinysite/markdown.py); it's small on purpose.

## Deploying to GitHub Pages

Build, then push the contents of `_site/` to a `gh-pages` branch or the
`docs/` folder of your repo. Pass `--base-url https://you.github.io` so the
feed has absolute links.

Links are currently root-absolute (`/style.css`, `/hello/`), which works for
a user site (`you.github.io`) but not yet for a project site served under
`/repo/`. That's first on the roadmap.

## Running the tests

```sh
pip install pytest
pytest
```

## Roadmap

See [ROADMAP.md](ROADMAP.md). Issues and PRs welcome.

## License

MIT. See [LICENSE](LICENSE).
