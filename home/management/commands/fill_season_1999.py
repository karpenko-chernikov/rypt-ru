"""Заполняет сезон 1999 по протоколам XXI Российского ТЮФ.

Источники (архив фонда):
- папка 26, лист 106 — результаты отборочных боёв;
- папка 26, лист 131 — полуфинал и финал;
- папка 14, лист 241 — статистика по задачам.
Турнир: Москва, СУНЦ МГУ; на листах — 17–18 марта 1999.
"""

from datetime import date
from pathlib import Path

from django.core.management.base import BaseCommand

from home.models import TournamentPage, TournamentResultRow

YEAR = 1999
CITY = "Москва, СУНЦ МГУ"
START = date(1999, 3, 17)
END = date(1999, 3, 18)
MORE_LABEL = "Оригинал (архив фонда: папка 26, листы 106 и 131; папка 14, лист 241)"
MORE_URL = (
    "/static/docs/results/1999-otborochnye.jpg\n"
    "/static/docs/results/1999-polufinal-final.jpg\n"
    "/static/docs/results/1999-statistika.jpg"
)
SCANS = (
    "1999-otborochnye.jpg",
    "1999-polufinal-final.jpg",
    "1999-statistika.jpg",
)

# Отборочные: место по TR (как на листе); в сумме — TR.
RANKING = [
    ("1", "СУНЦ УрГУ I", "14"),
    ("2", "Москва 363", "11"),
    ("3", "Екатеринбург 9", "10"),
    ("4", "Саров", "9.5"),
    ("4", "СУНЦ МГУ", "9.5"),
    ("4", "АГ СПбГУ", "9.5"),
    ("7", "СУНЦ УрГУ II", "8.5"),
    ("7", "Ставрополь", "8.5"),
    ("9", "Великие Луки", "6"),
    ("9", "Арзамас", "6"),
    ("11", "Глазов II", "4"),
    ("11", "Глазов I", "4"),
    ("11", "Саяногорск", "4"),
]

# Финал: на листе места I, I, II (как дипломы); баллы — SP.
FINAL = [
    ("I", "СУНЦ МГУ", "301"),
    ("I", "СУНЦ УрГУ I", "290"),
    ("II", "Саров", "268"),
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
    help = "Заполняет сезон 1999: отборочные, финал и сканы оригинала."

    def handle(self, *args, **options):
        page = TournamentPage.objects.filter(year=YEAR).first()
        if not page:
            self.stderr.write("Страницы 1999 нет.")
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
                f"1999: {CITY}, {START} — {END}, рейтинг {len(RANKING)}, "
                f"финал {len(FINAL)}, оригинал → {len(SCANS)} листа"
            )
        )
