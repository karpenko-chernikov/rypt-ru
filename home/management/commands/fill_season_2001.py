"""Заполняет сезон 2001 по листу итогов отборочных боёв.

Источник: архив фонда, папка 26, лист 058.
XXIII Российский ТЮФ; на листе — итоги I–IV отборочных боёв.
Площадка на скане не подписана; по эмблеме АГ и составу — Санкт-Петербург, АГ СПбГУ.
Финала на листе нет.
"""

from pathlib import Path

from django.core.management.base import BaseCommand

from home.models import TournamentPage, TournamentResultRow

YEAR = 2001
CITY = "Санкт-Петербург, АГ СПбГУ"
MORE_LABEL = "Оригинал (архив фонда, папка 26, лист 058)"
MORE_URL = "/static/docs/results/2001-otborochnye.jpg"
SCAN = "2001-otborochnye.jpg"

# Итоги I–IV отборочных боёв: место по баллам; в сумме — баллы с листа.
RANKING = [
    ("1", "СУНЦ УрГУ", "147.33"),
    ("2", "АГ СПбГУ", "147.25"),
    ("3", "Москва 363", "139.5"),
    ("4", "Великие Луки", "138.0"),
    ("5", "Арзамас", "127.67"),
    ("6", "Качканар", "109.25"),
    ("7", "Новодвинск", "94.55"),
    ("8", "Москва 465", "90.9"),
]


def add_rows(page, kind, rows, order):
    for place, team, points in rows:
        TournamentResultRow.objects.create(
            page=page,
            kind=kind,
            place=place,
            team=team,
            city="",
            points=points,
            sort_order=order,
        )
        order += 1
    return order


class Command(BaseCommand):
    help = "Заполняет сезон 2001: отборочные и скан оригинала."

    def handle(self, *args, **options):
        page = TournamentPage.objects.filter(year=YEAR).first()
        if not page:
            self.stderr.write("Страницы 2001 нет.")
            return

        root = Path(__file__).resolve().parents[3]
        path = root / "rypt/static/docs/results" / SCAN
        if not path.exists():
            self.stderr.write(f"Нет скана: {path}")
            return

        page.city = CITY
        page.results_more_url = MORE_URL
        page.results_more_label = MORE_LABEL
        page.save()

        page.ranking.all().delete()
        add_rows(page, TournamentResultRow.KIND_RANKING, RANKING, 0)
        page.save_revision().publish()

        self.stdout.write(
            self.style.SUCCESS(
                f"2001: {CITY}, рейтинг {len(RANKING)}, оригинал → {MORE_URL}"
            )
        )
