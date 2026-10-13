"""Convert Bot API message entities into a small sanitised HTML dialect.

Only tags the website's RichText field understands are emitted:
``<p>``, ``<b>``, ``<i>``, ``<a href>`` and ``<br/>``. Everything else
(underline, strikethrough, code, pre, spoiler, hashtags, mentions-by-id,
custom emoji) is kept as plain text. Emoji pass through as Unicode.

Bot API entity offsets are UTF-16 code units, so they are mapped onto Python
codepoint indices before building tags (important for emoji-heavy posts).
"""

import bisect
import html as _html
import re

_URL_RE = re.compile(r"^[a-zA-Z][a-zA-Z0-9+.-]*://")


def _entity_tags(entity, text):
    etype = entity.get("type")
    if etype == "bold":
        return "<b>", "</b>"
    if etype == "italic":
        return "<i>", "</i>"
    if etype == "text_link":
        return f'<a href="{_html.escape(entity.get("url") or "", quote=True)}">', "</a>"
    if etype == "url":
        url = text if _URL_RE.match(text) else "https://" + text
        return f'<a href="{_html.escape(url, quote=True)}">', "</a>"
    if etype == "mention":
        username = text.lstrip("@")
        return f'<a href="https://t.me/{_html.escape(username, quote=True)}">', "</a>"
    if etype == "email":
        return f'<a href="mailto:{_html.escape(text, quote=True)}">', "</a>"
    return None, None


def _entity_ranges(text, entities):
    """Map entity UTF-16 offsets onto Python codepoint indices."""
    utf16 = []
    total = 0
    for ch in text:
        utf16.append(total)
        total += 2 if ord(ch) > 0xFFFF else 1
    utf16.append(total)

    ranges = []
    for entity in entities:
        offset = entity.get("offset", 0)
        length = entity.get("length", 0)
        if offset < 0 or length <= 0:
            continue
        start = bisect.bisect_left(utf16, offset)
        end = bisect.bisect_left(utf16, offset + length)
        if end > start:
            ranges.append((start, end, entity))
    return ranges


def _apply_entities(text, entities):
    if not entities:
        return _html.escape(text, quote=False)

    opens = {}
    closes = {}
    for start, end, entity in _entity_ranges(text, entities):
        open_tag, close_tag = _entity_tags(entity, text[start:end])
        if open_tag is None:
            continue
        opens.setdefault(start, []).append(open_tag)
        closes.setdefault(end, []).append(close_tag)

    positions = sorted(set(opens) | set(closes))
    if not positions:
        return _html.escape(text, quote=False)

    out = []
    last = 0
    for pos in positions:
        if pos > last:
            out.append(_html.escape(text[last:pos], quote=False))
        for tag in closes.get(pos, []):
            out.append(tag)
        for tag in opens.get(pos, []):
            out.append(tag)
        last = pos
    out.append(_html.escape(text[last:], quote=False))
    return "".join(out)


def to_html(text, entities=None):
    """Plain text + entities -> minimal HTML with paragraphs and line breaks."""
    if not text:
        return ""
    tagged = _apply_entities(text, entities or [])
    parts = []
    for paragraph in re.split(r"\n\s*\n", tagged):
        paragraph = paragraph.replace("\n", "<br/>").strip()
        if paragraph:
            parts.append(f"<p>{paragraph}</p>")
    return "".join(parts)
