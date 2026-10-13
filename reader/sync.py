"""Receive channel posts via the Bot API and persist them."""

import os
from datetime import datetime, timezone as dt_timezone

from . import config
from .html import to_html
from .store import Store
from .telegram_client import TelegramBot


def _channel_name():
    name = (config.config.channel or "").strip()
    for prefix in ("https://t.me/", "http://t.me/", "t.me/"):
        if name.startswith(prefix):
            name = name[len(prefix):]
    return name.lstrip("@").split("/")[0]


def _post_url(message_id):
    name = _channel_name()
    return f"https://t.me/{name}/{message_id}" if name else ""


def _text_of(post):
    """Return (text, entities) preferring the text field, then the caption."""
    text = (post.get("text") or "").strip()
    if text:
        return text, post.get("entities")
    caption = (post.get("caption") or "").strip()
    return caption, post.get("caption_entities")


def _media_kind(post):
    if post.get("photo"):
        return "photo"
    if post.get("video") or post.get("animation") or post.get("video_note"):
        return "video"
    return None


def _photo_dims(post):
    photo = post.get("photo") or []
    if not photo:
        return None, None
    largest = photo[-1]
    return largest.get("width"), largest.get("height")


def _video_meta(post):
    doc = post.get("video") or post.get("animation") or post.get("video_note")
    if doc is None:
        return None, None, None
    return doc.get("duration"), doc.get("width"), doc.get("height")


def _file_id(post, kind):
    if kind == "photo":
        photo = post.get("photo") or []
        return photo[-1].get("file_id") if photo else None
    doc = post.get("video") or post.get("animation") or post.get("video_note")
    return doc.get("file_id") if doc else None


def _is_supported(post):
    text = (post.get("text") or post.get("caption") or "").strip()
    if post.get("poll"):
        # Polls are only mirrored when there is text or media to show.
        return bool(text) or _media_kind(post) is not None
    return bool(text) or _media_kind(post) is not None


def _group_posts(posts):
    """Split a post list into groups; media albums share media_group_id."""
    groups = []
    current = []
    last_gid = None
    for post in posts:
        gid = post.get("media_group_id")
        if gid is not None and current and gid == last_gid:
            current.append(post)
        else:
            if current:
                groups.append(current)
            current = [post]
        last_gid = gid
    if current:
        groups.append(current)
    return groups


class Syncer:
    def __init__(self):
        self.cfg = config.config
        self.store = Store(self.cfg.db_path)
        self.bot = TelegramBot()

    async def run_once(self):
        """Long-poll getUpdates once and persist any channel posts."""
        offset = int(self.store.get_state("update_offset", "0") or 0)
        data = await self.bot.get_updates(offset=offset, timeout=self.cfg.poll_timeout)

        new_offset = offset
        posts = []
        for update in data.get("result") or []:
            new_offset = max(new_offset, int(update["update_id"]) + 1)
            post = update.get("channel_post")
            if post:
                posts.append(post)

        for group in _group_posts(posts):
            await self._process_group(group)

        self.store.set_state("update_offset", new_offset)

    async def _process_group(self, group):
        if not any(_is_supported(p) for p in group):
            return
        post_id = max(p["message_id"] for p in group)
        if self.store.has_post(post_id):
            return

        text_msg = next(
            (p for p in group if (p.get("text") or p.get("caption") or "").strip()),
            None,
        )
        if text_msg:
            text, entities = _text_of(text_msg)
            html = to_html(text, entities)
        else:
            html = ""

        attachments = []
        for post in group:
            kind = _media_kind(post)
            if kind is None:
                continue
            file_id = _file_id(post, kind)
            if not file_id:
                continue
            base = f"{kind}_{post['message_id']}"
            path = await self.bot.download_file(file_id, self.cfg.media_dir, base)
            if not path:
                continue
            attachment = {
                "kind": kind,
                "url": os.path.relpath(path, self.cfg.media_dir),
                "original_url": _post_url(post["message_id"]),
            }
            if kind == "photo":
                width, height = _photo_dims(post)
                attachment["width"] = width
                attachment["height"] = height
            else:
                duration, width, height = _video_meta(post)
                attachment["duration"] = duration
                attachment["width"] = width
                attachment["height"] = height
            attachments.append(attachment)

        if not html and not attachments:
            return

        date_value = group[0].get("date")
        date_iso = (
            datetime.fromtimestamp(date_value, tz=dt_timezone.utc).isoformat()
            if date_value
            else ""
        )
        self.store.upsert_post(
            {
                "id": post_id,
                "channel": _channel_name(),
                "date": date_iso,
                "text_html": html,
                "attachments": attachments,
            }
        )
