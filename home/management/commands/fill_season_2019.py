import json
from datetime import date
from pathlib import Path

from django.core.management.base import BaseCommand

from home.models import TournamentPage, TournamentPhoto, TournamentResultRow

YEAR = 2019
CITY = "Симферополь"
START = date(2019, 3, 24)
END = date(2019, 3, 31)
MORE_LABEL = "Оригинал"
PHOTO_ALBUM = "https://vk.ru/album-44049348_261863720"
PHOTO_JSON = Path(__file__).with_name("season_2019_photos.json")

IYPT_MORE_URL = ""
IYPT_MORE_LABEL = "Оригинал"
IYPT_TEAM = """Состав сборной:
Грибова Ника
Шушарин Андрей
Полоник Иван
Фокин Владимир
Замараева Екатерина

Сборная принимала участие в Международном турнире в Варшаве (Польша). По итогам турнира заняла 19 место."""

# Общий рейтинг: высшая + первая по Итог.
RANKING = [
    ("1", "СУНЦ УрФУ - 1", "222.15"),
    ("2", "План-капкан", "203.78"),
    ("3", "СУНЦ УрФУ - 130", "202.52"),
    ("4", "Бобры", "202.38"),
    ("5", "Демоны физики", "195.88"),
    ("6", "ИнжеНЭТик", "193.33"),
    ("7", "ДПН", "189.50"),
    ("8", "Кипящий лед", "180.08"),
    ("9", "451 градус по Фаренгейту", "179.33"),
    ("10", "NEW", "177.50"),
    ("11", "12 детей науки", "177.48"),
    ("12", "ЛаНаТ", "177.03"),
    ("13", "ЭЙНШтейн", "176.75"),
    ("14", "Качканар", "176.60"),
    ("15", "ОНП", "175.13"),
    ("16", 'Команда "А"', "174.98"),
    ("17", "Физикон", "173.70"),
    ("18", "ВольтМетр", "171.88"),
    ("19", "АГ СПбГУ", "166.93"),
    ("20", "Люцифер", "165.58"),
    ("21", "КВАНТ-О", "165.53"),
    ("22", "Лицей №84", "160.75"),
    ("23", "Случайные люди", "160.33"),
    ("24", "239", "159.00"),
    ("25", "КВАНТ-Б", "153.25"),
    ("26", "Цунами", "150.10"),
    ("27", "Кимберлит", "142.88"),
    ("28", "Девятый легион", "141.58"),
    ("29", "Ч.Т.Д.", "137.85"),
    ("30", "73", "134.08"),
    ("31", "Темпаральный парадоксон", "107.15"),
]

LEAGUE_A = [
    ("1", "СУНЦ УрФУ - 1", "222.15"),
    ("2", "План-капкан", "203.78"),
    ("3", "СУНЦ УрФУ - 130", "202.52"),
    ("4", "Бобры", "202.38"),
    ("5", "Демоны физики", "195.88"),
    ("6", "ИнжеНЭТик", "193.33"),
    ("7", "АГ СПбГУ", "166.93"),
    ("8", "КВАНТ-О", "165.53"),
    ("9", "Случайные люди", "160.33"),
]

LEAGUE_B = [
    ("1", "ДПН", "189.50"),
    ("2", "Кипящий лед", "180.08"),
    ("3", "451 градус по Фаренгейту", "179.33"),
    ("4", "NEW", "177.50"),
    ("5", "12 детей науки", "177.48"),
    ("6", "ЛаНаТ", "177.03"),
    ("7", "ЭЙНШтейн", "176.75"),
    ("8", "Качканар", "176.60"),
    ("9", "ОНП", "175.13"),
    ("10", 'Команда "А"', "174.98"),
    ("11", "Физикон", "173.70"),
    ("12", "ВольтМетр", "171.88"),
    ("13", "Люцифер", "165.58"),
    ("14", "Лицей №84", "160.75"),
    ("15", "239", "159.00"),
    ("16", "КВАНТ-Б", "153.25"),
    ("17", "Цунами", "150.10"),
    ("18", "Кимберлит", "142.88"),
    ("19", "Девятый легион", "141.58"),
    ("20", "Ч.Т.Д.", "137.85"),
    ("21", "73", "134.08"),
    ("22", "Темпаральный парадоксон", "107.15"),
]

# Протокол финала высшей: сумма 3×ср(Д) + 2×ср(О).
FINAL_A = [
    ("1", "План-капкан", "42.21"),
    ("2", "СУНЦ УрФУ - 1", "40.79"),
    ("3", "СУНЦ УрФУ - 130", "35.07"),
]

# Протокол финала первой лиги.
FINAL_B = [
    ("1", "ДПН", "36.33"),
    ("2", "Кипящий лед", "34.83"),
    ("3", "451 градус по Фаренгейту", "33.17"),
]

# IYPT 2019, сумма по 5 боям.
IYPT_RANKING = [
    ("1", "Сингапур", "228.30"),
    ("2", "Германия", "218.80"),
    ("3", "Швейцария", "209.30"),
    ("4", "Китай", "205.20"),
    ("5", "Корея", "203.80"),
    ("6", "Бразилия", "199.50"),
    ("7", "Украина", "196.80"),
    ("8", "Новая Зеландия", "195.30"),
    ("9", "Швеция", "192.30"),
    ("10", "Канада", "191.80"),
    ("11", "Таиланд", "191.00"),
    ("12", "Венгрия", "188.70"),
    ("13", "Австрия", "188.00"),
    ("14", "Тайвань", "186.60"),
    ("15", "Словакия", "183.20"),
    ("16", "Иран", "182.00"),
    ("17", "Сербия", "181.90"),
    ("18", "Болгария", "178.90"),
    ("19", "Россия", "176.40"),
    ("20", "Беларусь", "175.90"),
    ("21", "США", "175.30"),
    ("22", "Австралия", "172.00"),
    ("23", "Польша", "165.50"),
    ("24", "Хорватия", "162.20"),
    ("25", "Грузия", "160.50"),
    ("26", "Великобритания", "150.00"),
    ("27", "Румыния", "141.90"),
    ("28", "Макао", "137.10"),
    ("29", "Чехия", "137.00"),
    ("30", "Индия", "130.70"),
    ("31", "Мексика", "128.90"),
    ("32", "Пакистан", "125.50"),
    ("33", "Турция", "117.30"),
    ("34", "Греция", "108.57"),
]

# Финал IYPT 2019.
IYPT_FINAL = [
    ("1", "Сингапур", "46.61"),
    ("2", "Германия", "45.11"),
    ("3", "Швейцария", "44.50"),
    ("4", "Китай", "41.21"),
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
    help = "Заполняет даты, город, таблицы, IYPT и фото сезона 2019."

    def handle(self, *args, **options):
        page = TournamentPage.objects.filter(year=YEAR).first()
        if not page:
            self.stderr.write("Страницы 2019 нет.")
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
                f"2019: общий {len(RANKING)}, высшая {len(LEAGUE_A)}, "
                f"первая {len(LEAGUE_B)}, финал высшей {len(FINAL_A)}, "
                f"финал первой {len(FINAL_B)}, IYPT рейтинг {len(IYPT_RANKING)}, "
                f"IYPT финал {len(IYPT_FINAL)}, фото {photo_count}."
            )
        )
