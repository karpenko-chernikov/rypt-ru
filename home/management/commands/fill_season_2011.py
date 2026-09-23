from django.core.management.base import BaseCommand

from home.models import TournamentPage, TournamentResultRow

YEAR = 2011
MORE_LABEL = "Оригинал"
MORE_URL = (
    "https://web.archive.org/web/20140702101144/"
    "http://rusypt.msu.ru/archive/tour2011/winners-command.shtml"
)

# Места из протокола (баллов нет).
LEAGUE_A = [
    ("1", "Лицей 130", "Екатеринбург", ""),
    ("2", "СУНЦ УрГУ-1", "Екатеринбург", ""),
    ("2", "АГ СПбГУ", "Санкт-Петербург", ""),
    ("3", "СУНЦ МГУ", "Москва", ""),
    ("3", "СУНЦ УрГУ-2", "Екатеринбург", ""),
    ("3", "СУНЦ НГУ", "Новосибирск", ""),
]

LEAGUE_B = [
    ("1", "Воронеж", "Воронеж", ""),
    ("2", "Вятская гуманитарная гимназия", "Киров", ""),
    ("2", "Державинский лицей", "Петрозаводск", ""),
    ("3", "Качканар", "Качканар", ""),
    ("", "Пульсар", "Воронеж", ""),
    ("", "Факториал", "Воронеж", ""),
    ("", "Лицей №6", "Горно-Алтайск", ""),
    ("", "СОШ №65", "Тюмень", ""),
]


def add_rows(page, kind, rows, order):
    for place, team, city, points in rows:
        TournamentResultRow.objects.create(
            page=page,
            kind=kind,
            place=place,
            team=team,
            city=city,
            points=points,
            sort_order=order,
        )
        order += 1
    return order


class Command(BaseCommand):
    help = "Заполняет лиги сезона 2011 по протоколу командного зачёта."

    def handle(self, *args, **options):
        page = TournamentPage.objects.filter(year=YEAR).first()
        if not page:
            self.stderr.write("Страницы 2011 нет.")
            return
        page.results_more_url = MORE_URL
        page.results_more_label = MORE_LABEL
        page.iypt_team = ""
        page.iypt_more_url = ""
        page.iypt_more_label = ""
        page.photo_album_url = ""
        page.save()
        page.ranking.all().delete()
        order = 0
        order = add_rows(page, TournamentResultRow.KIND_LEAGUE_A, LEAGUE_A, order)
        add_rows(page, TournamentResultRow.KIND_LEAGUE_B, LEAGUE_B, order)
        page.photos.all().delete()
        page.save_revision().publish()
        self.stdout.write(
            self.style.SUCCESS(
                f"2011: высшая {len(LEAGUE_A)}, первая {len(LEAGUE_B)}."
            )
        )
