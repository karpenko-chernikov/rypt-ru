"""Заполняет сезон 1997 по протоколу Оргкомитета и Жюри.

Источник: архив фонда, папка 29, листы 409–410.
Турнир: Екатеринбург, СУНЦ УрГУ, 14–20 марта 1997.
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
MORE_URL = "/static/docs/results/1997-protokol-1.jpg"

# Место — как на протоколе; в «Диплом» — степень по этому месту.
RANKING = [
    ("1", "СУНЦ МГУ", "I степени"),
    ("1", "СУНЦ УрГУ (1 сборная)", "I степени"),
    ("2", "Гимназия 9, Екатеринбург", "II степени"),
    ("3", "Школа 363, Москва", "III степени"),
    ("3", "СУНЦ УрГУ (2 сборная)", "III степени"),
    ("3", "Школа 130, Екатеринбург", "III степени"),
    ("4", "Улан-Удэ", "IV степени"),
    ("4", "Арзамас", "IV степени"),
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
    help = "Заполняет сезон 1997: протокол мест и сканы оригинала."

    def handle(self, *args, **options):
        page = TournamentPage.objects.filter(year=YEAR).first()
        if not page:
            self.stderr.write("Страницы 1997 нет.")
            return

        root = Path(__file__).resolve().parents[3]
        for name in ("1997-protokol-1.jpg", "1997-protokol-2.jpg"):
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
        add_rows(page, TournamentResultRow.KIND_RANKING, RANKING, 0)
        page.save_revision().publish()

        self.stdout.write(
            self.style.SUCCESS(
                f"1997: {CITY}, {START} — {END}, рейтинг {len(RANKING)}, "
                f"оригинал → {MORE_URL} (+ лист 2)"
            )
        )
