"""Заполняет сезон 1990: результаты физбоев (без финала) + IYPT + скан заданий финала.

Источник результатов: архив фонда, папка 29, лист 50.
Место: МЦ «Олимпиец», Москва.
Первая цифра в колонках I–IV — место в бою (регламент того времени).
Пробел между Новгородом и Барнаулом на скане — смысл неизвестен.
Задания финала — отдельный скан (рисунки остаются на скане).
"""

from pathlib import Path

from django.core.files.images import ImageFile
from django.core.management.base import BaseCommand
from wagtail.images.models import Image

from home.models import TournamentPage, TournamentProblemScan, TournamentResultRow

YEAR = 1990
CITY = "Москва, МЦ «Олимпиец»"
MORE_LABEL = "Оригинал (архив фонда, папка 29, лист 50)"
MORE_URL = "/static/docs/results/1990-rezultaty-fizboev.jpg"
FINAL_PROBLEMS_STATIC = Path("rypt/static/docs/problems/1990-zadaniya-finala.jpg")
FINAL_SCAN_TITLE = "ТЮФ 1990 задания финала"
FINAL_SCAN_CAPTION = "Первоисточник: архив фонда, папка 29, лист 252"
IYPT_MORE_URL = "https://archive.iypt.org/factsheets/"
IYPT_MORE_LABEL = "Оригинал"

IYPT_TEAM = """На III IYPT (7–14 июня 1990) выступали команды МФТИ и Риги в изменённых составах.

Обе команды вышли в финал 12.06.1990."""

# III IYPT, отборочные: порядок по сумме мест (регламент), баллы — TSP.
IYPT_RANKING = [
    ("1", "Рига", "114.4"),
    ("2", "Нидерланды", "107.6"),
    ("3", "МФТИ", "109.7"),
    ("4", "Венгрия", "107.3"),
    ("5", "Чехословакия", "104.1"),
    ("6", "Польша", "100.5"),
]

# Финал 12.06.1990.
IYPT_FINAL = [
    ("1", "МФТИ", "26.7"),
    ("2", "Рига", "25.8"),
    ("3", "Нидерланды", "22.4"),
]

# Расшифровка скана «РЕЗУЛЬТАТЫ ФИЗБОЕВ.»
# fights: (место_в_бою, балл) для боёв I–IV; place_sum / score — «Сумма».
# mark — рукописная пометка справа (Т / Ю / Ф), смысл для нац. таблицы не зафиксирован.
FIGHTS = [
    {
        "team": "ФМШ № 18",
        "fights": [(1, "43.17"), (1, "49.4"), (1, "43.14"), (1, "44.16")],
        "place_sum": 4,
        "score": "179.87",
        "mark": "Т",
        "block": "top",
    },
    {
        "team": "Рига",
        "fights": [(1, "47.33"), (2, "42.5"), (1, "51.5"), (1, "43.83")],
        "place_sum": 5,
        "score": "185.16",
        "mark": "Т",
        "block": "top",
    },
    {
        "team": "ФМШ № 542",
        "fights": [(1, "49.2"), (1, "40"), (2, "37.83"), (1, "47.0")],
        "place_sum": 5,
        "score": "174.03",
        "mark": "Т",
        "block": "top",
    },
    {
        "team": "Одесса",
        "fights": [(1, "47.75"), (1, "33.67"), (2, "48.5"), (2, "46.0")],
        "place_sum": 6,
        "score": "175.92",
        "mark": "Т",
        "block": "top",
    },
    {
        "team": "Запорожье",
        "fights": [(1, "36.83"), (1, "40.25"), (2, "37.5"), (2, "37.7")],
        "place_sum": 6,
        "score": "152.28",
        "mark": "Т",
        "block": "top",
    },
    {
        "team": "Свердловск",
        "fights": [(2, "36.83"), (1, "44.5"), (1, "40.17"), (3, "36.33")],
        "place_sum": 7,
        "score": "157.83",
        "mark": "Т",
        "block": "top",
    },
    {
        "team": "Красноярск",
        "fights": [(2, "34.25"), (2, "38.4"), (1, "38.5"), (2, "43.17")],
        "place_sum": 7,
        "score": "154.32",
        "mark": "Т",
        "block": "top",
    },
    {
        "team": "Казахстан",
        "fights": [(2, "44.2"), (2, "38.55"), (1, "40.4"), (3, "40.5")],
        "place_sum": 8,
        "score": "163.65",
        "mark": "Ю",
        "block": "top",
    },
    {
        "team": "Новгород",
        "fights": [(1, "42"), (2, "35.8"), (2, "43.0"), (3, "37.0")],
        "place_sum": 8,
        "score": "157.80",
        "mark": "Ю",
        "block": "top",
    },
    # На скане здесь большой вертикальный пробел (смысл неизвестен).
    {
        "team": "Барнаул",
        "fights": [(2, "33.66"), (1, "32.2"), (2, "32.8"), (1, "38.83")],
        "place_sum": 6,
        "score": "137.49",
        "mark": "Ф",
        "block": "bottom",
    },
    {
        "team": "Молдавия",
        "fights": [(3, "28.83"), (1, "37"), (1, "39.57"), (2, "32.4")],
        "place_sum": 7,
        "score": "137.80",
        "mark": "Ф",
        "block": "bottom",
    },
    {
        "team": "Туркмения",
        "fights": [(2, "33.75"), (2, "33.6"), (2, "29.17"), (1, "30.8")],
        "place_sum": 7,
        "score": "127.32",
        "mark": "Ф",
        "block": "bottom",
    },
    {
        "team": "Сборная 1",
        "fights": [(2, "40.67"), (2, "32.33"), (1, "38.33"), (1, "44.2")],
        "place_sum": 8,
        "score": "155.53",
        "mark": "Ю",
        "block": "bottom",
    },
    {
        "team": "Мишкино",
        "fights": [(1, "31.16"), (2, "30.8"), (3, "29.71"), (3, "28.2")],
        "place_sum": 9,
        "score": "119.87",
        "mark": "Ф",
        "block": "bottom",
    },
    {
        "team": "Сборная 2",
        "fights": [(3, "33"), (3, "35.5"), (3, "31.5"), (1, "33.8")],
        "place_sum": 10,
        "score": "133.80",
        "mark": "Ф",
        "block": "bottom",
    },
    {
        "team": "Норильск",
        "fights": [(2, "25.67"), (3, "25.2"), (3, "24.84"), (2, "26.32")],
        "place_sum": 10,
        "score": "102.03",
        "mark": "Ф",
        "block": "bottom",
    },
    {
        "team": "Симферополь",
        "fights": [(3, "33.33"), (3, "30.8"), (3, "27.7"), (2, "43.2")],
        "place_sum": 11,
        "score": "135.03",
        "mark": "Ф",
        "block": "bottom",
    },
    {
        "team": "Тбилиси",
        "fights": [(3, "35"), (3, "29.6"), (3, "31.28"), (3, "39.8")],
        "place_sum": 12,
        "score": "135.68",
        "mark": "Ф",
        "block": "bottom",
    },
    {
        "team": "Узбекистан",
        "fights": [(3, "19.75"), (3, "26.6"), (2, "32.57"), (2, "29.2")],
        "place_sum": 12,
        "score": "108.12",
        "mark": "",
        "block": "bottom",
    },
    {
        "team": "Якутия",
        "fights": [(3, "25.16"), (3, "21.8"), (3, "25.83"), (3, "25.5")],
        "place_sum": 12,
        "score": "98.29",
        "mark": "",
        "block": "bottom",
    },
    {
        "team": "Астрахань",
        "fights": [(3, "20.33"), (3, "25.33"), (3, "27.5"), (3, "21.6")],
        "place_sum": 12,
        "score": "94.73",
        "mark": "",
        "block": "bottom",
    },
]


def ranking_rows():
    """Строки сайта: порядок как на скане; в баллах — сумма очков."""
    rows = []
    for i, row in enumerate(FIGHTS, start=1):
        rows.append((str(i), row["team"], row["score"]))
    return rows


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


def ensure_image(path: Path, title: str) -> Image:
    existing = Image.objects.filter(title=title).first()
    if existing:
        return existing
    with path.open("rb") as fh:
        image = Image(title=title, file=ImageFile(fh, name=path.name))
        image.save()
    return image


def attach_final_problems_scan(page) -> bool:
    root = Path(__file__).resolve().parents[3]
    path = root / FINAL_PROBLEMS_STATIC
    if not path.exists():
        return False
    page.problem_scans.filter(kind=TournamentProblemScan.KIND_FINAL).delete()
    Image.objects.filter(title=FINAL_SCAN_TITLE).delete()
    image = ensure_image(path, FINAL_SCAN_TITLE)
    TournamentProblemScan.objects.create(
        page=page,
        kind=TournamentProblemScan.KIND_FINAL,
        image=image,
        caption=FINAL_SCAN_CAPTION,
        sort_order=0,
    )
    image.get_rendition("width-1400")
    return True


class Command(BaseCommand):
    help = "Заполняет сезон 1990: физбои без финала, IYPT, скан заданий финала."

    def handle(self, *args, **options):
        page = TournamentPage.objects.filter(year=YEAR).first()
        if not page:
            self.stderr.write("Страницы 1990 нет.")
            return

        root = Path(__file__).resolve().parents[3]
        scan = root / "rypt/static/docs/results/1990-rezultaty-fizboev.jpg"
        if not scan.exists():
            self.stderr.write(f"Нет скана: {scan}")
            return

        page.city = CITY
        page.results_more_url = MORE_URL
        page.results_more_label = MORE_LABEL
        page.iypt_team = IYPT_TEAM
        page.iypt_more_url = IYPT_MORE_URL
        page.iypt_more_label = IYPT_MORE_LABEL
        page.save()

        page.ranking.all().delete()
        order = 0
        order = add_rows(page, TournamentResultRow.KIND_RANKING, ranking_rows(), order)
        order = add_rows(page, TournamentResultRow.KIND_IYPT_RANKING, IYPT_RANKING, order)
        add_rows(page, TournamentResultRow.KIND_IYPT_FINAL, IYPT_FINAL, order)

        final_ok = attach_final_problems_scan(page)
        page.save_revision().publish()

        self.stdout.write(
            self.style.SUCCESS(
                f"1990: {CITY}, рейтинг {len(FIGHTS)}, без финала, "
                f"IYPT {len(IYPT_RANKING)}/{len(IYPT_FINAL)}, "
                f"задания финала={'да' if final_ok else 'нет'}, "
                f"оригинал → {MORE_URL}"
            )
        )
