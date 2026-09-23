import json
import shutil
from datetime import date
from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand

from home.models import TournamentPage, TournamentPhoto, TournamentResultRow

YEAR = 2017
CITY = "Екатеринбург"
START = date(2017, 3, 25)
END = date(2017, 3, 30)
MORE_LABEL = "Оригинал"
MORE_FILE = Path(__file__).with_name("season_files") / "Protokoly_39_RosTYuF.xlsx"
MORE_MEDIA_REL = Path("documents") / "2017" / "Protokoly_39_RosTYuF.xlsx"
PHOTO_ALBUMS = [
    "https://vk.ru/album-47350318_242875549",
    "https://vk.ru/album-44049348_242866869",
]
PHOTO_JSON = Path(__file__).with_name("season_2017_photos.json")

IYPT_MORE_URL = ""
IYPT_MORE_LABEL = ""
IYPT_TEAM = """Состав сборной:
Турищева Полина
Козлов Никита
Парпиходжаев Илья
Ильин Иван
Буданцев Алексей

Сборная принимала участие в Международном турнире в Сингапуре. По итогам турнира заняла 16 место."""

# Общий рейтинг: высшая + первая по сумме.
RANKING = [
    ("1", "Демоны физики", "222.8"),
    ("2", "Случайные люди", "215.0"),
    ("3", "СУНЦ УрФУ", "203.8"),
    ("4", "школа Пифагора", "201.7"),
    ("5", "Кипящий лед", "197.5"),
    ("6", "Воронежская область", "190.6"),
    ("7", "Резонанс", "185.9"),
    ("8", "Регион-42", "180.8"),
    ("9", "ЛаНаТ", "180.2"),
    ("10", "БИ1", "175.1"),
    ("11", "гимназия 406", "166.3"),
    ("12", "Физтех и МАН", "165.5"),
    ("13", "Джем", "165.1"),
    ("14", "Изотопы", "163.0"),
    ("15", "СУНЦ МГУ", "159.2"),
    ("16", "БИ2", "158.5"),
    ("17", "Тверичи", "156.4"),
    ("18", "ФМЛ № 30", "152.0"),
    ("19", "Кимберлит", "136.3"),
    ("20", "Cooling", "120.5"),
]

LEAGUE_A = [
    ("1", "Демоны физики", "222.8"),
    ("2", "Случайные люди", "215.0"),
    ("3", "СУНЦ УрФУ", "203.8"),
    ("4", "школа Пифагора", "201.7"),
    ("5", "СУНЦ МГУ", "159.2"),
]

LEAGUE_B = [
    ("1", "Кипящий лед", "197.5"),
    ("2", "Воронежская область", "190.6"),
    ("3", "Резонанс", "185.9"),
    ("4", "Регион-42", "180.8"),
    ("5", "ЛаНаТ", "180.2"),
    ("6", "БИ1", "175.1"),
    ("7", "гимназия 406", "166.3"),
    ("8", "Физтех и МАН", "165.5"),
    ("9", "Джем", "165.1"),
    ("10", "Изотопы", "163.0"),
    ("11", "БИ2", "158.5"),
    ("12", "Тверичи", "156.4"),
    ("13", "ФМЛ № 30", "152.0"),
    ("14", "Кимберлит", "136.3"),
    ("15", "Cooling", "120.5"),
]

# Протокол финалВ / финал1 (Protokoly_39_RosTYuF.xlsx).
FINAL_A = [
    ("1", "Случайные люди", "43.50"),
    ("2", "СУНЦ УрФУ", "38.79"),
    ("3", "Демоны физики", "38.14"),
]

FINAL_B = [
    ("1", "Воронежская область", "36.83"),
    ("2", "Кипящий лед", "35.33"),
    ("3", "Резонанс", "29.58"),
]

# IYPT 2017, TSP.
IYPT_RANKING = [
    ("1", "Сингапур", "237.6"),
    ("2", "Китай", "210.5"),
    ("3", "Польша", "204.7"),
    ("4", "Венгрия", "204.0"),
    ("5", "Новая Зеландия", "201.0"),
    ("6", "Германия", "199.2"),
    ("7", "Китайский Тайбэй", "193.6"),
    ("8", "Бразилия", "189.8"),
    ("9", "Чехия", "189.6"),
    ("10", "Словакия", "185.8"),
    ("11", "Австрия", "184.4"),
    ("11", "Таиланд", "184.4"),
    ("13", "Швейцария", "182.0"),
    ("14", "Канада", "180.7"),
    ("15", "Корея", "178.8"),
    ("16", "Россия", "178.6"),
    ("17", "Беларусь", "173.1"),
    ("18", "Австралия", "172.4"),
    ("19", "Швеция", "169.6"),
    ("20", "Великобритания", "167.3"),
    ("21", "США", "165.6"),
    ("22", "Грузия", "165.0"),
    ("23", "Болгария", "161.1"),
    ("24", "Румыния", "153.9"),
    ("25", "Сербия", "143.3"),
    ("26", "Пакистан", "138.9"),
    ("27", "Украина", "138.3"),
    ("28", "Макао", "128.9"),
    ("29", "Иран", "127.0"),
    ("30", "Азербайджан", "94.1"),
]

IYPT_FINAL = [
    ("1", "Сингапур", "51.05"),
    ("2", "Китай", "43.75"),
    ("3", "Польша", "39.35"),
    ("4", "Венгрия", "38.5"),
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
    help = "Заполняет даты, город, таблицы, IYPT и фото сезона 2017."

    def handle(self, *args, **options):
        page = TournamentPage.objects.filter(year=YEAR).first()
        if not page:
            self.stderr.write("Страницы 2017 нет.")
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
                f"2017: общий {len(RANKING)}, высшая {len(LEAGUE_A)}, "
                f"первая {len(LEAGUE_B)}, финал высшей {len(FINAL_A)}, "
                f"финал первой {len(FINAL_B)}, IYPT рейтинг {len(IYPT_RANKING)}, "
                f"IYPT финал {len(IYPT_FINAL)}, фото {photo_count}, "
                f"оригинал {page.results_more_url or '—'}."
            )
        )
