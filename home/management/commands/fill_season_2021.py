import json
from datetime import date
from pathlib import Path

from django.core.management.base import BaseCommand

from home.models import TournamentPage, TournamentPhoto, TournamentResultRow

YEAR = 2021
CITY = "Екатеринбург"
START = date(2021, 5, 3)
END = date(2021, 5, 8)
MORE_LABEL = "Оригинал"
PHOTO_ALBUM = "https://vk.ru/album-44049348_279215069"
PHOTO_JSON = Path(__file__).with_name("season_2021_photos.json")

IYPT_MORE_URL = "https://cc.iypt.org/iypt2021/rank/"
IYPT_MORE_LABEL = "Оригинал"
IYPT_TEAM = """Состав сборной:
Мария Буда (СЛНШ)
Олеся Карпенко (СЛНШ)
Артем Голомолзин (СЛНШ)
Никита Шаров (СЛНШ)
Екатерина Моисейкина (СУНЦ УРФУ)

Сборная принимала участие в Международном турнире в Кутаиси (Грузия). По итогам турнира заняла 8 место (бронзовые медали)."""

# https://cc.iypt.org/iypt2021/rank/ — Round 5 (TSP).
IYPT_RANKING = [
    ("1", "Словакия", "202.7"),
    ("2", "Польша", "199.5"),
    ("3", "Австрия", "189.2"),
    ("4", "Украина", "189.1"),
    ("5", "Венгрия", "185.9"),
    ("6", "Грузия", "185.0"),
    ("7", "Швейцария", "181.7"),
    ("8", "Россия", "178.9"),
    ("9", "Хорватия", "175.7"),
    ("10", "Чехия", "175.3"),
    ("11", "Греция", "160.8"),
    ("12", "Беларусь", "157.5"),
    ("13", "Болгария", "150.6"),
    ("14", "Иран", "143.9"),
    ("15", "Пакистан", "114.1"),
]

# Final Ranking.
IYPT_FINAL = [
    ("1", "Польша", "45.0"),
    ("2", "Словакия", "42.2"),
    ("3", "Австрия", "40.8"),
]

# Скрин «Итоги отборочных боев», ПСО по убыванию.
RANKING = [
    ("1", "СЛНШ", "227.0"),
    ("2", "СУНЦ МГУ", "220.3"),
    ("3", "СУНЦ-1", "208.3"),
    ("4", "451 по Фаренгейту", "204.7"),
    ("5", "ИнжеНЭТИк", "200.1"),
    ("6", "Бобры", "195.1"),
    ("7", "Лицей 84", "195.0"),
    ("8", "Кипящий лёд", "194.1"),
    ("9", "СУНЦ-2", "183.0"),
    ("10", "Театр юного физика", "179.7"),
    ("11", "Демоны физики", "177.7"),
    ("12", "Диффузия разума", "176.5"),
    ("13", "АГ СПбГУ", "171.9"),
    ("14", "Гриффиндор", "167.0"),
    ("15", "Ом", "165.0"),
    ("16", "Физикон", "164.2"),
    ("17", "Кимберлит", "163.5"),
    ("18", "План опоссума", "160.5"),
]

# Лига «В» — высшая, места внутри лиги по ПСО.
LEAGUE_A = [
    ("1", "СЛНШ", "227.0"),
    ("2", "СУНЦ МГУ", "220.3"),
    ("3", "СУНЦ-1", "208.3"),
    ("4", "451 по Фаренгейту", "204.7"),
    ("5", "ИнжеНЭТИк", "200.1"),
    ("6", "СУНЦ-2", "183.0"),
    ("7", "Демоны физики", "177.7"),
    ("8", "АГ СПбГУ", "171.9"),
]

# Лига «1» — первая.
LEAGUE_B = [
    ("1", "Бобры", "195.1"),
    ("2", "Лицей 84", "195.0"),
    ("3", "Кипящий лёд", "194.1"),
    ("4", "Театр юного физика", "179.7"),
    ("5", "Диффузия разума", "176.5"),
    ("6", "Гриффиндор", "167.0"),
    ("7", "Ом", "165.0"),
    ("8", "Физикон", "164.2"),
    ("9", "Кимберлит", "163.5"),
    ("10", "План опоссума", "160.5"),
]

# FinalVysshaya.pdf: ИТОГ; у СУНЦ МГУ штраф за доклад → 33,46.
FINAL_A = [
    ("1", "СУНЦ-1", "39.31"),
    ("2", "СЛНШ", "38.23"),
    ("3", "СУНЦ МГУ", "33.46"),
]

# FinalPervaya.pdf: ИТОГ.
FINAL_B = [
    ("1", "Кипящий лёд", "39.36"),
    ("2", "Бобры", "38.79"),
    ("3", "Лицей 84", "35.32"),
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
    help = "Заполняет даты, город, таблицы результатов, IYPT и фото сезона 2021."

    def handle(self, *args, **options):
        page = TournamentPage.objects.filter(year=YEAR).first()
        if not page:
            self.stderr.write("Страницы 2021 нет.")
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
        order = add_rows(page, TournamentResultRow.KIND_FINAL_B, FINAL_B, order)
        order = add_rows(page, TournamentResultRow.KIND_IYPT_RANKING, IYPT_RANKING, order)
        add_rows(page, TournamentResultRow.KIND_IYPT_FINAL, IYPT_FINAL, order)
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
                f"2021: общий {len(RANKING)}, высшая {len(LEAGUE_A)}, "
                f"первая {len(LEAGUE_B)}, финал высшей {len(FINAL_A)}, "
                f"финал первой {len(FINAL_B)}, IYPT рейтинг {len(IYPT_RANKING)}, "
                f"IYPT финал {len(IYPT_FINAL)}, фото {photo_count}."
            )
        )
