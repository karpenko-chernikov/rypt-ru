"""Общие операции кабинета: журнал, публикация, смена текущего сезона."""

from __future__ import annotations

from django.db import transaction

from editor.models import EditorChangeLog
from home.models import (
    HomePage,
    TournamentIndexPage,
    TournamentPage,
    season_title,
    year_to_roman,
)


def log_change(
    *,
    user,
    action: str,
    summary: str,
    object_type: str = "season",
    object_id: int | None = None,
    object_label: str = "",
    tab: str = EditorChangeLog.TAB_OTHER,
    payload: dict | None = None,
):
    try:
        EditorChangeLog.objects.create(
            user=user if getattr(user, "is_authenticated", False) else None,
            action=action,
            summary=summary[:400],
            object_type=object_type,
            object_id=object_id,
            object_label=object_label[:200],
            tab=tab,
            payload=payload or {},
        )
    except Exception:
        # Журнал никогда не должен ломать сохранение контента.
        pass


def publish_page(page: TournamentPage, user=None, summary: str | None = None, tab=EditorChangeLog.TAB_META):
    # Права Wagtail на страницы не используем: доступ в кабинет уже по is_staff.
    revision = page.save_revision(user=user)
    revision.publish(user=user, skip_permission_checks=True)
    if user is not None:
        log_change(
            user=user,
            action=EditorChangeLog.ACTION_PUBLISH,
            summary=summary or f"Опубликован сезон {page.display_title}",
            object_id=page.pk,
            object_label=page.display_title,
            tab=tab,
        )


def tournament_index() -> TournamentIndexPage:
    home = HomePage.objects.first()
    if not home:
        raise RuntimeError("Нет главной страницы. Сначала seed_site.")
    index = TournamentIndexPage.objects.child_of(home).first()
    if not index:
        raise RuntimeError("Нет раздела турниров. Сначала seed_site.")
    return index


@transaction.atomic
def create_season(year: int, *, make_current: bool = False, user=None) -> TournamentPage:
    index = tournament_index()
    if TournamentPage.objects.child_of(index).filter(slug=str(year)).exists():
        raise ValueError(f"Сезон {year} уже есть.")
    roman = year_to_roman(year)
    title = season_title(year, roman)
    if make_current:
        TournamentPage.objects.filter(is_current=True).update(is_current=False)
    page = TournamentPage(
        title=title,
        slug=str(year),
        year=year,
        roman=roman,
        is_current=make_current,
    )
    index.add_child(instance=page)
    publish_page(page, user=user, summary=f"Создан сезон {title}")
    log_change(
        user=user,
        action=EditorChangeLog.ACTION_CREATE,
        summary=f"Создан сезон {title}",
        object_id=page.pk,
        object_label=title,
        tab=EditorChangeLog.TAB_META,
        payload={"year": year, "make_current": make_current},
    )
    if make_current:
        log_change(
            user=user,
            action=EditorChangeLog.ACTION_MAKE_CURRENT,
            summary=f"Назначен текущим: {title}",
            object_id=page.pk,
            object_label=title,
            tab=EditorChangeLog.TAB_META,
        )
    return page


@transaction.atomic
def archive_current(*, user=None) -> TournamentPage | None:
    page = TournamentPage.objects.filter(is_current=True).first()
    if not page:
        return None
    page.is_current = False
    page.save()
    publish_page(page, user=user, summary=f"Сезон {page.display_title} перенесён в прошедшие")
    log_change(
        user=user,
        action=EditorChangeLog.ACTION_ARCHIVE_CURRENT,
        summary=f"В прошедшие: {page.display_title}",
        object_id=page.pk,
        object_label=page.display_title,
        tab=EditorChangeLog.TAB_META,
    )
    return page


@transaction.atomic
def make_current(page: TournamentPage, *, user=None) -> TournamentPage:
    TournamentPage.objects.filter(is_current=True).exclude(pk=page.pk).update(is_current=False)
    page.is_current = True
    page.save()
    publish_page(page, user=user, summary=f"Сезон {page.display_title} сделан текущим")
    log_change(
        user=user,
        action=EditorChangeLog.ACTION_MAKE_CURRENT,
        summary=f"Сделан текущим: {page.display_title}",
        object_id=page.pk,
        object_label=page.display_title,
        tab=EditorChangeLog.TAB_META,
    )
    return page


@transaction.atomic
def open_new_season(year: int, *, user=None) -> TournamentPage:
    """Создать сезон year, снять текущий, назначить новый текущим."""
    archive_current(user=user)
    return create_season(year, make_current=True, user=user)
