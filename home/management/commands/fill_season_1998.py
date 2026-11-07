"""Заполняет сезон 1998 по протоколу XX Всероссийского ТЮФ.

Источник: архив фонда, папка 33, лист 294.
Турнир: Санкт-Петербург, АГ СПбГУ, 21–25 марта 1998.
"""

from datetime import date
from pathlib import Path

from django.core.management.base import BaseCommand

from home.models import TournamentPage, TournamentResultRow

YEAR = 1998
CITY = "Санкт-Петербург, АГ СПбГУ"
START = date(1998, 3, 21)
END = date(1998, 3, 25)
MORE_LABEL = "Оригинал (архив фонда, папка 33, лист 294)"
MORE_URL = "/static/docs/results/1998-protokol.jpg"

# Общий зачёт / итоговый рейтинг (колонка на протоколе); баллы финала — отдельно.
RANKING = [
    ("1", "СУНЦ УрГУ I", "17.0"),
    ("2", "Москва 363", "15.0"),
    ("3", "СУНЦ УрГУ II", "14.0"),
    ("3", "СУНЦ МГУ", "13.0"),
    ("5", "АГ СПбГУ 1", "10.0"),
    ("6", "АГ СПбГУ 2", "9.0"),
    ("6", "Саров", "9.0"),
    ("8", "Новгород «Эврика»", "8.0"),
    ("8", "Арзамас", "8.0"),
    ("10", "Екатеринбург 130", "7.0"),
    ("11", "Пушкин 406", "6.0"),
    ("12", "Воткинск", "2.0"),
]

FINAL = [
    ("I", "СУНЦ УрГУ I", "293"),
    ("II", "Москва 363", "285"),
    ("III", "СУНЦ УрГУ II", "267"),
    ("III", "СУНЦ МГУ", "262"),
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
    help = "Заполняет сезон 1998: общий зачёт, финал и скан оригинала."

    def handle(self, *args, **options):
        page = TournamentPage.objects.filter(year=YEAR).first()
        if not page:
            self.stderr.write("Страницы 1998 нет.")
            return

        scan = Path(__file__).resolve().parents[3] / "rypt/static/docs/results/1998-protokol.jpg"
        if not scan.exists():
            self.stderr.write(f"Нет скана: {scan}")
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
                f"1998: {CITY}, {START} — {END}, рейтинг {len(RANKING)}, "
                f"финал {len(FINAL)}, оригинал → {MORE_URL}"
            )
        )
