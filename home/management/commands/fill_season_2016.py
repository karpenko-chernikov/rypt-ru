import json
from datetime import date
from pathlib import Path

from django.core.management.base import BaseCommand

from home.models import TournamentPage, TournamentPhoto, TournamentResultRow

YEAR = 2016
CITY = "Екатеринбург"
START = date(2016, 3, 24)
END = date(2016, 3, 29)
MORE_LABEL = "Оригинал"
PHOTO_ALBUM = "https://vk.ru/album-47350318_230138987"
PHOTO_JSON = Path(__file__).with_name("season_2016_photos.json")

IYPT_MORE_URL = ""
IYPT_MORE_LABEL = ""
IYPT_TEAM = """Состав сборной (СУНЦ УрФУ-1):
Пешнина Дарья
Дерябин Василий
Рыжихин Илья
Олифиренко Михаил
Калинин Даниил"""

# Отборочные (сумма 5 боёв), общий рейтинг.
RANKING = [
    ("1", "СУНЦ УрФУ-1", "239.23"),
    ("2", "Случайные люди", "225.15"),
    ("3", "ВМФ", "221"),
    ("4", "Школа Пифагора", "216.58"),
    ("5", "Демоны физики", "215.83"),
    ("6", "Винегрет", "209.43"),
    ("7", "Регион 42", "208.8"),
    ("8", "СУНЦ УрФУ-3", "205.35"),
    ("9", "Кипящий лёд", "202.93"),
    ("10", "Аметисты", "197.43"),
    ("11", "ИнжеНЭТиК", "195.34"),
    ("12", "ЛаНаТ", "191.9"),
    ("13", "239", "182.1"),
    ("14", "Брейн-индукция-2", "178.5"),
    ("15", "Брейн-индукция-1", "178.3"),
    ("16", "СУНЦ УрФУ-2", "174"),
    ("17", "Рододендрон", "159.58"),
    ("18", "Шушарики", "152.18"),
    ("19", "Интерференция", "144.55"),
]

LEAGUE_A = [
    ("1", "СУНЦ УрФУ-1", "239.23"),
    ("2", "Случайные люди", "225.15"),
    ("3", "Школа Пифагора", "216.58"),
    ("4", "Демоны физики", "215.83"),
    ("5", "СУНЦ УрФУ-3", "205.35"),
    ("6", "ИнжеНЭТиК", "195.34"),
    ("7", "ЛаНаТ", "191.9"),
    ("8", "СУНЦ УрФУ-2", "174"),
]

LEAGUE_B = [
    ("1", "ВМФ", "221"),
    ("2", "Винегрет", "209.43"),
    ("3", "Регион 42", "208.8"),
    ("4", "Кипящий лёд", "202.93"),
    ("5", "Аметисты", "197.43"),
    ("6", "239", "182.1"),
    ("7", "Брейн-индукция-2", "178.5"),
    ("8", "Брейн-индукция-1", "178.3"),
    ("9", "Рододендрон", "159.58"),
    ("10", "Шушарики", "152.18"),
    ("11", "Интерференция", "144.55"),
]

# Финал по баллам финала (не по ИТОГ).
FINAL_A = [
    ("1", "Школа Пифагора", "43.5"),
    ("2", "СУНЦ УрФУ-1", "43.375"),
    ("3", "Случайные люди", "40.5"),
]

FINAL_B = [
    ("1", "ВМФ", "38.44"),
    ("2", "Регион 42", "38.25"),
    ("3", "Винегрет", "38"),
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
    help = "Заполняет таблицы, IYPT (состав) и фото сезона 2016."

    def handle(self, *args, **options):
        page = TournamentPage.objects.filter(year=YEAR).first()
        if not page:
            self.stderr.write("Страницы 2016 нет.")
            return
        page.city = CITY
        page.date_start = START
        page.date_end = END
        page.results_more_url = ""
        page.results_more_label = MORE_LABEL
        page.iypt_team = IYPT_TEAM
        page.iypt_more_url = IYPT_MORE_URL
        page.iypt_more_label = IYPT_MORE_LABEL
        page.photo_album_url = PHOTO_ALBUM
        page.save()
        page.ranking.all().delete()
        order = 0
        order = add_rows(page, TournamentResultRow.KIND_RANKING, RANKING, order)
        order = add_rows(page, TournamentResultRow.KIND_LEAGUE_A, LEAGUE_A, order)
        order = add_rows(page, TournamentResultRow.KIND_LEAGUE_B, LEAGUE_B, order)
        order = add_rows(page, TournamentResultRow.KIND_FINAL, FINAL_A, order)
        add_rows(page, TournamentResultRow.KIND_FINAL_B, FINAL_B, order)
        photo_count = page.photos.count()
        if PHOTO_JSON.exists() and photo_count == 0:
            shots = json.loads(PHOTO_JSON.read_text(encoding="utf-8"))
            TournamentPhoto.objects.bulk_create(
                [
                    TournamentPhoto(
                        page=page,
                        external_url=shot.get("src", ""),
                        original_url=shot.get("original", ""),
                        caption=(shot.get("caption") or "")[:200],
                        sort_order=index,
                    )
                    for index, shot in enumerate(shots)
                ]
            )
            photo_count = len(shots)
        page.save_revision().publish()
        self.stdout.write(
            self.style.SUCCESS(
                f"2016: общий {len(RANKING)}, высшая {len(LEAGUE_A)}, "
                f"первая {len(LEAGUE_B)}, финал высшей {len(FINAL_A)}, "
                f"финал первой {len(FINAL_B)}, фото {photo_count}."
            )
        )
