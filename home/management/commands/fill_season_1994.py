"""Заполняет сезон 1994 по протоколу Оргкомитета и Жюри.

Источник: скан «ПРОТОКОЛ совместного заседания… XVI … турнира».
В таблице на скане порядок строк не по местам — на сайте сортируем по месту.
"""

from pathlib import Path

from django.core.management.base import BaseCommand

from home.models import TournamentPage, TournamentResultRow

YEAR = 1994
CITY = "Москва, СУНЦ МГУ"
MORE_LABEL = "Оригинал"
MORE_URL = "/static/docs/results/1994-protokol.jpg"

# Порядок: I → II → III → участники (как на скане внутри одной ступени).
RANKING = [
    ("I", "СУНЦ МГУ", "I степени"),
    ("II", "Екатеринбург", "II степени"),
    ("II", "Фрязино", "II степени"),
    ("III", "Бурятия", "III степени"),
    ("III", "Новгород", "III степени"),
    ("", "Одесса", "участника"),
    ("", "Норильск", "участника"),
    ("", "Шатура", "участника"),
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
    help = "Заполняет сезон 1994: протокол (места + дипломы) и скан оригинала."

    def handle(self, *args, **options):
        page = TournamentPage.objects.filter(year=YEAR).first()
        if not page:
            self.stderr.write("Страницы 1994 нет.")
            return

        scan = Path(__file__).resolve().parents[3] / "rypt/static/docs/results/1994-protokol.jpg"
        if not scan.exists():
            self.stderr.write(f"Нет скана: {scan}")
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
                f"1994: {CITY}, рейтинг {len(RANKING)} (по местам), оригинал → {MORE_URL}"
            )
        )
