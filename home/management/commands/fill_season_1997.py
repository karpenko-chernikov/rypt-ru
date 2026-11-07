"""Заполняет сезон 1997 по протоколу Оргкомитета и Жюри + IYPT.

Источник РосТЮФ: архив фонда, папка 29, листы 409–410.
Турнир: Екатеринбург, СУНЦ УрГУ, 14–20 марта 1997.
X IYPT (Хеб, Чехия): сканы TEAM COMPETITION и SEMIFINALS RESULTS.
"""

from datetime import date
from pathlib import Path

from django.core.management.base import BaseCommand

from home.models import TournamentPage, TournamentResultRow

YEAR = 1997
CITY = "Екатеринбург, СУНЦ УрГУ"
START = date(1997, 3, 14)
END = date(1997, 3, 20)
MORE_LABEL = "Оригинал (архив фонда, папка 29, листы 409–410)"
MORE_URL = (
    "/static/docs/results/1997-protokol-1.jpg\n"
    "/static/docs/results/1997-protokol-2.jpg"
)
IYPT_MORE_LABEL = "Оригинал IYPT"
IYPT_MORE_URL = (
    "/static/docs/results/1997-iypt-team-competition.jpg\n"
    "/static/docs/results/1997-iypt-semifinals.jpg"
)

IYPT_TEAM = """На X IYPT (1–7 июня 1997, Хеб, Чехия) выступали три российские команды: Москва (СУНЦ МГУ), Екатеринбург и Урал.

По итогам отборочных боёв: Екатеринбург — 8-е, Москва — 9-е, Урал — 12-е место."""

# Место — как на протоколе («Место 1» … «Место 4»). Баллов/дипломов на скане нет.
RANKING = [
    ("1", "СУНЦ МГУ", ""),
    ("1", "СУНЦ УрГУ (1 сборная)", ""),
    ("2", "Гимназия 9, Екатеринбург", ""),
    ("3", "Школа 363, Москва", ""),
    ("3", "СУНЦ УрГУ (2 сборная)", ""),
    ("3", "Школа 130, Екатеринбург", ""),
    ("4", "Улан-Удэ", ""),
    ("4", "Арзамас", ""),
]

# TEAM COMPETITION: место; в сумме — Total SP.
IYPT_RANKING = [
    ("1", "Украина — Одесса", "860"),
    ("2", "Грузия", "843"),
    ("3", "Белоруссия", "809"),
    ("4", "Украина — Львов", "807"),
    ("5", "Чехия — Прага", "824"),
    ("6", "Польша", "819"),
    ("7", "Венгрия", "846"),
    ("8", "Россия — Екатеринбург", "806"),
    ("9", "Россия — Москва", "756"),
    ("10", "Германия", "785"),
    ("11", "Словакия", "780"),
    ("12", "Россия — Урал", "755"),
    ("13", "Узбекистан", "714"),
    ("14", "Швеция", "705"),
    ("15", "Чехия — Опава", "656"),
]

# THE SEMIFINALS RESULTS: место; в сумме — Total SP.
IYPT_FINAL = [
    ("1", "Чехия — Прага", "290"),
    ("2", "Венгрия", "280"),
    ("3", "Белоруссия", "267"),
    ("4", "Россия — Москва", "262"),
    ("5", "Украина — Одесса", "273"),
    ("6", "Польша", "270"),
    ("7", "Грузия", "267"),
    ("8", "Украина — Львов", "258"),
    ("9", "Россия — Екатеринбург", "256"),
]

SCANS = (
    "1997-protokol-1.jpg",
    "1997-protokol-2.jpg",
    "1997-iypt-team-competition.jpg",
    "1997-iypt-semifinals.jpg",
)


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
    help = "Заполняет сезон 1997: протокол мест, IYPT и сканы оригинала."

    def handle(self, *args, **options):
        page = TournamentPage.objects.filter(year=YEAR).first()
        if not page:
            self.stderr.write("Страницы 1997 нет.")
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
        page.iypt_team = IYPT_TEAM
        page.iypt_more_url = IYPT_MORE_URL
        page.iypt_more_label = IYPT_MORE_LABEL
        page.save()

        page.ranking.all().delete()
        order = 0
        order = add_rows(page, TournamentResultRow.KIND_RANKING, RANKING, order)
        order = add_rows(page, TournamentResultRow.KIND_IYPT_RANKING, IYPT_RANKING, order)
        add_rows(page, TournamentResultRow.KIND_IYPT_FINAL, IYPT_FINAL, order)
        page.save_revision().publish()

        self.stdout.write(
            self.style.SUCCESS(
                f"1997: {CITY}, {START} — {END}, рейтинг {len(RANKING)}, "
                f"IYPT {len(IYPT_RANKING)}/{len(IYPT_FINAL)}, оригинал IYPT → 2 листа"
            )
        )
