import argparse
import functools
import http.server
import re
import sys
from datetime import date
from pathlib import Path

from . import site


def slugify(title):
    s = re.sub(r"[^a-z0-9]+", "-", title.lower()).strip("-")
    return s or "untitled"


def cmd_init(args):
    site.init(args.dir)
    print(f"created a starter site in {args.dir}/")
    print(f"next: tinysite build {args.dir} && tinysite serve {args.dir}")
    return 0


def cmd_build(args):
    written = site.build(args.dir, args.out, args.base_url)
    out = Path(args.out) if args.out else Path(args.dir) / "_site"
    print(f"wrote {len(written)} file(s) to {out}/")
    return 0


def cmd_new(args):
    content = Path(args.dir) / "content"
    if not content.is_dir():
        raise site.SiteError(f"no content/ folder in {args.dir}; run 'tinysite init' first")
    slug = args.slug or slugify(args.title)
    path = content / f"{slug}.md"
    if path.exists():
        raise site.SiteError(f"{path} already exists")
    lines = ["---", f"title: {args.title}"]
    if not args.page:
        lines.append(f"date: {date.today().isoformat()}")
    lines += ["---", "", ""]
    path.write_text("\n".join(lines), encoding="utf-8")
    print(f"created {path}")
    return 0


def cmd_serve(args):
    out = Path(args.out) if args.out else Path(args.dir) / "_site"
    if not out.is_dir():
        site.build(args.dir, args.out, args.base_url)
    handler = functools.partial(http.server.SimpleHTTPRequestHandler, directory=str(out))
    with http.server.ThreadingHTTPServer(("127.0.0.1", args.port), handler) as srv:
        print(f"serving {out}/ at http://127.0.0.1:{args.port}/  (ctrl-c to stop)")
        try:
            srv.serve_forever()
        except KeyboardInterrupt:
            print()
    return 0


def build_parser():
    p = argparse.ArgumentParser(prog="tinysite", description="a very small static site generator")
    sub = p.add_subparsers(dest="cmd", required=True)

    def common(sp):
        sp.add_argument("dir", nargs="?", default=".", help="site folder (default: current)")

    i = sub.add_parser("init", help="create a starter site")
    common(i)
    i.set_defaults(fn=cmd_init)

    b = sub.add_parser("build", help="render the site into _site/")
    common(b)
    b.add_argument("-o", "--out", help="output folder (default: <dir>/_site)")
    b.add_argument("--base-url", default="https://example.com", help="used for absolute links in the feed")
    b.set_defaults(fn=cmd_build)

    n = sub.add_parser("new", help="create a new post (or page) file")
    common(n)
    n.add_argument("title")
    n.add_argument("--slug", help="file name without .md (default: from the title)")
    n.add_argument("--page", action="store_true", help="a page, not a dated post")
    n.set_defaults(fn=cmd_new)

    s = sub.add_parser("serve", help="serve the built site locally")
    common(s)
    s.add_argument("-o", "--out")
    s.add_argument("--base-url", default="https://example.com")
    s.add_argument("--port", type=int, default=8000)
    s.set_defaults(fn=cmd_serve)

    return p


def main(argv=None):
    args = build_parser().parse_args(argv)
    try:
        return args.fn(args)
    except site.SiteError as e:
        print(f"error: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
