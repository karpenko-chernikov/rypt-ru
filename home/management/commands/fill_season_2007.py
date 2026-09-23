import json
from pathlib import Path

from django.core.management.base import BaseCommand

from home.models import TournamentPage, TournamentPhoto

YEAR = 2007
PHOTO_ALBUM = "https://vk.ru/album-44049348_172722442"
PHOTO_JSON = Path(__file__).with_name("season_2007_photos.json")


class Command(BaseCommand):
    help = "Заполняет фото сезона 2007."

    def handle(self, *args, **options):
        page = TournamentPage.objects.filter(year=YEAR).first()
        if not page:
            self.stderr.write("Страницы 2007 нет.")
            return
        page.photo_album_url = PHOTO_ALBUM
        page.save()
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
        self.stdout.write(self.style.SUCCESS(f"2007: фото {photo_count}."))
