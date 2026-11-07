"""Заполняет сезон 1996: результаты отборочных боёв + IYPT.

Источник скана: архив фонда, папка 29, лист 493.
Турнир: Новгород. На IX IYPT (Грузия) поехали Новгород и СУНЦ МГУ.
"""

from pathlib import Path

from django.core.management.base import BaseCommand

from home.models import TournamentPage, TournamentResultRow

YEAR = 1996
CITY = "Новгород"
MORE_LABEL = "Оригинал (архив фонда, папка 29, лист 493)"
MORE_URL = "/static/docs/results/1996-komandnoe-pervenstvo.jpg"
IYPT_MORE_URL = "https://archive.iypt.org/factsheets/"
IYPT_MORE_LABEL = "Оригинал"

IYPT_TEAM = """На IX IYPT (29 июня — 5 июля 1996, Цхалтубо, Грузия) выступали две российские команды: Новгород и СУНЦ МГУ.

Обе команды получили дипломы III степени."""

# Место по скану; в баллах — сумма SP.
RANKING = [
    ("1", "Москва", "1007"),
    ("2", "Новгород10", "1006"),
    ("3", "Новгород11", "985"),
    ("4", "Екатеринбург", "893"),
    ("5", "Улан-Удэ", "879"),
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
    help = "Заполняет сезон 1996: отборочные бои и скан оригинала."

    def handle(self, *args, **options):
        page = TournamentPage.objects.filter(year=YEAR).first()
        if not page:
            self.stderr.write("Страницы 1996 нет.")
            return

        scan = Path(__file__).resolve().parents[3] / "rypt/static/docs/results/1996-komandnoe-pervenstvo.jpg"
        if not scan.exists():
            self.stderr.write(f"Нет скана: {scan}")
            return

        page.city = CITY
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
                f"1996: {CITY}, рейтинг {len(RANKING)}, IYPT текст, "
                f"оригинал → {MORE_URL}"
            )
        )
