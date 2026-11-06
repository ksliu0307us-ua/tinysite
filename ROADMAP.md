# Roadmap

Roughly in the order I plan to do them.

## Soon

- [ ] `--base-path /repo` so links work on a GitHub Pages *project* site, not just a user site
- [ ] `tinysite deploy` that builds into `docs/` (or a `gh-pages` branch) ready for Pages
- [ ] `serve --watch`: rebuild when a file in `content/`, `templates/` or `static/` changes
- [ ] Draft posts: `draft: true` in front matter skips the file unless `--drafts` is passed
- [ ] A GitHub Actions workflow template that builds and publishes on push
- [ ] Nicer `new`: open the file in `$EDITOR` after creating it

## Markdown

- [ ] Nested lists
- [ ] Tables
- [ ] Horizontal rules (`---` outside front matter)
- [ ] Automatic `id` on headings so sections can be linked
- [ ] Footnotes
- [ ] Decide whether to keep the hand-written converter or add an optional `markdown` dependency

## Next

- [ ] Tags: `tags: python, git` in front matter, one listing page per tag
- [ ] Pagination on the index once there are more than N posts
- [ ] Sitemap.xml
- [ ] Syntax highlighting for fenced code blocks (probably a small client-side script, or Pygments as an optional extra)
- [ ] Per-page templates: `template: project.html` in front matter
- [ ] Excerpts on the index (first paragraph, or `<!-- more -->`)

## Later / maybe

- [ ] Incremental builds (only re-render what changed)
- [ ] Themes as a folder you can copy in
- [ ] Publish to PyPI

## Housekeeping

- [ ] Tests for the CLI commands, not only the modules
- [ ] GitHub Actions running `pytest`
- [ ] Type hints and a `mypy` pass
- [ ] CHANGELOG.md starting at 0.2.0
