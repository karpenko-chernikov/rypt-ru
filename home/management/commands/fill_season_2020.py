from django.core.management.base import BaseCommand

from home.models import TournamentPage, TournamentResultRow

YEAR = 2020
CITY = "онлайн"
MORE_URL = "https://voronezh.iptnet.info/IPT_RYPT2020_ONLINE/ranking"
MORE_LABEL = "Оригинал"

IYPT_MORE_URL = ""
IYPT_MORE_LABEL = ""
IYPT_TEAM = """Состав сборной:
Росновская Екатерина
Семенов Дмитрий
Шаров Никита
Карпенко Олеся
Шинкаренко Роман

Сборная принимала участие в Международном турнире в онлайн-формате. По итогам турнира заняла 5 место (бронзовые медали)."""

# The Final — physics_fights/5, сумма.
FINAL = [
    ("1", "ЭйНШтейн", "40.36"),
    ("2", "План Б", "37.89"),
    ("3", "Лицей 84", "36.93"),
]

# Selective Fights Ranking — итог отборочных боёв.
RANKING = [
    ("1", "ЭйНШтейн", "156.80"),
    ("2", "Лицей 84", "152.90"),
    ("3", "План Б", "151.00"),
    ("4", "Кипящий лёд", "141.46"),
    ("5", "Сигма IQ 200", "120.26"),
    ("6", "Фобос", "119.90"),
    ("7", "Коты Шрёдингера", "113.51"),
    ("8", "Обдоряне", "101.00"),
    ("9", "Галактика", "93.75"),
]

# IYPT'2020 selective ranking (TSP).
IYPT_RANKING = [
    ("1", "Канада", "205.1"),
    ("2", "Китай", "201.8"),
    ("3", "Украина", "184.3"),
    ("4", "Грузия", "183.6"),
    ("5", "Россия", "180.8"),
    ("6", "Китайский Тайбэй", "179.6"),
    ("7", "Словакия", "177.0"),
    ("8", "Иран", "171.8"),
    ("9", "Венгрия", "163.6"),
    ("10", "Румыния", "147.7"),
    ("11", "Казахстан", "124.5"),
]

# Finals — IYPT'2020 (у Китая штраф −1.0 уже в итоге).
IYPT_FINAL = [
    ("1", "Канада", "42.0"),
    ("2", "Китай", "40.9"),
    ("3", "Украина", "37.9"),
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
    help = "Заполняет итоги, финал и IYPT сезона 2020 (онлайн)."

    def handle(self, *args, **options):
        page = TournamentPage.objects.filter(year=YEAR).first()
        if not page:
            self.stderr.write("Страницы 2020 нет.")
            return
        page.city = CITY
        page.date_start = None
        page.date_end = None
        page.results_more_url = MORE_URL
        page.results_more_label = MORE_LABEL
        page.iypt_team = IYPT_TEAM
        page.iypt_more_url = IYPT_MORE_URL
        page.iypt_more_label = IYPT_MORE_LABEL
        page.photo_album_url = ""
        page.save()
        page.ranking.all().delete()
        order = 0
        order = add_rows(page, TournamentResultRow.KIND_FINAL, FINAL, order)
        order = add_rows(page, TournamentResultRow.KIND_RANKING, RANKING, order)
        order = add_rows(page, TournamentResultRow.KIND_IYPT_RANKING, IYPT_RANKING, order)
        add_rows(page, TournamentResultRow.KIND_IYPT_FINAL, IYPT_FINAL, order)
        page.photos.all().delete()
        page.save_revision().publish()
        self.stdout.write(
            self.style.SUCCESS(
                f"2020: финал {len(FINAL)}, итог {len(RANKING)}, "
                f"IYPT рейтинг {len(IYPT_RANKING)}, IYPT финал {len(IYPT_FINAL)}."
            )
        )
