import json
from pathlib import Path

from django.core.management.base import BaseCommand

from home.models import HomePage, TournamentIndexPage, TournamentPage, TournamentProblem, season_title, year_to_roman

CURRENT_YEAR = 2027
DATA = Path(__file__).with_name("season_problems.json")


class Command(BaseCommand):
    help = "Создаёт страницы сезонов и заливает списки задач."

    def handle(self, *args, **options):
        home = HomePage.objects.first()
        index = TournamentIndexPage.objects.child_of(home).first() if home else None
        if not index:
            self.stderr.write("Сначала сделайте seed_site.")
            return

        payload = json.loads(DATA.read_text(encoding="utf-8"))
        years = sorted((int(year) for year in payload), reverse=True)
        for year in years:
            problems = payload.get(str(year), [])
            if not problems:
                self.stderr.write(f"{year}: задачи не нашлись.")
                continue
            page = TournamentPage.objects.child_of(index).filter(slug=str(year)).first()
            roman = year_to_roman(year)
            title = season_title(year, roman)
            if not page:
                page = TournamentPage(
                    title=title,
                    slug=str(year),
                    year=year,
                    roman=roman,
                    is_current=(year == CURRENT_YEAR),
                )
                index.add_child(instance=page)
            else:
                page.title = title
                page.year = year
                page.roman = roman
                page.is_current = year == CURRENT_YEAR
            page.save_revision().publish()
            page.problems.all().delete()
            for item in problems:
                TournamentProblem.objects.create(
                    page=page,
                    number=item["number"],
                    title=item["title"],
                    statement=item["statement"],
                    sort_order=item["number"] - 1,
                )
            self.stdout.write(f"{year}: {len(problems)} задач.")

        self.stdout.write(self.style.SUCCESS("Сезоны обновлены."))
