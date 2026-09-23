import shutil
from datetime import date
from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand

from home.models import TournamentPage, TournamentResultRow

YEAR = 2014
CITY = "Новосибирск"
START = date(2014, 3, 25)
END = date(2014, 3, 31)
MORE_LABEL = "Оригинал"
MORE_FILE = Path(__file__).with_name("season_files") / "Protokol_RTYuF_2014_publikovat.xls"
MORE_MEDIA_REL = Path("documents") / "2014" / "Protokol_RTYuF_2014_publikovat.xls"

IYPT_MORE_URL = ""
IYPT_MORE_LABEL = ""
IYPT_TEAM = """Состав сборной — участники из Новосибирска.

Сборная принимала участие в Международном турнире. По итогам турнира — серебряные медали."""

# Лист «итоги отб боев», ПСО.
RANKING = [
    ("1", "Школа Пифагора", "223.88"),
    ("2", "СУНЦ НГУ", "205.88"),
    ("3", "Случайные люди", "202.07"),
    ("4", "СУНЦ МГУ", "197.92"),
    ("5", "ИнжеНЭТИк", "191.58"),
    ("6", "Винегрет-Воронеж", "179.92"),
    ("7", "Диоген", "179.63"),
    ("8", "СУНЦ УрФУ-2", "178.92"),
    ("9", "Лицей 130", "177.96"),
    ("10", "Воронеж", "174.85"),
    ("11", "ОМлет", "174.25"),
    ("12", "АГ СПбГУ", "170.28"),
    ("13", "113-ый элемент", "164.93"),
    ("14", "СУНЦ УрФУ-1", "164.31"),
    ("15", "Брейн индукция 1", "161.95"),
    ("16", "Брейн индукция 2", "161.14"),
    ("17", "Регион 42", "160.71"),
    ("18", "М5", "159.13"),
    ("19", "Кипящий лёд", "156.88"),
    ("20", "ШОРты", "144.13"),
    ("21", "17!", "114.28"),
    ("22", "Бочка", "103.40"),
]

LEAGUE_A = [
    ("1", "Школа Пифагора", "223.88"),
    ("2", "СУНЦ НГУ", "205.88"),
    ("3", "Случайные люди", "202.07"),
    ("4", "СУНЦ МГУ", "197.92"),
    ("5", "Диоген", "179.63"),
    ("6", "СУНЦ УрФУ-2", "178.92"),
    ("7", "Лицей 130", "177.96"),
    ("8", "Воронеж", "174.85"),
    ("9", "АГ СПбГУ", "170.28"),
    ("10", "СУНЦ УрФУ-1", "164.31"),
    ("11", "М5", "159.13"),
]

LEAGUE_B = [
    ("1", "ИнжеНЭТИк", "191.58"),
    ("2", "Винегрет-Воронеж", "179.92"),
    ("3", "ОМлет", "174.25"),
    ("4", "113-ый элемент", "164.93"),
    ("5", "Брейн индукция 1", "161.95"),
    ("6", "Брейн индукция 2", "161.14"),
    ("7", "Регион 42", "160.71"),
    ("8", "Кипящий лёд", "156.88"),
    ("9", "ШОРты", "144.13"),
    ("10", "17!", "114.28"),
    ("11", "Бочка", "103.40"),
]

# Лист «финал», колонка СО.
FINAL_A = [
    ("1", "Школа Пифагора", "44.25"),
    ("2", "Случайные люди", "43.30"),
    ("3", "СУНЦ НГУ", "41.50"),
]

FINAL_B = [
    ("1", "Винегрет-Воронеж", "34.86"),
    ("2", "ИнжеНЭТИк", "32.86"),
    ("3", "ОМлет", "31.71"),
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
    help = "Заполняет даты, город, таблицы, IYPT и файл-оригинал сезона 2014."

    def handle(self, *args, **options):
        page = TournamentPage.objects.filter(year=YEAR).first()
        if not page:
            self.stderr.write("Страницы 2014 нет.")
            return
        page.city = CITY
        page.date_start = START
        page.date_end = END
        if MORE_FILE.exists():
            dest = Path(settings.MEDIA_ROOT) / MORE_MEDIA_REL
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(MORE_FILE, dest)
            page.results_more_url = f"{settings.MEDIA_URL}{MORE_MEDIA_REL.as_posix()}"
        else:
            page.results_more_url = ""
        page.results_more_label = MORE_LABEL
        page.iypt_team = IYPT_TEAM
        page.iypt_more_url = IYPT_MORE_URL
        page.iypt_more_label = IYPT_MORE_LABEL
        page.photo_album_url = ""
        page.save()
        page.ranking.all().delete()
        order = 0
        order = add_rows(page, TournamentResultRow.KIND_RANKING, RANKING, order)
        order = add_rows(page, TournamentResultRow.KIND_LEAGUE_A, LEAGUE_A, order)
        order = add_rows(page, TournamentResultRow.KIND_LEAGUE_B, LEAGUE_B, order)
        order = add_rows(page, TournamentResultRow.KIND_FINAL, FINAL_A, order)
        add_rows(page, TournamentResultRow.KIND_FINAL_B, FINAL_B, order)
        page.photos.all().delete()
        page.save_revision().publish()
        self.stdout.write(
            self.style.SUCCESS(
                f"2014: общий {len(RANKING)}, высшая {len(LEAGUE_A)}, "
                f"первая {len(LEAGUE_B)}, финал высшей {len(FINAL_A)}, "
                f"финал первой {len(FINAL_B)}, оригинал {page.results_more_url or '—'}."
            )
        )
