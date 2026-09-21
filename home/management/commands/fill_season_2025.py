import json
from datetime import date
from pathlib import Path

from django.core.management.base import BaseCommand

from home.models import TournamentPage, TournamentPhoto, TournamentResultRow

YEAR = 2025
CITY = "Обнинск"
START = date(2025, 3, 22)
END = date(2025, 3, 27)
MORE_URL = "https://docs.google.com/spreadsheets/d/1gH9OGgPY-DOocrEwnGKpjpuEXv4LoX7d7GVsmF7juDU/edit?gid=236229439#gid=236229439"
MORE_LABEL = "Оригинал"
PHOTO_ALBUMS = [
    "https://vk.ru/album-222342853_309165222",
    "https://vk.ru/album-222342853_309166101",
    "https://vk.ru/album-222342853_309166108",
    "https://vk.ru/album-222342853_309166118",
    "https://vk.ru/album-222342853_309166122",
    "https://vk.ru/album-222342853_309166133",
]
PHOTO_JSON = Path(__file__).with_name("season_2025_photos.json")

# Лист «Финал», сумма по убыванию.
FINAL = [
    ("1", "Хычины", "41.4"),
    ("2", "Бобры", "40.95"),
    ("3", "Физикон", "39.35"),
]

# Лист «Рейтинг» / итог отборочных, сумма по убыванию.
RANKING = [
    ("1", "Бобры", "213.1"),
    ("2", "Физикон", "195.8"),
    ("3", "Хычины", "193.9"),
    ("4", "МБХ", "176.2"),
    ("5", "ДИО-ГЕН", "171.5"),
    ("6", "Потенциал картошки", "166.8"),
    ("7", "Случайные люди", "153.1"),
    ("8", "Искра", "150.9"),
    ("9", "Млечный путь", "124.6"),
    ("10", "Тесла в ушанке", "118.4"),
    ("11", "Эксперимент", "115.1"),
    ("12", "Мирный атом", "103.4"),
]


class Command(BaseCommand):
    help = "Заполняет итоги, финал и фото сезона 2025."

    def handle(self, *args, **options):
        page = TournamentPage.objects.filter(year=YEAR).first()
        if not page:
            self.stderr.write("Страницы 2025 нет.")
            return
        page.city = CITY
        page.date_start = START
        page.date_end = END
        page.results_more_url = MORE_URL
        page.results_more_label = MORE_LABEL
        page.photo_album_url = "\n".join(PHOTO_ALBUMS)
        page.save()
        page.ranking.all().delete()
        order = 0
        for place, team, points in FINAL:
            TournamentResultRow.objects.create(
                page=page,
                kind=TournamentResultRow.KIND_FINAL,
                place=place,
                team=team,
                city="",
                points=points,
                sort_order=order,
            )
            order += 1
        for place, team, points in RANKING:
            TournamentResultRow.objects.create(
                page=page,
                kind=TournamentResultRow.KIND_RANKING,
                place=place,
                team=team,
                city="",
                points=points,
                sort_order=order,
            )
            order += 1
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
                f"2025: финал {len(FINAL)}, итог {len(RANKING)}, фото {photo_count}."
            )
        )
