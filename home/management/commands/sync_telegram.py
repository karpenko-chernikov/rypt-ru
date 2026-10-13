"""Mirror Telegram channel posts into NewsPage via the reader service.

The site cannot reach Telegram directly (it runs in Russia). A separate reader
service on a foreign server exposes ``GET /api/posts`` and ``GET /media/<file>``
behind a bearer token. This command pulls from it with stdlib urllib only.

Usage:
    python manage.py sync_telegram

Environment:
    TG_READER_URL    https://tg-reader.example.com   (required)
    TG_READER_TOKEN  bearer token shared with reader  (optional if reader open)
    TG_CHANNEL       channel username, e.g. mychannel (optional; cached in state)

Значения берутся из окружения, а при его отсутствии — из файла ``.env``
в корне проекта (существующие переменные окружения не перезаписываются).
"""

import json
import os
import re
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone as dt_timezone
from io import BytesIO

from django.conf import settings
from django.core.files.base import ContentFile
from django.core.files.images import ImageFile
from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone

from home.models import NewsAttachment, NewsIndexPage, NewsPage, NewsSyncState
from wagtail.images.models import Image as WagtailImage

LIMIT = 100
MAX_ITERATIONS = 1000
_TAG_RE = re.compile(r"<[^>]+>")
_SPACE_RE = re.compile(r"\s+")


def _cfg(name, default=None):
    return os.environ.get(name, default)


def _load_env_file():
    """Загрузить KEY=VALUE из корневого .env, не трогая уже заданные переменные."""
    env_path = os.path.join(settings.BASE_DIR, ".env")
    if not os.path.isfile(env_path):
        return
    with open(env_path, encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, _, value = line.partition("=")
            key = key.strip()
            value = value.strip()
            if len(value) >= 2 and value[0] == value[-1] and value[0] in "\"'":
                value = value[1:-1]
            if key and key not in os.environ:
                os.environ[key] = value


def _to_date(iso):
    if not iso:
        return timezone.now().date()
    dt = datetime.fromisoformat(iso)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=dt_timezone.utc)
    return timezone.localtime(dt).date()


def _plain(text_html):
    return _SPACE_RE.sub(" ", _TAG_RE.sub(" ", text_html or "")).strip()


class Command(BaseCommand):
    help = "Подтягивает новые посты Telegram-канала через reader-сервис и создаёт NewsPage."

    def _headers(self, token):
        headers = {"Accept": "application/json"}
        if token:
            headers["Authorization"] = f"Bearer {token}"
        return headers

    def _fetch_json(self, url, token):
        req = urllib.request.Request(url, headers=self._headers(token))
        try:
            with urllib.request.urlopen(req, timeout=60) as resp:
                return json.loads(resp.read().decode("utf-8"))
        except urllib.error.HTTPError as exc:
            body = exc.read().decode("utf-8", "replace")[:300]
            raise CommandError(f"Reader ответил {exc.code}: {body}") from exc
        except urllib.error.URLError as exc:
            raise CommandError(f"Не удалось достучаться до reader: {exc.reason}.") from exc

    def _fetch_bytes(self, url, token):
        req = urllib.request.Request(url, headers=self._headers(token))
        try:
            with urllib.request.urlopen(req, timeout=120) as resp:
                return resp.read()
        except urllib.error.HTTPError as exc:
            raise CommandError(f"Не удалось скачать медиа ({exc.code}).") from exc
        except urllib.error.URLError as exc:
            raise CommandError(f"Не удалось скачать медиа: {exc.reason}.") from exc

    def handle(self, *args, **options):
        _load_env_file()
        base = (_cfg("TG_READER_URL") or "").rstrip("/")
        if not base:
            raise CommandError("Не задан TG_READER_URL.")

        token = _cfg("TG_READER_TOKEN")
        state = NewsSyncState.get()

        channel = _cfg("TG_CHANNEL")
        if channel:
            state.channel = channel
        if not state.channel:
            raise CommandError("Не задан TG_CHANNEL (и нет сохранённого канала).")

        news_index = NewsIndexPage.objects.live().first()
        if not news_index:
            raise CommandError("NewsIndexPage не найден — сначала seed_site.")

        cursor = state.last_message_id or 0
        created = 0
        iterations = 0

        while True:
            url = f"{base}/api/posts?after={cursor}&limit={LIMIT}"
            payload = self._fetch_json(url, token)
            posts = payload.get("posts") or []
            if not posts:
                break

            for post in posts:
                cursor = max(cursor, int(post["id"]))
                if NewsPage.objects.filter(
                    telegram_channel=state.channel,
                    telegram_message_id=post["id"],
                ).exists():
                    continue
                self._create_post(news_index, state.channel, post, base, token)
                created += 1

            iterations += 1
            if len(posts) < LIMIT or iterations >= MAX_ITERATIONS:
                break

        state.last_message_id = cursor
        state.save()
        self.stdout.write(
            self.style.SUCCESS(
                f"Синхронизация завершена: новых постов {created}, курсор {cursor}."
            )
        )

    def _create_post(self, news_index, channel, post, base, token):
        text_html = post.get("text_html") or ""
        title = _plain(text_html)[:160] or f"Новость от {_to_date(post.get('date')).strftime('%d.%m.%Y')}"

        page = NewsPage(
            title=title,
            date=_to_date(post.get("date")),
            body=text_html or "<p></p>",
            telegram_channel=channel,
            telegram_message_id=post["id"],
        )
        news_index.add_child(instance=page)

        for att in post.get("attachments") or []:
            self._create_attachment(page, att, base, token)

        page.save_revision().publish()

    def _create_attachment(self, page, att, base, token):
        url = att.get("url") or ""
        if not url:
            return
        name = os.path.basename(urllib.parse.urlparse(url).path) or "file"
        data = self._fetch_bytes(f"{base}/media/{urllib.parse.quote(url)}", token)
        original_url = att.get("original_url") or ""

        if att.get("kind") == "video":
            item = NewsAttachment(
                page=page,
                kind=NewsAttachment.KIND_VIDEO,
                original_url=original_url,
            )
            item.video_file.save(name, ContentFile(data), save=True)
        else:
            image = WagtailImage(title=name)
            image.file.save(name, ImageFile(BytesIO(data), name=name), save=True)
            NewsAttachment.objects.create(
                page=page,
                kind=NewsAttachment.KIND_PHOTO,
                image=image,
                original_url=original_url,
            )
