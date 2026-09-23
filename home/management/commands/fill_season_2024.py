import json
from datetime import date
from pathlib import Path

from django.core.management.base import BaseCommand

from home.models import TournamentPage, TournamentPhoto, TournamentResultRow

YEAR = 2024
CITY = "Москва"
START = date(2024, 6, 21)
END = date(2024, 6, 25)
MORE_URL = (
    "https://docs.google.com/spreadsheets/d/"
    "1zzlMd0cIaAUgLFoyYRwOPyvOSRz2cj4c9hdbbJ7jKbo/edit?gid=236229439#gid=236229439"
)
MORE_LABEL = "Оригинал"
PHOTO_ALBUM = "https://vk.ru/album-44049348_303233921"
PHOTO_JSON = Path(__file__).with_name("season_2024_photos.json")

# Лист «Результаты», Итого по убыванию.
RANKING = [
    ("1", "Бобры", "192.2"),
    ("2", "Буравчики", "191.7"),
    ("3", "ИнжеНЭТИк", "172.8"),
    ("4", "СУНЦ-1", "160.9"),
    ("5", "Физикон", "159.9"),
    ("6", "Это просто волшебно", "159.6"),
    ("7", "Театр юного физика", "156.8"),
    ("8", "Могло быть хуже", "152.8"),
    ("9", "Хычины", "150"),
    ("10", "Боброгены", "133.8"),
    ("11", "ФМЛ 239", "113.5"),
    ("12", "НИИ", "101.1"),
    ("13", "МАН", "94.7"),
]

LEAGUE_A = [
    ("1", "Бобры", "192.2"),
    ("2", "ИнжеНЭТИк", "172.8"),
    ("3", "СУНЦ-1", "160.9"),
    ("4", "Могло быть хуже", "152.8"),
    ("5", "Хычины", "150"),
]

LEAGUE_B = [
    ("1", "Буравчики", "191.7"),
    ("2", "Физикон", "159.9"),
    ("3", "Это просто волшебно", "159.6"),
    ("4", "Театр юного физика", "156.8"),
    ("5", "Боброгены", "133.8"),
    ("6", "ФМЛ 239", "113.5"),
    ("7", "НИИ", "101.1"),
    ("8", "МАН", "94.7"),
]

# Лист «Финал»: сумма 3×Д + 2×О.
FINAL = [
    ("1", "Буравчики", "32.05"),
    ("2", "ИнжеНЭТИк", "30.64"),
    ("3", "Бобры", "27.50"),
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
    help = "Заполняет даты, город, таблицы результатов и фото сезона 2024."

    def handle(self, *args, **options):
        page = TournamentPage.objects.filter(year=YEAR).first()
        if not page:
            self.stderr.write("Страницы 2024 нет.")
            return
        page.city = CITY
        page.date_start = START
        page.date_end = END
        page.results_more_url = MORE_URL
        page.results_more_label = MORE_LABEL
        page.photo_album_url = PHOTO_ALBUM
        page.save()
        page.ranking.all().delete()
        order = 0
        order = add_rows(page, TournamentResultRow.KIND_RANKING, RANKING, order)
        order = add_rows(page, TournamentResultRow.KIND_LEAGUE_A, LEAGUE_A, order)
        order = add_rows(page, TournamentResultRow.KIND_LEAGUE_B, LEAGUE_B, order)
        add_rows(page, TournamentResultRow.KIND_FINAL, FINAL, order)
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
                f"2024: общий {len(RANKING)}, высшая {len(LEAGUE_A)}, "
                f"первая {len(LEAGUE_B)}, финал {len(FINAL)}, фото {photo_count}."
            )
        )
