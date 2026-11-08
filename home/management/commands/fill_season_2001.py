"""Заполняет сезон 2001 по протоколу XXIII Российского ТЮФ.

Источники (архив фонда, папка 26):
- лист 058 — итоги I–IV отборочных боёв;
- лист 059 — протокол: финал, общий зачёт, личный рейтинг.
Турнир: Санкт-Петербург, АГ СПбГУ, 1–4 апреля 2001.
"""

from datetime import date
from pathlib import Path

from django.core.management.base import BaseCommand

from home.models import TournamentPage, TournamentResultRow

YEAR = 2001
CITY = "Санкт-Петербург, АГ СПбГУ"
START = date(2001, 4, 1)
END = date(2001, 4, 4)
MORE_LABEL = "Оригинал (архив фонда, папка 26, листы 058–059)"
MORE_URL = (
    "/static/docs/results/2001-otborochnye.jpg\n"
    "/static/docs/results/2001-protokol.jpg"
)
SCANS = (
    "2001-otborochnye.jpg",
    "2001-protokol.jpg",
)

# Итоги I–IV отборочных боёв: место по баллам; в сумме — баллы с листа 058.
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

# Итоги финала (лист 059).
FINAL = [
    ("I", "СУНЦ УрГУ", "42.0"),
    ("II", "АГ СПбГУ", "39.8"),
    ("III", "Москва 363", "38.4"),
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
    help = "Заполняет сезон 2001: отборочные, финал и сканы оригинала."

    def handle(self, *args, **options):
        page = TournamentPage.objects.filter(year=YEAR).first()
        if not page:
            self.stderr.write("Страницы 2001 нет.")
            return

        root = Path(__file__).resolve().parents[3]
        for name in SCANS:
            path = root / "rypt/static/docs/results" / name
            if not path.exists():
                self.stderr.write(f"Нет скана: {path}")
                return

        page.city = CITY
        page.date_start = START
        page.date_end = END
        page.results_more_url = MORE_URL
        page.results_more_label = MORE_LABEL
        page.save()

        page.ranking.all().delete()
        order = 0
        order = add_rows(page, TournamentResultRow.KIND_RANKING, RANKING, order)
        add_rows(page, TournamentResultRow.KIND_FINAL, FINAL, order)
        page.save_revision().publish()

        self.stdout.write(
            self.style.SUCCESS(
                f"2001: {CITY}, {START} — {END}, рейтинг {len(RANKING)}, "
                f"финал {len(FINAL)}, оригинал → {len(SCANS)} листа"
            )
        )
