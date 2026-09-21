import json
from datetime import date
from pathlib import Path

from django.core.management.base import BaseCommand

from home.models import TournamentPage, TournamentPhoto, TournamentResultRow

YEAR = 2026
CITY = "Новосибирск"
START = date(2026, 3, 27)
END = date(2026, 4, 1)
MORE_URL = "https://mtiyt.ru/tournaments/8/results/team"
MORE_LABEL = "Оригинал"
PHOTO_ALBUM = "https://vk.ru/album-222342853_313083741"
PHOTO_JSON = Path(__file__).with_name("season_2026_photos.json")

FINAL = [
    ("1", "Бобры", "43.7"),
    ("2", "ФизиКон1", "41.2"),
    ("3", "Могло быть хуже", "37.6"),
]

# Итоговые суммы с командной таблицы, без колонок боёв.
RANKING = [
    ("1", "Бобры", "229"),
    ("2", "ФизиКон1", "210"),
    ("3", "Могло быть хуже", "188.6"),
    ("4", "Случайные люди в ДИО-ГЕНе", "171.6"),
    ("5", "ФизиКон2", "162.2"),
    ("6", "Атом", "161.1"),
    ("7", "Тридцатка", "143.6"),
    ("8", "Ом", "142.8"),
    ("9", "Без двух двенадцать", "141.4"),
    ("10", "Делайте выводы", "133.4"),
    ("11", "Коты Шрёдингера", "131.4"),
    ("12", "Physic's", "123.4"),
    ("13", "ИскРа", "120.7"),
]


class Command(BaseCommand):
    help = "Заполняет итоги, финал и фото сезона 2026."

    def handle(self, *args, **options):
        page = TournamentPage.objects.filter(year=YEAR).first()
        if not page:
            self.stderr.write("Страницы 2026 нет.")
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
                        sort_order=index,
                    )
                    for index, shot in enumerate(shots)
                ]
            )
            photo_count = len(shots)
        page.save_revision().publish()
        self.stdout.write(
            self.style.SUCCESS(
                f"2026: финал {len(FINAL)}, итог {len(RANKING)}, фото {photo_count}."
            )
        )
