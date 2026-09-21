from datetime import date
from pathlib import Path
import json

from django.core.management.base import BaseCommand

from home.models import TournamentPage, TournamentPhoto, TournamentResultRow

YEAR = 2023
CITY = "Москва"
START = date(2023, 3, 24)
END = date(2023, 3, 30)
MORE_URL = "http://92.63.100.65:90/RUSYPT2023/ranking"
MORE_LABEL = "Оригинал"
PHOTO_ALBUM = "https://vk.ru/album-44049348_292157656"
PHOTO_JSON = Path(__file__).with_name("season_2023_photos.json")

IYPT_MORE_URL = "https://cc.iypt.org/oypt2023/rank/"
IYPT_MORE_LABEL = "Оригинал"
IYPT_TEAM = """Состав сборной:
Данил Воробьёв (Пластмассовый мир)
Александр Зинкевич (Бобры)
Антон Гаек
Александра Ченцова (Пластмассовый мир)
Кирилл Смирнов (Пластмассовый мир)

Сборная принимала участие в Международном турнире в онлайн-формате под названием Field of Experiments. По итогам турнира заняла 9 место (бронзовые медали)."""

# http://92.63.100.65:90/RUSYPT2023/ranking
RANKING = [
    ("1", "Бобры", "194.63"),
    ("2", "Случайные люди", "185.13"),
    ("3", "СУНЦ-1.1", "180.08"),
    ("4", "Ом", "175.58"),
    ("5", "Кипящий лёд", "172.58"),
    ("6", "Пластмассовый мир", "171.75"),
    ("7", "452", "165.88"),
    ("8", "Стражи хаоса", "163.63"),
    ("9", "Лицей 84", "162.96"),
    ("10", "Победители по шизне", "162.62"),
    ("11", "Буравчики", "159.21"),
    ("12", "СУНЦ-1", "158.97"),
    ("13", "Путь самурая", "153.89"),
    ("14", "Театр Юного Физика", "149.72"),
    ("15", "МБвТ", "142.08"),
    ("16", "СУНЦ-2", "141.11"),
    ("17", "Физикон-1", "139.63"),
    ("18", "Ионный ветер", "138.75"),
    ("19", "Качканар", "136.67"),
    ("20", "Комнатные ростки", "133.75"),
    ("21", "Квантовый кактус", "130.17"),
    ("22", "Физикон-2", "121.65"),
    ("23", "Optimum", "112.20"),
    ("24", "Вирус разума", "83.93"),
]

# Группа A на IPT connect.
LEAGUE_A = [
    ("1", "Бобры", "194.63"),
    ("2", "Случайные люди", "185.13"),
    ("3", "СУНЦ-1.1", "180.08"),
    ("4", "Ом", "175.58"),
    ("5", "Пластмассовый мир", "171.75"),
    ("6", "452", "165.88"),
    ("7", "Победители по шизне", "162.62"),
    ("8", "СУНЦ-1", "158.97"),
    ("9", "Путь самурая", "153.89"),
    ("10", "СУНЦ-2", "141.11"),
]

# Группа B на IPT connect.
LEAGUE_B = [
    ("1", "Кипящий лёд", "172.58"),
    ("2", "Стражи хаоса", "163.63"),
    ("3", "Лицей 84", "162.96"),
    ("4", "Буравчики", "159.21"),
    ("5", "Театр Юного Физика", "149.72"),
    ("6", "МБвТ", "142.08"),
    ("7", "Физикон-1", "139.63"),
    ("8", "Ионный ветер", "138.75"),
    ("9", "Качканар", "136.67"),
    ("10", "Комнатные ростки", "133.75"),
    ("11", "Квантовый кактус", "130.17"),
    ("12", "Физикон-2", "121.65"),
    ("13", "Optimum", "112.20"),
    ("14", "Вирус разума", "83.93"),
]

# Физический бой 7 (Финал), сумма.
FINAL_A = [
    ("1", "Случайные люди", "36.41"),
    ("2", "Бобры", "35.05"),
    ("3", "СУНЦ-1.1", "31.77"),
]

# Физический бой 6 (First league final), сумма.
FINAL_B = [
    ("1", "Кипящий лёд", "34.92"),
    ("2", "Лицей 84", "31.85"),
    ("3", "Стражи хаоса", "26.96"),
]

# https://cc.iypt.org/oypt2023/rank/ — Round 5 (TSP).
IYPT_RANKING = [
    ("1", "Сингапур", "194.9"),
    ("2", "Германия", "193.0"),
    ("3", "Сингапур B", "181.7"),
    ("4", "Австрия", "171.4"),
    ("5", "Китай", "170.7"),
    ("6", "Китайский Тайбэй", "170.5"),
    ("7", "Корея Arirang", "162.2"),
    ("8", "Бразилия", "159.6"),
    ("9", "Field of Experiments", "157.3"),
    ("10", "Корея Taegeuk", "154.2"),
    ("11", "Швеция", "133.0"),
    ("12", "Новая Зеландия", "129.9"),
    ("13", "Греция", "128.9"),
    ("14", "Австралия", "127.7"),
    ("15", "Гонконг", "120.1"),
    ("16", "Индия", "111.8"),
    ("17", "Австралия B", "89.8"),
    ("18", "Иран Team Valeh", "86.7"),
]

# Final Ranking / финальный бой.
IYPT_FINAL = [
    ("1", "Сингапур", "45.7"),
    ("2", "Германия", "42.8"),
    ("3", "Австрия", "40.5"),
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
    help = "Заполняет даты, город, таблицы результатов, IYPT и фото сезона 2023."

    def handle(self, *args, **options):
        page = TournamentPage.objects.filter(year=YEAR).first()
        if not page:
            self.stderr.write("Страницы 2023 нет.")
            return
        page.city = CITY
        page.date_start = START
        page.date_end = END
        page.results_more_url = MORE_URL
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
                f"2023: общий {len(RANKING)}, высшая {len(LEAGUE_A)}, "
                f"первая {len(LEAGUE_B)}, финал высшей {len(FINAL_A)}, "
                f"финал первой {len(FINAL_B)}, IYPT рейтинг {len(IYPT_RANKING)}, "
                f"IYPT финал {len(IYPT_FINAL)}, фото {photo_count}."
            )
        )
