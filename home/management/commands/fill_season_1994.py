"""Заполняет сезон 1994 по протоколу Оргкомитета и Жюри + IYPT.

Источник скана РосТЮФ: архив фонда, папка 29, лист 428.
В таблице на скане порядок строк не по местам — на сайте сортируем по месту.
На VII IYPT (Гронинген) выступали две российские команды.
"""

from pathlib import Path

from django.core.management.base import BaseCommand

from home.models import TournamentPage, TournamentResultRow

YEAR = 1994
CITY = "Москва, СУНЦ МГУ"
MORE_LABEL = "Оригинал (архив фонда, папка 29, лист 428)"
MORE_URL = "/static/docs/results/1994-protokol.jpg"
IYPT_MORE_URL = "https://archive.iypt.org/factsheets/"
IYPT_MORE_LABEL = "Оригинал"

IYPT_TEAM = """На VII IYPT (30 мая — 6 июня 1994, Гронинген, Нидерланды) выступали две российские команды: СУНЦ МГУ и Фрязино (сборная).

СУНЦ МГУ разделил 1-е место с Чехией (диплом I степени). Фрязино — 4-е место (диплом III степени)."""

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

# VII IYPT: итог по местам (после финала / полуфинала); баллы — TSP после SF (или после 3 боёв).
IYPT_RANKING = [
    ("1", "СУНЦ МГУ", "1119"),
    ("1", "Чехия", "1106"),
    ("3", "Грузия", "1067"),
    ("4", "Фрязино", "1063"),
    ("5", "Белоруссия", "1093"),
    ("6", "Венгрия", "1050"),
    ("7", "Нидерланды", "1029"),
    ("8", "Украина", "1014"),
    ("9", "Польша", "1009"),
    ("10", "Словакия", "987"),
    ("11", "Швеция", "740"),
    ("12", "Узбекистан", "725"),
]

# Финал 3.06.1994 — два золота, точные баллы финала неизвестны.
IYPT_FINAL = [
    ("1", "СУНЦ МГУ", ""),
    ("1", "Чехия", ""),
    ("3", "Грузия", ""),
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
    help = "Заполняет сезон 1994: протокол РосТЮФ, IYPT Гронинген, скан оригинала."

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
                f"1994: {CITY}, рейтинг {len(RANKING)}, "
                f"IYPT {len(IYPT_RANKING)}/{len(IYPT_FINAL)}, "
                f"оригинал → {MORE_URL}"
            )
        )
