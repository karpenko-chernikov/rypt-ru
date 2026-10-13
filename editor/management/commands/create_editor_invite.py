"""Создать одноразовое приглашение в кабинет редактора."""

from datetime import timedelta

from django.core.management.base import BaseCommand
from django.utils import timezone

from editor.authz import ensure_editors_group
from editor.models import EditorInvite
from editor.security import invite_code


class Command(BaseCommand):
    help = "Создать одноразовую ссылку регистрации редактора"

    def add_arguments(self, parser):
        parser.add_argument(
            "--days",
            type=int,
            default=7,
            help="Срок в днях (0 = бессрочно, иначе 1…365)",
        )
        parser.add_argument("--note", default="", help="Заметка")
        parser.add_argument(
            "--base-url",
            default="https://rypt.folomin.com",
            help="Базовый URL сайта для печати полной ссылки",
        )

    def handle(self, *args, **options):
        ensure_editors_group()
        days = options["days"]
        if days < 0 or days > 365:
            self.stderr.write(" --days: 0 (бессрочно) или 1…365")
            return
        expires_at = None if days == 0 else timezone.now() + timedelta(days=days)
        invite = EditorInvite.objects.create(
            code=invite_code(),
            note=options["note"],
            expires_at=expires_at,
        )
        url = f"{options['base_url'].rstrip('/')}/dlya-redaktorov/priglashenie/{invite.code}/"
        self.stdout.write(self.style.SUCCESS(url))
        if expires_at is None:
            self.stdout.write("Истекает: бессрочно (до использования или отзыва)")
        else:
            self.stdout.write(f"Истекает: {invite.expires_at:%Y-%m-%d %H:%M %Z}")
