"""Санитайзер ограниченного HTML по allowlist.

Используется для поля «О турнире» (RegionalTournament.info), которое рендерится
на клиенте через innerHTML. Пропускаются только безопасные теги форматирования,
без скриптов, обработчиков событий и опасных URL-схем.
"""

from __future__ import annotations

import nh3

# Разрешённые теги: только базовое форматирование, списки и ссылки.
ALLOWED_TAGS = {"p", "br", "strong", "em", "b", "i", "a", "ol", "ul", "li"}

# Атрибуты разрешены только у ссылок. rel не входит в allowlist: его
# принудительно проставляет nh3 через link_rel="noopener noreferrer".
ALLOWED_ATTRIBUTES = {"a": {"href", "title"}}

# Разрешённые схемы URL; относительные ссылки (без схемы) nh3 пропускает как есть.
ALLOWED_URL_SCHEMES = {"http", "https", "mailto"}


def sanitize_limited_html(value: str) -> str:
    """Возвращает безопасный HTML: только разрешённые теги, атрибуты и схемы URL."""
    if not value:
        return ""
    return nh3.clean(
        value,
        tags=ALLOWED_TAGS,
        attributes=ALLOWED_ATTRIBUTES,
        url_schemes=ALLOWED_URL_SCHEMES,
        link_rel="noopener noreferrer",
    )
