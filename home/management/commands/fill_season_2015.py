from datetime import date

from django.core.management.base import BaseCommand

from home.models import TournamentPage, TournamentResultRow

YEAR = 2015
CITY = "Екатеринбург"
START = date(2015, 3, 21)
END = date(2015, 3, 27)
MORE_LABEL = "Оригинал"

IYPT_MORE_URL = ""
IYPT_MORE_LABEL = ""
IYPT_TEAM = """Состав сборной (участники из Новосибирска):
Матюнин Виталий
Янко Павел
Сибиряков Николай
Захаров Степан
Буданцев Алексей

Сборная принимала участие в Международном турнире. По итогам турнира заняла 7 место (серебряные медали)."""

# Отборочные: сумма по 5 боям.
RANKING = [
    ("1", "Случайные люди", "221.4"),
    ("2", "Школа Пифагора", "219.7"),
    ("3", "ИнжеНЭТИК", "205.6"),
    ("4", "Винегрет", "204.7"),
    ("5", "Екатеринбург, 130", "204.5"),
    ("6", "СУНЦ УрФУ", "202.9"),
    ("7", "Кипящий лёд", "199.6"),
    ("8", "ВМФ", "198.9"),
    ("9", "Амплитуда", "188.9"),
    ("10", "Мишки", "183.2"),
    ("11", "Брейн-индукция", "181.7"),
    ("12", "Млечный путь", "181.3"),
    ("13", "Ланат", "178.7"),
    ("14", "Регион-42", "178.0"),
    ("15", "Пушкин, 406", "177.1"),
    ("16", "12+13", "170.2"),
    ("17", "Северо-запад", "166.2"),
]

LEAGUE_A = [
    ("1", "Случайные люди", "221.4"),
    ("2", "Школа Пифагора", "219.7"),
    ("3", "ИнжеНЭТИК", "205.6"),
    ("4", "Винегрет", "204.7"),
    ("5", "Екатеринбург, 130", "204.5"),
    ("6", "СУНЦ УрФУ", "202.9"),
    ("7", "Северо-запад", "166.2"),
]

LEAGUE_B = [
    ("1", "Кипящий лёд", "199.6"),
    ("2", "ВМФ", "198.9"),
    ("3", "Амплитуда", "188.9"),
    ("4", "Мишки", "183.2"),
    ("5", "Брейн-индукция", "181.7"),
    ("6", "Млечный путь", "181.3"),
    ("7", "Ланат", "178.7"),
    ("8", "Регион-42", "178.0"),
    ("9", "Пушкин, 406", "177.1"),
    ("10", "12+13", "170.2"),
]

FINAL_A = [
    ("1", "Школа Пифагора", "44.55"),
    ("2", "Случайные люди", "43.1"),
    ("3", "ИнжеНЭТИК", "42.8"),
]

FINAL_B = [
    ("1", "ВМФ", "36.32"),
    ("2", "Амплитуда", "36.14"),
    ("3", "Кипящий лёд", "35.73"),
]

IYPT_RANKING = [
    ("1", "Сингапур", "215.7"),
    ("2", "Польша", "200.0"),
    ("3", "Китай", "194.9"),
    ("4", "Словакия", "190.5"),
    ("5", "Бразилия", "187.8"),
    ("6", "Болгария", "186.6"),
    ("7", "Россия", "186.2"),
    ("8", "Южная Корея", "186.1"),
    ("9", "Венгрия", "181.5"),
    ("10", "Новая Зеландия", "181.3"),
    ("11", "Швейцария", "178.6"),
    ("12", "Тайвань", "175.3"),
    ("13", "Германия", "175.0"),
    ("14", "Великобритания", "174.5"),
    ("15", "Швеция", "173.9"),
    ("16", "Австрия", "170.9"),
    ("17", "Беларусь", "169.3"),
    ("18", "Украина", "168.7"),
    ("19", "Австралия", "156.1"),
    ("20", "Румыния", "153.5"),
    ("21", "Чехия", "152.9"),
    ("22", "Иран", "152.5"),
    ("23", "США", "150.6"),
    ("24", "Таиланд", "142.4"),
    ("25", "Макао", "136.8"),
    ("26", "Нигерия", "116.2"),
    ("27", "Кения", "94.4"),
]

IYPT_FINAL = [
    ("1", "Сингапур", ""),
    ("2", "Польша", ""),
    ("3", "Китай", ""),
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
    help = "Заполняет даты, город, таблицы и IYPT сезона 2015."

    def handle(self, *args, **options):
        page = TournamentPage.objects.filter(year=YEAR).first()
        if not page:
            self.stderr.write("Страницы 2015 нет.")
            return
        page.city = CITY
        page.date_start = START
        page.date_end = END
        page.results_more_url = ""
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
        order = add_rows(page, TournamentResultRow.KIND_LEAGUE_B, LEAGUE_B, order)
        order = add_rows(page, TournamentResultRow.KIND_FINAL, FINAL_A, order)
        order = add_rows(page, TournamentResultRow.KIND_FINAL_B, FINAL_B, order)
        order = add_rows(page, TournamentResultRow.KIND_IYPT_RANKING, IYPT_RANKING, order)
        add_rows(page, TournamentResultRow.KIND_IYPT_FINAL, IYPT_FINAL, order)
        page.photos.all().delete()
        page.save_revision().publish()
        self.stdout.write(
            self.style.SUCCESS(
                f"2015: общий {len(RANKING)}, высшая {len(LEAGUE_A)}, "
                f"первая {len(LEAGUE_B)}, финал высшей {len(FINAL_A)}, "
                f"финал первой {len(FINAL_B)}, IYPT рейтинг {len(IYPT_RANKING)}, "
                f"IYPT финал {len(IYPT_FINAL)}."
            )
        )
