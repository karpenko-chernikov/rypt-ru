"""Права кабинета: группа Editors, без is_staff / Wagtail / django-admin."""

from __future__ import annotations

from django.contrib.auth.models import Group

EDITORS_GROUP = "Editors"


def ensure_editors_group() -> Group:
    group, _ = Group.objects.get_or_create(name=EDITORS_GROUP)
    return group


def user_is_editor(user) -> bool:
    if not getattr(user, "is_authenticated", False):
        return False
    if user.is_superuser:
        return True
    return user.groups.filter(name=EDITORS_GROUP).exists()


def grant_editor(user) -> None:
    """Выдать доступ в кабинет без прав Wagtail/django-admin."""
    group = ensure_editors_group()
    user.groups.add(group)
    if not user.is_superuser:
        user.is_staff = False
        user.is_superuser = False
        user.save(update_fields=["is_staff", "is_superuser"])
