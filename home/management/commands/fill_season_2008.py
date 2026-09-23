from datetime import date

from django.core.management.base import BaseCommand

from home.models import TournamentPage, TournamentResultRow

YEAR = 2008
CITY = "Москва"
START = date(2008, 3, 16)
END = date(2008, 3, 22)
MORE_LABEL = "Оригинал"
MORE_URL = (
    "https://web.archive.org/web/20131107041540/"
    "http://www.rusypt.msu.ru/archive/tour2008.shtml"
)

IYPT_MORE_URL = ""
IYPT_MORE_LABEL = ""
IYPT_TEAM = """Состав сборной (СУНЦ УрГУ-2, Екатеринбург):
Есин Александр
Шилкин Даниил
Черепанов Павел
Орехов Всеволод
Почечуев Матвей

Сборная была направлена на XXI Международный Турнир Юных Физиков в Трогире (Хорватия), но по техническим причинам не явилась на турнир."""

# Итоговый протокол командного зачёта (лист «РЕЗУЛЬТАТЫ»: 4 боя + ИТОГ).
RANKING = [
    ("1", "СУНЦ УрГУ-2", "Екатеринбург", "183.32"),
    ("2", "АГ СПбГУ-1", "Санкт-Петербург", "176.83"),
    ("3", "Лицей 130", "Екатеринбург", "172.43"),
    ("4", "Качканар", "Качканар", "169.41"),
    ("5", "СУНЦ УрГУ-1", "Екатеринбург", "167.00"),
    ("6", "СУНЦ МГУ", "Москва", "163.15"),
    ("7", "Пушкин", "Санкт-Петербург", "158.25"),
    ("8", "АГ СПбГУ-2", "Санкт-Петербург", "156.61"),
    ("9", "Лицей 30", "Санкт-Петербург", "156.08"),
    ("10", "Лесной", "Лесной", "151.48"),
    ("11", "Лицей 239", "Санкт-Петербург", "139.40"),
    ("12", "Ставрополь", "Ставрополь", "139.10"),
    ("13", "Воронеж", "Воронеж", "131.17"),
    ("14", "Арзамас", "Арзамас", "123.79"),
    ("15", "Великие Луки", "Великие Луки", "112.97"),
    ("16", "Лицей 1580", "Москва", "107.92"),
    ("17", "Заречный", "Заречный", "99.61"),
]

LEAGUE_A = [
    ("1", "СУНЦ УрГУ-2", "Екатеринбург", "183.32"),
    ("2", "АГ СПбГУ-1", "Санкт-Петербург", "176.83"),
    ("3", "Лицей 130", "Екатеринбург", "172.43"),
    ("4", "СУНЦ УрГУ-1", "Екатеринбург", "167.00"),
    ("5", "СУНЦ МГУ", "Москва", "163.15"),
    ("6", "АГ СПбГУ-2", "Санкт-Петербург", "156.61"),
    ("7", "Лицей 30", "Санкт-Петербург", "156.08"),
    ("8", "Лицей 239", "Санкт-Петербург", "139.40"),
]

LEAGUE_B = [
    ("1", "Качканар", "Качканар", "169.41"),
    ("2", "Пушкин", "Санкт-Петербург", "158.25"),
    ("3", "Лесной", "Лесной", "151.48"),
    ("4", "Ставрополь", "Ставрополь", "139.10"),
    ("5", "Воронеж", "Воронеж", "131.17"),
    ("6", "Арзамас", "Арзамас", "123.79"),
    ("7", "Великие Луки", "Великие Луки", "112.97"),
    ("8", "Лицей 1580", "Москва", "107.92"),
    ("9", "Заречный", "Заречный", "99.61"),
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
    help = "Заполняет даты, город, общий рейтинг, лиги и IYPT сезона 2008."

    def handle(self, *args, **options):
        page = TournamentPage.objects.filter(year=YEAR).first()
        if not page:
            self.stderr.write("Страницы 2008 нет.")
            return
        page.city = CITY
        page.date_start = START
        page.date_end = END
        page.results_more_url = MORE_URL
        page.results_more_label = MORE_LABEL
        page.iypt_team = IYPT_TEAM
        page.iypt_more_url = IYPT_MORE_URL
        page.iypt_more_label = IYPT_MORE_LABEL
        page.photo_album_url = ""
        page.save()
        page.ranking.all().delete()
        order = 0
        order = add_rows(page, TournamentResultRow.KIND_RANKING, RANKING, order)
        order = add_rows(page, TournamentResultRow.KIND_LEAGUE_A, LEAGUE_A, order)
        add_rows(page, TournamentResultRow.KIND_LEAGUE_B, LEAGUE_B, order)
        page.photos.all().delete()
        page.save_revision().publish()
        self.stdout.write(
            self.style.SUCCESS(
                f"2008: {page.city}, {page.date_start} — {page.date_end}, "
                f"общий {len(RANKING)}, высшая {len(LEAGUE_A)}, "
                f"первая {len(LEAGUE_B)}, оригинал {page.results_more_url}."
            )
        )
