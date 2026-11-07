"""Заполняет сезон 1995: командный зачёт + мета + IYPT.

Источник скана: архив фонда, папка 24, листы 361–363.
Турнир: Фрязино, 30 марта — 5 апреля 1995.
Строки после Саяногорска (00 и пустые) не включаем.
"""

from datetime import date
from pathlib import Path

from django.core.management.base import BaseCommand

from home.models import TournamentPage, TournamentResultRow

YEAR = 1995
CITY = "Фрязино"
START = date(1995, 3, 30)
END = date(1995, 4, 5)
MORE_LABEL = "Оригинал (архив фонда, папка 24, листы 361–363)"
MORE_URL = "/static/docs/results/1995-komandnyy-zachet.jpg"
IYPT_MORE_URL = "https://archive.iypt.org/factsheets/"
IYPT_MORE_LABEL = "Оригинал"

IYPT_TEAM = """На VIII IYPT (4–11 июня 1995, Спала, Польша) выступали две российские команды: СУНЦ МГУ и Новгород.

Команды заняли 13-е и 14-е места."""

# Место по скану (по сумме R); в баллах — сумма SP.
RANKING = [
    ("1", "Новгород", "1050"),
    ("2", "СУНЦ", "1014"),
    ("3", "Протвино", "924"),
    ("4", "Одесса", "942"),
    ("5", "Краснодар", "926"),
    ("6", "Арзамас-16", "876"),
    ("7", "Люблино", "930"),
    ("8", "Саяногорск", "796"),
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
    help = "Заполняет сезон 1995: командный зачёт, даты, IYPT, скан оригинала."

    def handle(self, *args, **options):
        page = TournamentPage.objects.filter(year=YEAR).first()
        if not page:
            self.stderr.write("Страницы 1995 нет.")
            return

        scan = Path(__file__).resolve().parents[3] / "rypt/static/docs/results/1995-komandnyy-zachet.jpg"
        if not scan.exists():
            self.stderr.write(f"Нет скана: {scan}")
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
                f"1995: {CITY}, {START} — {END}, рейтинг {len(RANKING)}, "
                f"IYPT текст, оригинал → {MORE_URL}"
            )
        )
