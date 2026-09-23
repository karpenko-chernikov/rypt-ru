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
        parser.add_argument("--days", type=int, default=7, help="Срок действия в днях")
        parser.add_argument("--note", default="", help="Заметка")
        parser.add_argument(
            "--base-url",
            default="https://rypt.folomin.com",
            help="Базовый URL сайта для печати полной ссылки",
        )

    def handle(self, *args, **options):
        ensure_editors_group()
        days = max(1, min(30, options["days"]))
        invite = EditorInvite.objects.create(
            code=invite_code(),
            note=options["note"],
            expires_at=timezone.now() + timedelta(days=days),
        )
        url = f"{options['base_url'].rstrip('/')}/dlya-redaktorov/priglashenie/{invite.code}/"
        self.stdout.write(self.style.SUCCESS(url))
        self.stdout.write(f"Истекает: {invite.expires_at:%Y-%m-%d %H:%M %Z}")
