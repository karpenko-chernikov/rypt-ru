import json
from datetime import date
from pathlib import Path

from django.core.management.base import BaseCommand

from home.models import TournamentPage, TournamentPhoto, TournamentResultRow

YEAR = 2009
CITY = "Москва"
START = date(2009, 3, 16)
END = date(2009, 3, 21)
MORE_LABEL = "Оригинал"
MORE_URL = "http://rusypt.msu.ru/archive/tour2009.shtml"
PHOTO_ALBUM = "https://vk.ru/album-44049348_172882517"
PHOTO_JSON = Path(__file__).with_name("season_2009_photos.json")

IYPT_TEAM = """Состав сборной (СУНЦ МГУ, Москва):
Астапов Артем
Гришина Яна
Закиров Марат
Кудряшова Людмила
Мордвинцев Илья

Сборная направлялась на XXII Международный Турнир Юных Физиков в Тяньцзине (Китай)."""

RANKING = [
    ("1", "СУНЦ МГУ", "Москва", "234"),
    ("2", "СУНЦ УрГУ-1", "Екатеринбург", "231"),
    ("3", "Лицей 130", "Екатеринбург", "213"),
    ("4", "СУНЦ УрГУ-3", "Екатеринбург", "207"),
    ("5", "АГ СПбГУ", "Санкт-Петербург", "204"),
    ("6", "ФМЛ 239", "Санкт-Петербург", "202"),
    ("7", "СУНЦ УрГУ-2", "Екатеринбург", "201"),
    ("8", "Пушкин", "Санкт-Петербург", "186"),
    ("9", "Лесной", "Лесной", "180"),
    ("10", "Воронеж", "Воронеж", "170"),
    ("11", "Саранск", "Саранск", "163"),
    ("12", "Арзамас", "Арзамас", "146"),
    ("13", "Лицей 1580", "Москва", "139"),
]

LEAGUE_A = [
    ("1", "СУНЦ МГУ", "Москва", "234"),
    ("2", "СУНЦ УрГУ-1", "Екатеринбург", "231"),
    ("3", "Лицей 130", "Екатеринбург", "213"),
    ("4", "СУНЦ УрГУ-3", "Екатеринбург", "207"),
    ("5", "АГ СПбГУ", "Санкт-Петербург", "204"),
    ("6", "ФМЛ 239", "Санкт-Петербург", "202"),
    ("7", "СУНЦ УрГУ-2", "Екатеринбург", "201"),
]

LEAGUE_B = [
    ("1", "Пушкин", "Санкт-Петербург", "186"),
    ("2", "Лесной", "Лесной", "180"),
    ("3", "Воронеж", "Воронеж", "170"),
    ("4", "Саранск", "Саранск", "163"),
    ("5", "Арзамас", "Арзамас", "146"),
    ("6", "Лицей 1580", "Москва", "139"),
]


def add_rows(page, kind, rows, order):
    for place, team, city, points in rows:
        TournamentResultRow.objects.create(
            page=page,
            kind=kind,
            place=place,
            team=team,
            city=city,
            points=points,
            sort_order=order,
        )
        order += 1
    return order


class Command(BaseCommand):
    help = "Заполняет сезон 2009: даты, таблицы, IYPT и фото."

    def handle(self, *args, **options):
        page = TournamentPage.objects.filter(year=YEAR).first()
        if not page:
            self.stderr.write("Страницы 2009 нет.")
            return
        page.city = CITY
        page.date_start = START
        page.date_end = END
        page.results_more_url = MORE_URL
        page.results_more_label = MORE_LABEL
        page.iypt_team = IYPT_TEAM
        page.iypt_more_url = ""
        page.iypt_more_label = ""
        page.photo_album_url = PHOTO_ALBUM
        page.save()
        page.ranking.all().delete()
        order = 0
        order = add_rows(page, TournamentResultRow.KIND_RANKING, RANKING, order)
        order = add_rows(page, TournamentResultRow.KIND_LEAGUE_A, LEAGUE_A, order)
        add_rows(page, TournamentResultRow.KIND_LEAGUE_B, LEAGUE_B, order)
        page.photos.all().delete()
        photo_count = 0
        if PHOTO_JSON.exists():
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
                f"2009: общий {len(RANKING)}, высшая {len(LEAGUE_A)}, "
                f"первая {len(LEAGUE_B)}, фото {photo_count}."
            )
        )
