"""Зарегистрировать legacy-файлы /media/documents/… как Wagtail-документы.

Команда ничего не удаляет и не копирует: она создаёт Document-записи, указывающие
на уже существующие файлы в MEDIA_ROOT, и заменяет прямые ссылки /media/documents/…
на document.url (/documents/<id>/<filename>/), который раздаётся Wagtail serve_view
с проверкой прав коллекции.
"""

from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand
from django.db import transaction

from home.models import HomeInfoFile, TournamentPage
from wagtail.documents.models import Document


class Command(BaseCommand):
    help = (
        "Заменяет прямые ссылки /media/documents/… на Wagtail document.url. "
        "Файлы не копируются и не удаляются."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Только показать планируемые изменения, ничего не записывать.",
        )

    def _resolve_document(self, rel, path, dry_run):
        """Возвращает (document, status). status: created/reused/create/missing."""
        doc = Document.objects.filter(file=rel).first()
        if doc is not None:
            return doc, "reused"
        if not path.exists():
            return None, "missing"
        if dry_run:
            return None, "create"
        with transaction.atomic():
            doc = Document(title=path.name, file=rel)
            doc.save()
        return doc, "created"

    def handle(self, *args, **options):
        dry_run = options["dry_run"]
        media_root = Path(settings.MEDIA_ROOT)

        created = 0
        reused = 0
        updated_pages = 0
        updated_files = 0
        missing = 0

        pages = TournamentPage.objects.filter(results_more_url__contains="/media/documents/")
        for page in pages:
            lines = page.results_more_url.splitlines()
            new_lines = []
            for line in lines:
                stripped = line.strip()
                if not stripped.startswith("/media/documents/"):
                    new_lines.append(line)
                    continue

                rel = stripped[len("/media/"):]
                if not rel or rel.startswith("/") or ".." in rel:
                    self.stderr.write(
                        self.style.WARNING(f"Пропущен подозрительный путь: {stripped}")
                    )
                    new_lines.append(line)
                    continue

                doc, status = self._resolve_document(rel, media_root / rel, dry_run)
                if doc is None:
                    if status == "missing":
                        self.stderr.write(
                            self.style.WARNING(f"Файл не найден: {media_root / rel}")
                        )
                        missing += 1
                    elif status == "create":
                        self.stdout.write(f"[dry-run] будет создан Document: {rel}")
                    new_lines.append(line)
                    continue

                if status == "created":
                    created += 1
                elif status == "reused":
                    reused += 1
                new_lines.append(doc.url)

            if new_lines == lines:
                continue

            updated_pages += 1
            if dry_run:
                self.stdout.write(
                    self.style.SUCCESS(
                        f"[dry-run] {page.title or page.pk}: {lines} -> {new_lines}"
                    )
                )
            else:
                page.results_more_url = "\n".join(new_lines)
                page.save()

        info_files = HomeInfoFile.objects.filter(url__startswith="/media/documents/")
        for item in info_files:
            value = (item.url or "").strip()
            rel = value[len("/media/"):]
            if not rel or rel.startswith("/") or ".." in rel:
                self.stderr.write(
                    self.style.WARNING(f"Пропущен подозрительный путь: {value}")
                )
                continue

            doc, status = self._resolve_document(rel, media_root / rel, dry_run)
            if doc is None:
                if status == "missing":
                    self.stderr.write(
                        self.style.WARNING(f"Файл не найден: {media_root / rel}")
                    )
                    missing += 1
                elif status == "create":
                    self.stdout.write(f"[dry-run] будет создан Document: {rel}")
                continue

            if status == "created":
                created += 1
            elif status == "reused":
                reused += 1

            updated_files += 1
            if dry_run:
                self.stdout.write(
                    self.style.SUCCESS(
                        f"[dry-run] HomeInfoFile {item.pk}: {value} -> {doc.url}"
                    )
                )
            else:
                item.document = doc
                item.url = ""
                item.save()

        self.stdout.write(
            self.style.SUCCESS(
                f"Создано документов: {created}; переиспользовано: {reused}; "
                f"обновлено страниц: {updated_pages}; обновлено ссылок главной: "
                f"{updated_files}; пропущено: {missing}."
            )
        )
