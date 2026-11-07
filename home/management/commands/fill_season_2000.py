"""Заполняет сезон 2000 по протоколам XXII Российского ТЮФ.

Источники (архив фонда, папка 26):
- лист 092 — итоги трёх отборочных боёв;
- лист 087 — полуфинал;
- лист 088 — сводные итоги (в т.ч. финал).
Турнир: Екатеринбург; на листах штамп 18.03.00.
"""

from datetime import date
from pathlib import Path

from django.core.management.base import BaseCommand

from home.models import TournamentPage, TournamentResultRow

YEAR = 2000
CITY = "Екатеринбург"
START = date(2000, 3, 18)
END = date(2000, 3, 18)
MORE_LABEL = "Оригинал (архив фонда, папка 26, листы 092, 087, 088)"
MORE_URL = (
    "/static/docs/results/2000-otborochnye.jpg\n"
    "/static/docs/results/2000-polufinal.jpg\n"
    "/static/docs/results/2000-itogi.jpg"
)
SCANS = (
    "2000-otborochnye.jpg",
    "2000-polufinal.jpg",
    "2000-itogi.jpg",
)

# Отборочные: место по суммарному рейтингу; в сумме — рейтинг.
RANKING = [
    ("1", "СУНЦ УрГУ 1", "14"),
    ("2", "Екатеринбург, шк. 9 (1)", "12"),
    ("3", "Великие Луки", "11"),
    ("3", "Саров", "11"),
    ("5", "Екатеринбург, шк. 130", "10"),
    ("5", "Екатеринбург, шк. 9 (2)", "10"),
    ("7", "Арзамас, лицей", "9.5"),
    ("8", "СУНЦ УрГУ 2", "9"),
    ("9", "Москва, шк. 363", "8.5"),
    ("10", "АГ СПбГУ", "8"),
    ("11", "Качканар, шк. 7", "7.5"),
    ("12", "СУНЦ МГУ", "6.5"),
    ("13", "СУНЦ НГУ", "6"),
    ("14", "Пушкин, гимн. 406", "5"),
    ("15", "Н. Тагил, шк. 61", "4"),
    ("16", "Н. Тагил, шк. 86", "3"),
]

# Финал: место по рейтингу боя (5 / 3 / 2.5); баллы — SP финала.
FINAL = [
    ("I", "СУНЦ УрГУ 1", "301"),
    ("II", "Великие Луки", "285"),
    ("III", "Екатеринбург, шк. 9 (1)", "284"),
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
    help = "Заполняет сезон 2000: отборочные, финал и сканы оригинала."

    def handle(self, *args, **options):
        page = TournamentPage.objects.filter(year=YEAR).first()
        if not page:
            self.stderr.write("Страницы 2000 нет.")
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
                f"2000: {CITY}, {START} — {END}, рейтинг {len(RANKING)}, "
                f"финал {len(FINAL)}, оригинал → {len(SCANS)} листа"
            )
        )
