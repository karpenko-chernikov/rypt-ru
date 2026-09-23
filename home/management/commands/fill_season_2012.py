import shutil
from datetime import date
from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand

from home.models import TournamentPage, TournamentResultRow

YEAR = 2012
CITY = "Екатеринбург"
START = date(2012, 3, 25)
END = date(2012, 3, 31)
MORE_LABEL = "Оригинал"
MORE_FILE = Path(__file__).with_name("season_files") / "command2012.xls"
MORE_MEDIA_REL = Path("documents") / "2012" / "command2012.xls"

IYPT_TEAM = """Состав сборной:
Матюнин Вячеслав
Сорочихина Юлия
Курилович Влад
Курилович Павел
Кротов Алексей

Сборная принимала участие в Международном турнире. По итогам турнира заняла 12 место (бронзовые медали)."""

# XXV IYPT, Бад-Заульгау: сумма после пяти отборочных боёв.
IYPT_RANKING = [
    ("1", "Южная Корея", "227.1"),
    ("2", "Сингапур", "216.8"),
    ("3", "Иран", "205.1"),
    ("4", "Белоруссия", "197.0"),
    ("5", "Германия", "196.9"),
    ("6", "Тайвань", "196.7"),
    ("7", "Швейцария", "194.0"),
    ("8", "Австрия", "191.9"),
    ("9", "Словакия", "190.1"),
    ("10", "Бразилия", "187.9"),
    ("11", "Грузия", "184.2"),
    ("12", "Россия", "177.3"),
    ("13", "Новая Зеландия", "174.0"),
    ("14", "Франция", "166.7"),
    ("15", "Швеция", "165.7"),
    ("16", "Болгария", "163.8"),
    ("17", "Австралия", "163.2"),
    ("18", "Китай", "162.4"),
    ("19", "Польша", "161.5"),
    ("20", "Великобритания", "158.0"),
    ("21", "Чехия", "154.2"),
    ("22", "Таиланд", "139.0"),
    ("23", "Венгрия", "132.5"),
    ("24", "Индонезия", "128.5"),
    ("25", "Кения", "119.7"),
    ("26", "Словения", "114.6"),
    ("27", "Нидерланды", "98.6"),
    ("28", "Нигерия", "90.1"),
]

IYPT_FINAL = [
    ("1", "Южная Корея", "48.7"),
    ("2", "Иран", "46.9"),
    ("3", "Сингапур", "46.7"),
]

# Баллы пяти отборочных боёв.
RANKING = [
    ("1", "СУНЦ УрФУ-1", "251.4"),
    ("2", "Новосибирск, Пифагор", "237.2"),
    ("3", "Воронеж, сборная", "232.1"),
    ("4", "СУНЦ МГУ", "231.2"),
    ("5", "Екатеринбург, 130", "224.7"),
    ("6", "Киров-1", "219.8"),
    ("7", "Киров-2", "217.0"),
    ("8", "Качканар", "211.3"),
    ("9", "СУНЦ УрФУ-2", "209.5"),
    ("10", "СУНЦ НГУ", "207.0"),
    ("11", "АГ СПбГУ", "200.2"),
    ("12", "Горно-Алтайск", "181.9"),
    ("13", "Чебоксары, 53", "175.1"),
    ("14", "Воронеж, Факториал", "174.1"),
    ("15", "Чебоксары, 11", "171.3"),
    ("16", "Салехард", "162.0"),
    ("17", "Москва, Бобрята", "161.6"),
    ("18", "Чебоксары, 9", "158.4"),
]

LEAGUE_A = [
    ("1", "СУНЦ УрФУ-1", "251.4"),
    ("2", "Новосибирск, Пифагор", "237.2"),
    ("3", "Воронеж, сборная", "232.1"),
    ("4", "СУНЦ МГУ", "231.2"),
    ("5", "Екатеринбург, 130", "224.7"),
    ("6", "СУНЦ УрФУ-2", "209.5"),
    ("7", "СУНЦ НГУ", "207.0"),
    ("8", "АГ СПбГУ", "200.2"),
    ("9", "Москва, Бобрята", "161.6"),
]

LEAGUE_B = [
    ("1", "Киров-1", "219.8"),
    ("2", "Киров-2", "217.0"),
    ("3", "Качканар", "211.3"),
    ("4", "Горно-Алтайск", "181.9"),
    ("5", "Чебоксары, 53", "175.1"),
    ("6", "Воронеж, Факториал", "174.1"),
    ("7", "Чебоксары, 11", "171.3"),
    ("8", "Салехард", "162.0"),
    ("9", "Чебоксары, 9", "158.4"),
]

FINAL_A = [
    ("1", "СУНЦ УрФУ-1", "47.59"),
    ("2", "Новосибирск, Пифагор", "44.73"),
    ("3", "Воронеж, сборная", "40.5"),
]

FINAL_B = [
    ("1", "Киров-1", "41.8"),
    ("2", "Киров-2", "40.04"),
    ("3", "Качканар", "39.5"),
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
    help = "Заполняет таблицы и IYPT сезона 2012 по command2012.xls."

    def handle(self, *args, **options):
        page = TournamentPage.objects.filter(year=YEAR).first()
        if not page:
            self.stderr.write("Страницы 2012 нет.")
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
        page.iypt_more_url = ""
        page.iypt_more_label = ""
        page.photo_album_url = ""
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
        page.save_revision().publish()
        self.stdout.write(
            self.style.SUCCESS(
                f"2012: {page.city}, {page.date_start} — {page.date_end}, "
                f"общий {len(RANKING)}, высшая {len(LEAGUE_A)}, "
                f"первая {len(LEAGUE_B)}, финалы {len(FINAL_A)}/{len(FINAL_B)}, "
                f"IYPT {len(IYPT_RANKING)}/{len(IYPT_FINAL)}, "
                f"оригинал {page.results_more_url or '—'}."
            )
        )
