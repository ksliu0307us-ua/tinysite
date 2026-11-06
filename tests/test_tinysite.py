import pytest

from tinysite import markdown, site
from tinysite.cli import slugify


# --- markdown --------------------------------------------------------------


def test_headings_and_paragraphs():
    out = markdown.convert("# Title\n\nSome text\nover two lines.\n\n## Sub")
    assert out == "<h1>Title</h1>\n<p>Some text over two lines.</p>\n<h2>Sub</h2>"


def test_inline_markup():
    out = markdown.convert("**bold** and *italic* and `code` and [a link](https://x.y)")
    assert "<strong>bold</strong>" in out
    assert "<em>italic</em>" in out
    assert "<code>code</code>" in out
    assert '<a href="https://x.y">a link</a>' in out


def test_markup_inside_code_is_left_alone():
    assert "<em>" not in markdown.convert("`*not italic*`")


def test_html_is_escaped():
    out = markdown.convert("<script>alert(1)</script>")
    assert "<script>" not in out
    assert "&lt;script&gt;" in out


def test_lists():
    assert markdown.convert("- a\n- b") == "<ul><li>a</li><li>b</li></ul>"
    assert markdown.convert("1. a\n2. b") == "<ol><li>a</li><li>b</li></ol>"


def test_fenced_code_keeps_text_verbatim():
    out = markdown.convert("```python\nx = 1 < 2  # *not* italic\n```")
    assert out == '<pre><code class="language-python">x = 1 &lt; 2  # *not* italic</code></pre>'


def test_blockquote():
    assert markdown.convert("> quoted\n> text") == "<blockquote><p>quoted text</p></blockquote>"


def test_image():
    assert markdown.convert("![alt](/pic.png)") == '<p><img src="/pic.png" alt="alt"></p>'


# --- front matter / pages --------------------------------------------------


def test_front_matter():
    meta, body = site.parse_front_matter("---\ntitle: Hi\ndate: 2026-01-02\n---\nbody here\n")
    assert meta == {"title": "Hi", "date": "2026-01-02"}
    assert body == "body here\n"


def test_no_front_matter():
    meta, body = site.parse_front_matter("just text")
    assert meta == {} and body == "just text"


def test_missing_title_is_an_error(tmp_path):
    f = tmp_path / "x.md"
    f.write_text("---\ndate: 2026-01-01\n---\nhi")
    with pytest.raises(site.SiteError):
        site.load_page(f)


def test_bad_date_is_an_error(tmp_path):
    f = tmp_path / "x.md"
    f.write_text("---\ntitle: x\ndate: yesterday\n---\nhi")
    with pytest.raises(site.SiteError):
        site.load_page(f)


# --- build -----------------------------------------------------------------


def test_init_then_build(tmp_path):
    root = tmp_path / "blog"
    site.init(root)
    written = site.build(root, base_url="https://me.example")
    out = root / "_site"

    assert (out / "index.html").exists()
    assert (out / "hello" / "index.html").exists()
    assert (out / "feed.xml").exists()
    assert (out / "style.css").exists()

    index = (out / "index.html").read_text()
    assert '<a href="/hello/">Hello, world</a>' in index

    feed = (out / "feed.xml").read_text()
    assert "<link>https://me.example/hello/</link>" in feed


def test_pages_without_date_are_not_posts(tmp_path):
    root = tmp_path / "blog"
    site.init(root)
    (root / "content" / "about.md").write_text("---\ntitle: About\n---\nme")
    site.build(root)
    out = root / "_site"
    assert (out / "about" / "index.html").exists()
    assert "/about/" not in (out / "index.html").read_text()


def test_init_refuses_to_clobber(tmp_path):
    site.init(tmp_path / "s")
    with pytest.raises(site.SiteError):
        site.init(tmp_path / "s")


def test_slugify():
    assert slugify("Hello, World!  2026") == "hello-world-2026"
    assert slugify("???") == "untitled"
