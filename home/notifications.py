"""Уведомления администраторов о новых объявлениях на «Доске заявок».

Отправка идёт через Telegram reader-сервис (см. reader/README.md), потому что
сайт работает из России и напрямую в Telegram Bot API ходить не может.
Уведомления — best-effort: любая сетевая ошибка логируется и не должна
ломать создание объявления.
"""

import json
import logging
import urllib.error
import urllib.request

from django.conf import settings
from django.utils import timezone

logger = logging.getLogger("home.training_board")


def build_training_board_message(card):
    """Текст сообщения для админ-чата: вся публичная информация о заявке."""
    lines = [
        "Новая заявка на тренировочный бой",
        "",
        f"Команда: {card.team_name}",
        f"Даты: {card.dates}",
        f"Город: {card.city}",
    ]
    if card.tasks:
        lines.append(f"Задания: {card.tasks}")
    if card.comments:
        lines.append(f"Комментарии: {card.comments}")
    lines.append(f"Контакты: {card.contact}")

    created_at = card.created_at
    if created_at is not None:
        local_created = timezone.localtime(created_at)
        lines.append(f"Создано: {local_created.strftime('%d.%m.%Y %H:%M')}")
    return "\n".join(lines)


def notify_training_board_card(card):
    """Отправить сообщение о новой заявке через reader-сервис.

    Возвращает True при успешной отправке, False — если уведомления
    выключены или отправка не удалась. Исключения наружу не пробрасываются.
    """
    base_url = (getattr(settings, "TG_READER_URL", "") or "").strip().rstrip("/")
    token = (getattr(settings, "TG_READER_TOKEN", "") or "").strip()
    if not base_url or not token:
        logger.info(
            "Telegram notification skipped for card %s: TG_READER_URL/TG_READER_TOKEN are not configured",
            card.pk,
        )
        return False

    payload = json.dumps({"text": build_training_board_message(card)}).encode("utf-8")
    request = urllib.request.Request(
        f"{base_url}/api/notify",
        data=payload,
        method="POST",
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        },
    )

    timeout = getattr(settings, "TG_NOTIFY_TIMEOUT", 10)
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            response.read()
    except urllib.error.URLError as exc:
        logger.warning(
            "Training-board notification failed for card %s: %s",
            card.pk,
            exc,
        )
        return False
    except TimeoutError as exc:
        logger.warning(
            "Training-board notification timed out for card %s: %s",
            card.pk,
            exc,
        )
        return False
    except Exception:
        logger.exception(
            "Unexpected error sending training-board notification for card %s",
            card.pk,
        )
        return False

    logger.info("Training-board notification sent for card %s", card.pk)
    return True
