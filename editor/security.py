"""Хелперы безопасности кабинета редактора."""

from __future__ import annotations

import hmac
import secrets
from io import BytesIO
from urllib.parse import urlparse

from django.conf import settings
from django.core.cache import cache
from django.core.exceptions import ValidationError
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


def client_ip(request) -> str:
    """IP клиента. X-Forwarded-For доверяем только за прокси (USE_X_FORWARDED_HOST)."""
    if getattr(settings, "USE_X_FORWARDED_HOST", False):
        forwarded = request.META.get("HTTP_X_FORWARDED_FOR", "")
        if forwarded:
            return forwarded.split(",")[0].strip() or "unknown"
    return request.META.get("REMOTE_ADDR") or "unknown"


def throttle(key: str, *, limit: int, window: int = 3600) -> bool:
    """True если лимит превышен. Счётчик в cache (в проде — общий бэкенд)."""
    n = cache.get(key, 0)
    if n >= limit:
        return True
    cache.set(key, n + 1, window)
    return False


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


def validate_editor_image(upload: UploadedFile | None) -> UploadedFile | None:
    """Проверка картинки: размер, расширение, content-type, декод Pillow."""
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
    try:
        from PIL import Image as PILImage
    except ImportError as exc:
        raise ValidationError("Сервер не может проверить изображение.") from exc
    try:
        upload.seek(0)
        raw = upload.read()
        if len(raw) > MAX_IMAGE_BYTES:
            raise ValidationError("Файл больше 8 МБ.")
        with PILImage.open(BytesIO(raw)) as img:
            img.verify()
        upload.seek(0)
        with PILImage.open(upload) as img2:
            img2.load()
            if img2.format not in {"JPEG", "PNG", "WEBP", "GIF"}:
                raise ValidationError("Формат изображения не поддерживается.")
        upload.seek(0)
    except ValidationError:
        raise
    except Exception as exc:
        raise ValidationError("Файл повреждён или это не изображение.") from exc
    return upload
