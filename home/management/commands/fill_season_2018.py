import json
from datetime import date
from pathlib import Path

from django.core.management.base import BaseCommand

from home.models import TournamentPage, TournamentPhoto, TournamentResultRow

YEAR = 2018
CITY = "Новосибирск"
START = date(2018, 3, 26)
END = date(2018, 3, 30)
MORE_LABEL = "Оригинал"
PHOTO_ALBUMS = [
    "https://vk.ru/album-47350318_252837761",
    "https://vk.ru/album-44049348_252807019",
]
PHOTO_JSON = Path(__file__).with_name("season_2018_photos.json")

IYPT_MORE_URL = ""
IYPT_MORE_LABEL = ""
IYPT_TEAM = """Состав сборной:
Козлов Никита
Турищева Полина
Пальцева Анастасия
Разуева Дарья
Полтораднев Кирилл

Сборная принимала участие в Международном турнире в Пекине (Китай). По итогам турнира заняла 21 место."""

# Итоги отборочных боев, ПСО.
RANKING = [
    ("1", "Демоны физики", "212.0"),
    ("2", "СУНЦ-1", "205.8"),
    ("3", "Изолента", "186.3"),
    ("4", "Регион 42", "184.6"),
    ("5", "Синергия", "180.9"),
    ("6", "ИнжеНЭТИк", "178.3"),
    ("7", "СУНЦ МГУ", "176.2"),
    ("8", "СУНЦ-2", "174.5"),
    ("9", "Кипящий лёд", "173.8"),
    ("10", "Случайные люди", "173.2"),
    ("11", "ЛАНАТ", "170.5"),
    ("12", "Узумаки", "165.7"),
    ("13", "Что такое ботать?", "159.6"),
    ("14", "ФТЛ", "158.7"),
    ("15", "-273,15", "158.3"),
    ("16", "КОТЭ", "155.5"),
    ("17", "Авангард", "152.0"),
    ("18", "ФМЛ#5", "149.9"),
    ("19", "Сборная Воронежа", "141.4"),
    ("20", "ФИЗКЕК", "139.7"),
    ("21", "Качканар", "137.8"),
    ("22", "Квант", "135.0"),
    ("23", "Ом", "126.7"),
    ("24", "Кимберлит", "126.5"),
    ("25", "Фобос", "126.3"),
    ("26", "СЕЛЕН", "109.1"),
    ("27", "Парсек", "100.9"),
    ("28", "Экситон", "96.2"),
    ("29", "-50 по Фаренгейту", "48.0"),
]

# Лига «В».
LEAGUE_A = [
    ("1", "Демоны физики", "212.0"),
    ("2", "СУНЦ-1", "205.8"),
    ("3", "Изолента", "186.3"),
    ("4", "ИнжеНЭТИк", "178.3"),
    ("5", "СУНЦ МГУ", "176.2"),
    ("6", "СУНЦ-2", "174.5"),
    ("7", "Случайные люди", "173.2"),
    ("8", "ЛАНАТ", "170.5"),
    ("9", "Квант", "135.0"),
]

# Лига «1».
LEAGUE_B = [
    ("1", "Регион 42", "184.6"),
    ("2", "Синергия", "180.9"),
    ("3", "Кипящий лёд", "173.8"),
    ("4", "Узумаки", "165.7"),
    ("5", "Что такое ботать?", "159.6"),
    ("6", "ФТЛ", "158.7"),
    ("7", "-273,15", "158.3"),
    ("8", "КОТЭ", "155.5"),
    ("9", "Авангард", "152.0"),
    ("10", "ФМЛ#5", "149.9"),
    ("11", "Сборная Воронежа", "141.4"),
    ("12", "ФИЗКЕК", "139.7"),
    ("13", "Качканар", "137.8"),
    ("14", "Ом", "126.7"),
    ("15", "Кимберлит", "126.5"),
    ("16", "Фобос", "126.3"),
    ("17", "СЕЛЕН", "109.1"),
    ("18", "Парсек", "100.9"),
    ("19", "Экситон", "96.2"),
    ("20", "-50 по Фаренгейту", "48.0"),
]

# Финал высшей: Итог; при равенстве 36.4 — порядок по отборочным.
FINAL_A = [
    ("1", "Демоны физики", "36.4"),
    ("2", "Изолента", "36.4"),
    ("3", "СУНЦ-1", "34.5"),
]

# Финал первой: места известны, баллов нет.
FINAL_B = [
    ("1", "Синергия", ""),
    ("2", "Кипящий лёд", ""),
    ("3", "Регион 42", ""),
]

# IYPT 2018, TSP.
IYPT_RANKING = [
    ("1", "Сингапур", "222.8"),
    ("2", "Китай", "220.4"),
    ("3", "Корея", "218.6"),
    ("4", "Германия", "211.4"),
    ("5", "Бразилия", "204.8"),
    ("6", "Швеция", "200.1"),
    ("7", "Словакия", "194.9"),
    ("8", "Польша", "192.8"),
    ("9", "Украина", "192.3"),
    ("10", "Швейцария", "192.1"),
    ("11", "Новая Зеландия", "191.0"),
    ("12", "Чехия", "190.9"),
    ("13", "Китайский Тайбэй", "189.9"),
    ("14", "Канада", "187.2"),
    ("15", "Венгрия", "185.1"),
    ("16", "Австрия", "178.1"),
    ("17", "Иран", "177.6"),
    ("18", "Сербия", "176.4"),
    ("19", "Таиланд", "170.0"),
    ("20", "Грузия", "168.3"),
    ("21", "Россия", "166.8"),
    ("22", "Австралия", "166.7"),
    ("23", "Беларусь", "165.5"),
    ("24", "Великобритания", "157.3"),
    ("25", "Пакистан", "155.5"),
    ("26", "Болгария", "150.9"),
    ("27", "Макао", "144.7"),
    ("28", "Румыния", "144.4"),
    ("29", "США", "134.3"),
    ("30", "Индия", "118.1"),
    ("31", "Турция", "115.3"),
    ("32", "Чили", "105.6"),
]

IYPT_FINAL = [
    ("1", "Сингапур", "51.1"),
    ("2", "Китай", "45.1"),
    ("3", "Германия", "42.1"),
    ("4", "Корея", "35.8"),
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
    help = "Заполняет даты, город, таблицы, IYPT и фото сезона 2018."

    def handle(self, *args, **options):
        page = TournamentPage.objects.filter(year=YEAR).first()
        if not page:
            self.stderr.write("Страницы 2018 нет.")
            return
        page.city = CITY
        page.date_start = START
        page.date_end = END
        page.results_more_url = ""
        page.results_more_label = MORE_LABEL
        page.iypt_team = IYPT_TEAM
        page.iypt_more_url = IYPT_MORE_URL
        page.iypt_more_label = IYPT_MORE_LABEL
        page.photo_album_url = "\n".join(PHOTO_ALBUMS)
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
                f"2018: общий {len(RANKING)}, высшая {len(LEAGUE_A)}, "
                f"первая {len(LEAGUE_B)}, финал высшей {len(FINAL_A)}, "
                f"финал первой {len(FINAL_B)}, IYPT рейтинг {len(IYPT_RANKING)}, "
                f"IYPT финал {len(IYPT_FINAL)}, фото {photo_count}."
            )
        )
