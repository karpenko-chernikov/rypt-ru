"""Заполняет сезон 1989 по статье Е. Н. Юносова в «Кванте».

Источник: Юносов Е. Н. Об итогах ТЮФ 1988/89 года // Квант. 1989. № 10. С. 42
(web.archive.org/…/ob_itogah_tyuf_1988-89_goda.htm; скан страницы).

II Всесоюзный и II Международный ТЮФ: Москва, МЦ «Олимпиец»,
24 марта — 3 апреля 1989 (даты по приказу Гособразования СССР № 440).
В статье — 24 марта — 2 апреля (весенние каникулы).
Степени дипломов в тексте не разведены по командам — не выдумываем.
"""

from datetime import date
from pathlib import Path

from django.core.management.base import BaseCommand

from home.models import TournamentPage, TournamentResultRow

YEAR = 1989
CITY = "Москва, МЦ «Олимпиец»"
START = date(1989, 3, 24)
END = date(1989, 4, 3)
MORE_LABEL = "Оригинал: «Квант» № 10, 1989, стр. 42"
MORE_URL = "/static/docs/results/1989-kvant.jpg"
IYPT_MORE_URL = "https://archive.iypt.org/factsheets/"
IYPT_MORE_LABEL = "Оригинал"

IYPT_TEAM = """II Международный ТЮФ проходил в Москве вместе со II Всесоюзным.
По итогам Всесоюзного тура и личного первенства в Международный тур допущены
команды школы № 710 (Москва) и станции юных техников (Одесса).
Победили команды ФРГ и Болгарии."""

# II Всесоюзный: абсолютный победитель + команды с дипломами различных степеней
# (степени в статье не указаны — только факт диплома).
RANKING = [
    ("1", "Школа № 710, Москва", ""),
    ("—", "СЮТ, Одесса", "диплом"),
    ("—", "Школа № 1, Душанбе", "диплом"),
    ("—", "ВФШ при МГУ", "диплом"),
    ("—", "Школа № 1, Фрязино", "диплом"),
    ("—", "ФМШ № 18 при МГУ", "диплом"),
    ("—", "ФМШ № 542 при МИФИ", "диплом"),
    ("—", "ВФМШ при Томском ГУ", "диплом"),
    ("—", "Школа № 28, Запорожье", "диплом"),
    ("—", "Школа № 2, Дрокия", "диплом"),
    ("—", "Школа № 130, Новосибирск", "диплом"),
    ("—", "Школа-интернат им. В. М. Комарова, Тбилиси", "диплом"),
    ("—", "Школа № 45, Вильнюс", "диплом"),
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
    help = "Заполняет сезон 1989: II Всесоюзный ТЮФ по статье в «Кванте»."

    def handle(self, *args, **options):
        page = TournamentPage.objects.filter(year=YEAR).first()
        if not page:
            self.stderr.write("Страницы 1989 нет.")
            return

        scan = Path(__file__).resolve().parents[3] / "rypt/static/docs/results/1989-kvant.jpg"
        if not scan.exists():
            self.stderr.write(f"Нет скана: {scan}")
            return

        page.city = CITY
        page.date_start = START
        page.date_end = END
        page.results_more_url = MORE_URL
        page.results_more_label = MORE_LABEL
        page.iypt_team = IYPT_TEAM
        page.iypt_more_url = IYPT_MORE_URL
        page.iypt_more_label = IYPT_MORE_LABEL
        page.save()

        page.ranking.all().delete()
        add_rows(page, TournamentResultRow.KIND_RANKING, RANKING, 0)
        page.save_revision().publish()

        self.stdout.write(
            self.style.SUCCESS(
                f"1989: {CITY}, {START} — {END}, рейтинг {len(RANKING)}, "
                f"IYPT текст, оригинал → скан + Wayback"
            )
        )
