from django.core.management.base import BaseCommand

from home.models import TournamentPage, season_title, year_to_roman


class Command(BaseCommand):
    help = "Обновляет римские номера и названия сезонов как на МТИ."

    def handle(self, *args, **options):
        count = 0
        for page in TournamentPage.objects.all().order_by("year"):
            roman = year_to_roman(page.year)
            title = season_title(page.year, roman)
            page.roman = roman
            page.title = title
            page.save()
            page.save_revision().publish()
            self.stdout.write(f"{page.year}: {title}")
            count += 1
        self.stdout.write(self.style.SUCCESS(f"Обновлено сезонов: {count}."))
