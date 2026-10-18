import os

from .base import *

DEBUG = False

SECRET_KEY = os.environ["DJANGO_SECRET_KEY"]

ALLOWED_HOSTS = [
    host.strip()
    for host in os.environ.get(
        "ALLOWED_HOSTS",
        "rypt.folomin.com",
    ).split(",")
    if host.strip()
]

CSRF_TRUSTED_ORIGINS = []
for host in ALLOWED_HOSTS:
    CSRF_TRUSTED_ORIGINS.append(f"https://{host}")
    CSRF_TRUSTED_ORIGINS.append(f"http://{host}")

WAGTAILADMIN_BASE_URL = os.environ.get(
    "WAGTAILADMIN_BASE_URL",
    "https://rypt.folomin.com",
)

# Разрешить Wagtail-админку /redaktura/ вне DEBUG (например, на staging).
# По умолчанию выключено — на боевом сайте админка недоступна.
ENABLE_WAGTAIL_ADMIN = os.environ.get("ENABLE_WAGTAIL_ADMIN") == "1"

SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
USE_X_FORWARDED_HOST = True
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

try:
    from .local import *
except ImportError:
    pass
