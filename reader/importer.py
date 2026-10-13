"""Import a Telegram Desktop chat export into the post store.

Telegram Desktop's ``Export chat history`` produces a folder like
``ChatExport_2026-09-25`` containing ``result.json`` plus ``photos`` (and,
optionally, ``videos`` / ``files``) directories. The message objects in
``result.json`` differ from Bot API ``channel_post`` objects:

- ``text`` is either a plain string or a list of str / entity-dict segments;
- entities carry their text inline (no offset/length);
- ``photo`` is a relative path such as ``photos/photo_2@14-09-2024_19-57-11.jpg``;
- videos use ``media_type == "video_file"`` and a ``file`` path;
- ``id`` is the real Telegram message id.

This module converts those messages into the same shape the live syncer
persists and upserts them into the shared SQLite store, copying media files
into ``TG_MEDIA_DIR`` so the existing ``/media/<file>`` endpoint can serve them.
"""

import html as _html
import json
import os
import re
import shutil
from datetime import datetime, timezone as dt_timezone

from . import config
from .html import to_html
from .store import Store

_URL_RE = re.compile(r"^[a-zA-Z][a-zA-Z0-9+.-]*://")

_VIDEO_TYPES = {"video_file", "video_message", "animation"}


def _channel_name():
    name = (config.config.channel or "").strip()
    for prefix in ("https://t.me/", "http://t.me/", "t.me/"):
        if name.startswith(prefix):
            name = name[len(prefix):]
    return name.lstrip("@").split("/")[0]


def _post_url(message_id):
    name = _channel_name()
    return f"https://t.me/{name}/{message_id}" if name else ""


_INLINE_TAG_RE = re.compile(r"(</?[a-zA-Z][^>]*>)")
_PARAGRAPH_SPLIT = re.compile(r"(\n\s*\n)")


def _closing(tag):
    match = re.match(r"<([a-zA-Z][a-zA-Z0-9]*)", tag)
    return f"</{match.group(1)}>" if match else ""


def _wrap_paragraphs(tagged):
    """Split tagged HTML into ``<p>`` blocks like ``html.to_html`` does, but
    rebalance inline tags (``<b>``/``<i>``/``<a>``) that span a paragraph
    break so they are closed before the break and reopened after it."""
    paragraphs = []
    open_tags = []  # stack of opening tags currently open
    current = []

    def flush():
        body = "".join(current)
        for tag in reversed(open_tags):
            body += _closing(tag)
        body = body.replace("\n", "<br/>").strip()
        if body:
            paragraphs.append(f"<p>{body}</p>")
        del current[:]
        for tag in open_tags:
            current.append(tag)

    for piece in _INLINE_TAG_RE.split(tagged):
        if not piece:
            continue
        if piece.startswith("<") and piece.endswith(">"):
            if piece.startswith("</"):
                if open_tags:
                    open_tags.pop()
            else:
                open_tags.append(piece)
            current.append(piece)
            continue
        for part in _PARAGRAPH_SPLIT.split(piece):
            if _PARAGRAPH_SPLIT.fullmatch(part):
                flush()
            else:
                current.append(part)

    if current:
        flush()
    html = "".join(paragraphs)
    # Drop empty inline elements left behind by formatting that only wrapped
    # a paragraph break (e.g. ``<b></b>`` around a split paragraph).
    html = re.sub(r"<(b|i)></\1>|<a[^>]*></a>", "", html)
    return html


def _segment_html(seg):
    """Render one export text segment (str or entity dict) to sanitised HTML."""
    if isinstance(seg, str):
        return _html.escape(seg, quote=False)

    etype = seg.get("type")
    text = _html.escape(seg.get("text") or "", quote=False)
    if etype == "bold":
        return f"<b>{text}</b>"
    if etype == "italic":
        return f"<i>{text}</i>"
    if etype == "link":
        url = seg.get("text") or ""
        if not _URL_RE.match(url):
            url = "https://" + url
        return f'<a href="{_html.escape(url, quote=True)}">{text}</a>'
    if etype == "text_link":
        url = seg.get("href") or ""
        return f'<a href="{_html.escape(url, quote=True)}">{text}</a>'
    if etype == "mention":
        username = (seg.get("text") or "").lstrip("@")
        return f'<a href="https://t.me/{_html.escape(username, quote=True)}">{text}</a>'
    if etype == "email":
        return f'<a href="mailto:{text}">{text}</a>'
    # blockquote, hashtag, custom_emoji, spoiler, plain, ... -> plain text.
    return text


def _text_html(msg):
    text = msg.get("text")
    if isinstance(text, str):
        return to_html(text, None)
    if isinstance(text, list):
        tagged = "".join(_segment_html(seg) for seg in text)
        return _wrap_paragraphs(tagged)
    return ""


def _media_kind(msg):
    if msg.get("photo"):
        return "photo"
    if msg.get("media_type") in _VIDEO_TYPES:
        return "video"
    return None


def _date_iso(msg):
    ts = msg.get("date_unixtime")
    if ts:
        try:
            return datetime.fromtimestamp(int(ts), tz=dt_timezone.utc).isoformat()
        except (ValueError, OverflowError, OSError):
            pass
    return msg.get("date") or ""


def _copy_media(export_dir, rel, media_dir):
    """Copy a media file from the export into ``media_dir``; return its url."""
    if not rel or not isinstance(rel, str):
        return None
    src = os.path.join(export_dir, rel)
    if not os.path.isfile(src):
        return None
    name = os.path.basename(rel)
    os.makedirs(media_dir, exist_ok=True)
    dest = os.path.join(media_dir, name)
    shutil.copy2(src, dest)
    return os.path.relpath(dest, media_dir)


def _resolve_folder(folder):
    candidates = []
    if os.path.isabs(folder):
        candidates.append(folder)
    else:
        candidates.append(os.path.join(config.config.export_dir, folder))
        candidates.append(os.path.join(os.getcwd(), folder))
    for cand in candidates:
        if os.path.isfile(os.path.join(cand, "result.json")):
            return os.path.abspath(cand)
    raise FileNotFoundError(
        f"ChatExport folder not found (looked for result.json in: "
        f"{', '.join(candidates)})"
    )


def import_folder(folder):
    """Import one ChatExport folder into the store. Returns a summary dict."""
    cfg = config.config
    export_dir = _resolve_folder(folder)
    result_path = os.path.join(export_dir, "result.json")
    with open(result_path, encoding="utf-8") as fh:
        data = json.load(fh)

    channel = (data.get("name") or "").strip() or _channel_name()
    store = Store(cfg.db_path)

    imported = 0
    for msg in data.get("messages") or []:
        if msg.get("type") != "message":
            continue

        post_id = int(msg["id"])
        text_html = _text_html(msg)

        attachments = []
        kind = _media_kind(msg)
        if kind == "photo":
            url = _copy_media(export_dir, msg.get("photo"), cfg.media_dir)
            if url:
                attachments.append(
                    {
                        "kind": "photo",
                        "url": url,
                        "original_url": _post_url(post_id),
                        "width": msg.get("width"),
                        "height": msg.get("height"),
                    }
                )
        elif kind == "video":
            url = _copy_media(export_dir, msg.get("file"), cfg.media_dir)
            if url:
                attachments.append(
                    {
                        "kind": "video",
                        "url": url,
                        "original_url": _post_url(post_id),
                        "duration": msg.get("duration_seconds"),
                        "width": msg.get("width"),
                        "height": msg.get("height"),
                    }
                )

        if not text_html and not attachments:
            continue

        store.upsert_post(
            {
                "id": post_id,
                "channel": channel,
                "date": _date_iso(msg),
                "text_html": text_html,
                "attachments": attachments,
            }
        )
        imported += 1

    return {
        "imported": imported,
        "folder": os.path.basename(export_dir),
        "channel": channel,
    }
