"""Хелперы безопасности кабинета редактора."""

from __future__ import annotations

import hashlib
import hmac
import secrets
from io import BytesIO
from urllib.parse import urlparse
from uuid import uuid4

from django.conf import settings
from django.core.cache import cache
from django.core.exceptions import ValidationError
from django.core.files.base import ContentFile
from django.core.files.uploadedfile import UploadedFile
from django.shortcuts import resolve_url
from django.utils.http import url_has_allowed_host_and_scheme

ALLOWED_IMAGE_CONTENT_TYPES = {
    "image/jpeg",
    "image/png",
    "image/webp",
    "image/gif",
}
ALLOWED_IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp", ".gif"}
MAX_IMAGE_BYTES = 8 * 1024 * 1024  # 8 MiB
MAX_IMAGE_PIXELS = 30_000_000  # 30 MP — защита от decompression-бомб
MAX_IMAGE_FRAMES = 1

_IMAGE_FORMAT_EXT = {
    "JPEG": ".jpg",
    "PNG": ".png",
    "WEBP": ".webp",
    "GIF": ".gif",
}
_IMAGE_SAVE_FORMATS = set(_IMAGE_FORMAT_EXT)


def client_ip(request) -> str:
    """IP клиента. За прокси (TRUST_PROXY_HEADERS) берём X-Real-IP:
    Nginx затирает этот заголовок значением $remote_addr."""
    if getattr(settings, "TRUST_PROXY_HEADERS", False):
        return request.META.get("HTTP_X_REAL_IP") or request.META.get("REMOTE_ADDR") or "unknown"
    return request.META.get("REMOTE_ADDR") or "unknown"


def throttle(key: str, *, limit: int, window: int = 3600) -> bool:
    """True если лимит превышен. Атомарные add/incr, чтобы гонки не
    завышали счётчик (LocMemCache потокобезопасен; общий он при одном worker)."""
    if cache.add(key, 1, window):
        return False
    try:
        n = cache.incr(key)
    except ValueError:
        # Ключ истёк между add и incr — начинаем окно заново.
        cache.set(key, 1, window)
        n = 1
    return n > limit


def safe_redirect_url(request, candidate: str | None, fallback: str = "editor:dashboard") -> str:
    """Защита от open redirect: только относительные URL того же хоста."""
    if candidate and url_has_allowed_host_and_scheme(
        url=candidate,
        allowed_hosts={request.get_host()},
        require_https=request.is_secure(),
    ):
        return candidate
    return resolve_url(fallback)


def constant_time_equals(a: str, b: str) -> bool:
    return hmac.compare_digest(a.encode("utf-8"), b.encode("utf-8"))


def invite_code() -> str:
    return secrets.token_urlsafe(24)


def hash_invite_code(code: str) -> str:
    """Храним только SHA-256 код приглашения; исходный код — только в URL."""
    return hashlib.sha256(code.encode("utf-8")).hexdigest()


def validate_public_http_url(value: str, *, field_name: str = "Ссылка") -> str:
    """Только http(s), без javascript:/data:/внутренних схем."""
    value = (value or "").strip()
    if not value:
        return ""
    parsed = urlparse(value)
    if parsed.scheme not in ("http", "https"):
        raise ValidationError(f"{field_name}: допустимы только http/https.")
    if not parsed.netloc:
        raise ValidationError(f"{field_name}: нужен полный URL с хостом.")
    if parsed.username or parsed.password:
        raise ValidationError(f"{field_name}: учётные данные в URL запрещены.")
    host = (parsed.hostname or "").lower()
    if host in {"localhost", "127.0.0.1", "::1"} or host.endswith(".local"):
        raise ValidationError(f"{field_name}: локальные адреса запрещены.")
    return value


def _normalize_image(upload):
    """Полностью декодирует изображение и возвращает безопасную перекодированную копию."""
    try:
        from PIL import Image as PILImage
        from PIL import ImageOps
    except ImportError as exc:
        raise ValidationError("Сервер не может проверить изображение.") from exc

    upload.seek(0)
    raw = upload.read()
    if len(raw) > MAX_IMAGE_BYTES:
        raise ValidationError("Файл больше 8 МБ.")

    try:
        with PILImage.open(BytesIO(raw)) as probe:
            probe.verify()
    except ValidationError:
        raise
    except Exception as exc:
        raise ValidationError("Файл повреждён или это не изображение.") from exc

    try:
        with PILImage.open(BytesIO(raw)) as img:
            fmt = img.format or ""
            if fmt not in _IMAGE_SAVE_FORMATS:
                raise ValidationError("Формат изображения не поддерживается.")
            frames = getattr(img, "n_frames", 1)
            if frames > MAX_IMAGE_FRAMES:
                raise ValidationError("Анимированные изображения не поддерживаются.")
            width, height = img.size
            if width * height > MAX_IMAGE_PIXELS:
                raise ValidationError("Изображение слишком большое: превышен лимит пикселей.")

            img = ImageOps.exif_transpose(img)
            if fmt == "JPEG":
                img = img.convert("RGB")
                save_fmt = "JPEG"
                save_kwargs = {"quality": 92, "optimize": True}
            elif fmt == "PNG":
                if img.mode not in ("RGB", "RGBA", "P", "L", "LA", "1"):
                    img = img.convert("RGBA")
                save_fmt = "PNG"
                save_kwargs = {"optimize": True}
            elif fmt == "WEBP":
                if img.mode not in ("RGB", "RGBA"):
                    img = img.convert("RGBA")
                save_fmt = "WEBP"
                save_kwargs = {"quality": 90, "method": 6}
            else:  # GIF — принимаем только одиночный кадр и перекодируем в PNG
                img = img.convert("RGBA")
                save_fmt = "PNG"
                save_kwargs = {"optimize": True}

            buf = BytesIO()
            img.save(buf, format=save_fmt, **save_kwargs)
            buf.seek(0)
            if buf.getbuffer().nbytes > MAX_IMAGE_BYTES:
                raise ValidationError("Файл больше 8 МБ после перекодирования.")

            name = f"{uuid4().hex}{_IMAGE_FORMAT_EXT[save_fmt]}"
            return ContentFile(buf.read(), name=name)
    except ValidationError:
        raise
    except Exception as exc:
        raise ValidationError("Файл повреждён или это не изображение.") from exc


def validate_editor_image(upload: UploadedFile | None):
    """Проверка картинки и возврат безопасной перекодированной копии."""
    if upload is None:
        return None
    name = (getattr(upload, "name", "") or "").lower()
    ext = ""
    if "." in name:
        ext = "." + name.rsplit(".", 1)[-1]
    if ext not in ALLOWED_IMAGE_EXTENSIONS:
        raise ValidationError(
            "Допустимы только JPEG, PNG, WebP, GIF. SVG и другие типы запрещены."
        )
    content_type = (getattr(upload, "content_type", "") or "").lower()
    if content_type and content_type not in ALLOWED_IMAGE_CONTENT_TYPES:
        raise ValidationError("Недопустимый тип файла изображения.")
    size = getattr(upload, "size", None)
    if size is not None and size > MAX_IMAGE_BYTES:
        raise ValidationError("Файл больше 8 МБ.")
    return _normalize_image(upload)
