from datetime import date

from django.core.management.base import BaseCommand

from home.models import TournamentLink, TournamentPage

YEAR = 2010
CITY = "Санкт-Петербург"
START = date(2010, 3, 21)
END = date(2010, 3, 27)
ARCHIVE_LABEL = "Архив rusypt.msu.ru"
ARCHIVE_URL = "http://rusypt.msu.ru/archive/tour2010/"

IYPT_TEAM = """Состав сборной — СУНЦ УрГУ-1 (Екатеринбург).

Победитель высшей лиги направлялся на XXIII Международный Турнир Юных Физиков в Вене (Австрия)."""


class Command(BaseCommand):
    help = "Заполняет город, даты и IYPT сезона 2010 (таблиц в открытом доступе нет)."

    def handle(self, *args, **options):
        page = TournamentPage.objects.filter(year=YEAR).first()
        if not page:
            self.stderr.write("Страницы 2010 нет.")
            return
        page.city = CITY
        page.date_start = START
        page.date_end = END
        # Таблиц нет — вкладку «Результаты» не открываем; ссылка на архив в материалах.
        page.results_more_url = ""
        page.results_more_label = ""
        page.iypt_team = IYPT_TEAM
        page.iypt_more_url = ""
        page.iypt_more_label = ""
        page.photo_album_url = ""
        page.save()
        page.ranking.all().delete()
        page.photos.all().delete()
        page.links.filter(url=ARCHIVE_URL).delete()
        TournamentLink.objects.create(
            page=page,
            kind=TournamentLink.REPORT,
            title=ARCHIVE_LABEL,
            url=ARCHIVE_URL,
            sort_order=0,
        )
        page.save_revision().publish()
        self.stdout.write(
            self.style.SUCCESS(
                f"2010: {page.city}, {page.date_start} — {page.date_end}."
            )
        )
