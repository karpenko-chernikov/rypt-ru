"""Заполняет сезон 2002 по результатам отборочных боёв.

Источник: архив фонда, папка 63, лист 039.
XXIV Российский ТЮФ: Саров, 17–22 марта 2002
(даты — «Физика» № 40 / 2002; на листе — «Саров 2002»).
Финала на листе нет.
"""

from datetime import date
from pathlib import Path

from django.core.management.base import BaseCommand

from home.models import TournamentPage, TournamentResultRow

YEAR = 2002
CITY = "Саров"
START = date(2002, 3, 17)
END = date(2002, 3, 22)
MORE_LABEL = "Оригинал (архив фонда, папка 63, лист 039)"
MORE_URL = "/static/docs/results/2002-otborochnye.jpg"
SCAN = "2002-otborochnye.jpg"

IYPT_MORE_URL = "https://archive.iypt.org/factsheets/"
IYPT_MORE_LABEL = "Оригинал"
IYPT_TEAM = """По итогам Всероссийского турнира право представлять Россию на XV IYPT
(23–30 мая 2002, Одесса) получили СУНЦ УрГУ и Саров; на международном турнире
выступала команда СУНЦ УрГУ."""

# Результаты отборочных боёв: место по «Итог 1-2-3»; в сумме — этот итог.
RANKING = [
    ("1", "Саров-1", "132.4"),
    ("2", "СУНЦ УрГУ", "130.7"),
    ("3", "АГ СПбГУ", "127.4"),
    ("4", "СУНЦ МГУ", "123.24"),
    ("5", "Заречный", "121.8"),
    ("6", "Екатеринбург", "121.2"),
    ("7", "Качканар", "113.0"),
    ("8", "Саров-3", "106.4"),
    ("9", "Арзамас", "105.75"),
    ("10", "Новодвинск", "104.95"),
    ("11", "Саров-2", "104.85"),
    ("12", "Пушкин", "97.2"),
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
    help = "Заполняет сезон 2002: отборочные и скан оригинала."

    def handle(self, *args, **options):
        page = TournamentPage.objects.filter(year=YEAR).first()
        if not page:
            self.stderr.write("Страницы 2002 нет.")
            return

        root = Path(__file__).resolve().parents[3]
        path = root / "rypt/static/docs/results" / SCAN
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
        add_rows(page, TournamentResultRow.KIND_RANKING, RANKING, 0)
        page.save_revision().publish()

        self.stdout.write(
            self.style.SUCCESS(
                f"2002: {CITY}, {START} — {END}, рейтинг {len(RANKING)}, "
                f"оригинал → {MORE_URL}"
            )
        )
