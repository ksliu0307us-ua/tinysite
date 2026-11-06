"""A small Markdown-to-HTML converter.

Deliberately not a full CommonMark implementation. It handles the subset I
actually use when writing posts: headings, paragraphs, bold/italic, inline
code, links, images, bullet and numbered lists, blockquotes and fenced code
blocks. Anything else comes out as a paragraph, which is a fine fallback.
"""

import html
import re

_INLINE_CODE = re.compile(r"`([^`]+)`")
_BOLD = re.compile(r"\*\*(.+?)\*\*")
_ITALIC = re.compile(r"(?<!\*)\*([^*]+?)\*(?!\*)")
_IMAGE = re.compile(r"!\[([^\]]*)\]\(([^)\s]+)\)")
_LINK = re.compile(r"\[([^\]]+)\]\(([^)\s]+)\)")
_HEADING = re.compile(r"^(#{1,6})\s+(.*)$")
_ORDERED = re.compile(r"^\d+\.\s+(.*)$")


def inline(text):
    """Convert inline markup inside one line of already-escaped text."""
    # code first, so markup inside backticks is left alone
    parts = []
    last = 0
    for m in _INLINE_CODE.finditer(text):
        parts.append(_inline_no_code(text[last : m.start()]))
        parts.append(f"<code>{m.group(1)}</code>")
        last = m.end()
    parts.append(_inline_no_code(text[last:]))
    return "".join(parts)


def _inline_no_code(text):
    text = _IMAGE.sub(r'<img src="\2" alt="\1">', text)
    text = _LINK.sub(r'<a href="\2">\1</a>', text)
    text = _BOLD.sub(r"<strong>\1</strong>", text)
    text = _ITALIC.sub(r"<em>\1</em>", text)
    return text


def convert(md):
    lines = md.splitlines()
    out = []
    i = 0
    n = len(lines)

    while i < n:
        line = lines[i]
        stripped = line.strip()

        if not stripped:
            i += 1
            continue

        # fenced code block
        if stripped.startswith("```"):
            lang = stripped[3:].strip()
            i += 1
            code = []
            while i < n and not lines[i].strip().startswith("```"):
                code.append(lines[i])
                i += 1
            i += 1  # closing fence
            cls = f' class="language-{lang}"' if lang else ""
            out.append(f"<pre><code{cls}>{html.escape(chr(10).join(code))}</code></pre>")
            continue

        m = _HEADING.match(stripped)
        if m:
            level = len(m.group(1))
            out.append(f"<h{level}>{inline(html.escape(m.group(2)))}</h{level}>")
            i += 1
            continue

        if stripped.startswith("> "):
            quote = []
            while i < n and lines[i].strip().startswith("> "):
                quote.append(lines[i].strip()[2:])
                i += 1
            out.append(f"<blockquote>{convert(chr(10).join(quote))}</blockquote>")
            continue

        if stripped.startswith("- ") or stripped.startswith("* "):
            items = []
            while i < n and (lines[i].strip().startswith("- ") or lines[i].strip().startswith("* ")):
                items.append(inline(html.escape(lines[i].strip()[2:])))
                i += 1
            out.append("<ul>" + "".join(f"<li>{it}</li>" for it in items) + "</ul>")
            continue

        if _ORDERED.match(stripped):
            items = []
            while i < n and _ORDERED.match(lines[i].strip()):
                items.append(inline(html.escape(_ORDERED.match(lines[i].strip()).group(1))))
                i += 1
            out.append("<ol>" + "".join(f"<li>{it}</li>" for it in items) + "</ol>")
            continue

        # paragraph: gather until a blank line or something that isn't prose
        para = []
        while i < n and lines[i].strip() and not _is_block_start(lines[i].strip()):
            para.append(lines[i].strip())
            i += 1
        out.append(f"<p>{inline(html.escape(' '.join(para)))}</p>")

    return "\n".join(out)


def _is_block_start(s):
    return (
        s.startswith("```")
        or _HEADING.match(s)
        or s.startswith("> ")
        or s.startswith("- ")
        or s.startswith("* ")
        or _ORDERED.match(s)
    )
