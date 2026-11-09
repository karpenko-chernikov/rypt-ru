import os

from .base import *

DEBUG = False


def _require(name):
    """Fail closed: production must not start without an explicit, valid value."""
    value = os.environ.get(name, "").strip()
    if not value:
        raise RuntimeError(
            f"{name} must be set in the environment for production startup"
        )
    return value


# Каталоги данных/медиа вынесены в writable-каталоги runtime-пользователя,
# статика собирается в каталог текущего релиза (читается Nginx).
# Значения можно переопределить через /etc/rypt.env.
DATABASES["default"]["NAME"] = os.environ.get(
    "DATABASE_PATH", "/var/lib/rypt/db/db.sqlite3"
)
MEDIA_ROOT = os.environ.get("MEDIA_ROOT", "/var/lib/rypt/media")
STATIC_ROOT = os.environ.get("STATIC_ROOT", "/srv/rypt/current/static")

SECRET_KEY = _require("DJANGO_SECRET_KEY")
if len(SECRET_KEY) < 50 or SECRET_KEY.startswith("django-insecure-"):
    raise RuntimeError(
        "DJANGO_SECRET_KEY is too weak for production; "
        "generate a long random key (e.g. secrets.token_urlsafe(50))"
    )

ALLOWED_HOSTS = [
    host.strip()
    for host in _require("ALLOWED_HOSTS").split(",")
    if host.strip()
]
if not ALLOWED_HOSTS or "*" in ALLOWED_HOSTS:
    raise RuntimeError(
        "ALLOWED_HOSTS must be an explicit, non-empty list and must not contain '*'"
    )

# Сайт работает только по HTTPS: доверять http-Origin не нужно.
CSRF_TRUSTED_ORIGINS = [f"https://{host}" for host in ALLOWED_HOSTS]

WAGTAILADMIN_BASE_URL = os.environ.get(
    "WAGTAILADMIN_BASE_URL",
    "https://rypt.folomin.com",
)

# Разрешить Wagtail-админку /redaktura/ вне DEBUG (например, на staging).
# По умолчанию выключено — на боевом сайте админка недоступна.
ENABLE_WAGTAIL_ADMIN = os.environ.get("ENABLE_WAGTAIL_ADMIN") == "1"

SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
# Хост берём из канонического заголовка Host, который выставляет Nginx.
# Клиентский X-Forwarded-Host игнорируем — иначе он подменяет get_host().
USE_X_FORWARDED_HOST = False
# IP клиента берём из X-Real-IP, который Nginx затирает значением $remote_addr.
TRUST_PROXY_HEADERS = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = "DENY"
SECURE_REFERRER_POLICY = "same-origin"
SECURE_HSTS_SECONDS = 31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_SSL_REDIRECT = True

# Content-Security-Policy (базовая; fonts.googleapis.com для кабинета)
SECURE_CROSS_ORIGIN_OPENER_POLICY = "same-origin"

# Логи в stderr → systemd/gunicorn → journalctl.
# Без этого django.request при DEBUG=False пишет только в mail_admins,
# и ошибки 500 не видны в journalctl.
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "verbose": {
            "format": "{levelname} {asctime} {module} {process:d} {thread:d} {message}",
            "style": "{",
        },
    },
    "handlers": {
        "console": {
            "level": "INFO",
            "class": "logging.StreamHandler",
            "formatter": "verbose",
        },
    },
    "root": {
        "handlers": ["console"],
        "level": "WARNING",
    },
    "loggers": {
        "django": {
            "handlers": ["console"],
            "level": "INFO",
            "propagate": False,
        },
        "django.request": {
            "handlers": ["console"],
            "level": "ERROR",
            "propagate": False,
        },
        "home": {
            "handlers": ["console"],
            "level": "WARNING",
            "propagate": False,
        },
    },
}

# Локальные override-файлы в production НЕ подключаются: wildcard-импорт
# мог бы молча переопределить DEBUG/SECRET_KEY/ALLOWED_HOSTS выше.
