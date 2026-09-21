from datetime import date
from pathlib import Path
import json

from django.core.management.base import BaseCommand

from home.models import TournamentPage, TournamentPhoto, TournamentResultRow

YEAR = 2022
CITY = "Санкт-Петербург"
START = date(2022, 3, 21)
END = date(2022, 3, 27)
MORE_URL = "http://92.63.100.65:90/RUSYPT2022/ranking"
MORE_LABEL = "Оригинал"
PHOTO_ALBUM = "https://vk.ru/album-44049348_283368624"
PHOTO_JSON = Path(__file__).with_name("season_2022_photos.json")

IYPT_MORE_URL = "https://cc.iypt.org/oypt2022/rank/"
IYPT_MORE_LABEL = "Оригинал"
IYPT_TEAM = """Состав сборной:
Гусев Алексей (СУНЦ-1)
Воробьев Данил (Школа Летово)
Воробьев Артем (Гриффиндор)
Калюжный Михаил (452 F)
Артемий Тарханов (Бобры)

Сборная принимала участие в Международном турнире, который проходил в онлайн-формате. По итогам турнира заняла 7 место."""

# http://92.63.100.65:90/RUSYPT2022/ranking
RANKING = [
    ("1", "СУНЦ-1", "192.63"),
    ("2", "Бобры", "189.48"),
    ("3", "СУНЦ-2", "183.23"),
    ("4", "Статус-КВО", "182.13"),
    ("5", "ИнжеНЭТИк", "179.66"),
    ("6", 'Школа "Летово"', "179.22"),
    ("7", "Кипящий лед", "177.75"),
    ("8", "Гриффиндор", "175.23"),
    ("9", "Ом", "175.13"),
    ("10", "СУНЦ МГУ", "170.88"),
    ("11", "Случайные люди", "169.53"),
    ("12", "Театр юного физика", "169.23"),
    ("13", "Клещи из АГ", "160.88"),
    ("14", "ДИФФУЗИЯ РАЗУМА", "158.03"),
    ("15", "Спектр", "157.60"),
    ("16", "КОНВЕКЦИЯ РАЗУМА", "155.92"),
    ("17", "452F", "150.66"),
    ("18", "Физикон", "135.38"),
]

# Группа A на IPT connect.
LEAGUE_A = [
    ("1", "СУНЦ-1", "192.63"),
    ("2", "Бобры", "189.48"),
    ("3", "СУНЦ-2", "183.23"),
    ("4", "ИнжеНЭТИк", "179.66"),
    ("5", 'Школа "Летово"', "179.22"),
    ("6", "Гриффиндор", "175.23"),
    ("7", "СУНЦ МГУ", "170.88"),
    ("8", "Случайные люди", "169.53"),
    ("9", "Клещи из АГ", "160.88"),
    ("10", "452F", "150.66"),
]

# Группа B на IPT connect.
LEAGUE_B = [
    ("1", "Статус-КВО", "182.13"),
    ("2", "Кипящий лед", "177.75"),
    ("3", "Ом", "175.13"),
    ("4", "Театр юного физика", "169.23"),
    ("5", "ДИФФУЗИЯ РАЗУМА", "158.03"),
    ("6", "Спектр", "157.60"),
    ("7", "КОНВЕКЦИЯ РАЗУМА", "155.92"),
    ("8", "Физикон", "135.38"),
]

# Физический бой 7, сумма.
FINAL_A = [
    ("1", "СУНЦ-1", "34.27"),
    ("2", "Бобры", "33.95"),
    ("3", "СУНЦ-2", "30.00"),
]

# First league final, физический бой 6.
FINAL_B = [
    ("1", "Статус-КВО", "35.63"),
    ("2", "Кипящий лед", "34.67"),
    ("3", "Ом", "31.67"),
]

# https://cc.iypt.org/oypt2022/rank/ — Round 5 (TSP).
IYPT_RANKING = [
    ("1", "Сингапур", "184.2"),
    ("2", "Китай", "171.2"),
    ("3", "Канада", "167.7"),
    ("4", "Корея", "161.5"),
    ("5", "Новая Зеландия", "157.0"),
    ("6", "Таиланд", "142.2"),
    ("7", "Россия", "135.0"),
    ("8", "Австралия", "119.2"),
]

# Final Ranking / финальный бой.
IYPT_FINAL = [
    ("1", "Китай", "37.0"),
    ("2", "Сингапур", "36.3"),
    ("3", "Канада", "35.7"),
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
    help = "Заполняет даты, город, таблицы результатов и IYPT сезона 2022."

    def handle(self, *args, **options):
        page = TournamentPage.objects.filter(year=YEAR).first()
        if not page:
            self.stderr.write("Страницы 2022 нет.")
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
                f"2022: общий {len(RANKING)}, высшая {len(LEAGUE_A)}, "
                f"первая {len(LEAGUE_B)}, финал высшей {len(FINAL_A)}, "
                f"финал первой {len(FINAL_B)}, IYPT рейтинг {len(IYPT_RANKING)}, "
                f"IYPT финал {len(IYPT_FINAL)}, фото {photo_count}."
            )
        )
