import json
from datetime import date
from pathlib import Path

from django.core.management.base import BaseCommand

from home.models import TournamentPage, TournamentPhoto

YEAR = 2013
CITY = "Москва"
START = date(2013, 3, 25)
END = date(2013, 3, 30)
PHOTO_ALBUM = "https://vk.ru/album-44049348_172719908"
PHOTO_JSON = Path(__file__).with_name("season_2013_photos.json")


class Command(BaseCommand):
    help = "Заполняет город, даты и фото сезона 2013."

    def handle(self, *args, **options):
        page = TournamentPage.objects.filter(year=YEAR).first()
        if not page:
            self.stderr.write("Страницы 2013 нет.")
            return
        page.city = CITY
        page.date_start = START
        page.date_end = END
        page.results_more_url = ""
        page.results_more_label = ""
        page.iypt_team = ""
        page.iypt_more_url = ""
        page.iypt_more_label = ""
        page.photo_album_url = PHOTO_ALBUM
        page.save()
        page.ranking.all().delete()
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
                f"2013: {page.city}, {page.date_start} — {page.date_end}, "
                f"фото {photo_count}."
            )
        )
