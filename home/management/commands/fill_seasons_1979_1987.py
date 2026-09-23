"""Создаёт сезоны I–IX (1979–1987) и вешает сканы Metod_1987 разворотами/страницами."""

from __future__ import annotations

import json
from pathlib import Path

from django.core.files.images import ImageFile
from django.core.management.base import BaseCommand
from wagtail.images.models import Image

from home.models import (
    HomePage,
    TournamentIndexPage,
    TournamentLink,
    TournamentPage,
    TournamentProblemScan,
    season_title,
    year_to_roman,
)

MAP = Path(__file__).resolve().parents[3] / "_scan_preview" / "metod_1987_map.json"
SCANS_ROOT = Path(__file__).resolve().parents[3] / "_scan_preview" / "by_tournament"
SOURCE_URL = "https://ilyam.org/PV_VM_Turnir_junyh_fizikov_MGU_Metod_1987.pdf"
SOURCE_LABEL = "Сканы: Metod_1987 (ильям.org)"


def ensure_image(path: Path, title: str) -> Image:
    existing = Image.objects.filter(title=title).first()
    if existing:
        return existing
    with path.open("rb") as fh:
        image = Image(title=title, file=ImageFile(fh, name=path.name))
        image.save()
    return image


class Command(BaseCommand):
    help = "Сезоны 1979–1987: страницы + сканы задач (разворот или страница)."

    def handle(self, *args, **options):
        if not MAP.exists():
            self.stderr.write(f"Нет карты: {MAP}")
            return
        home = HomePage.objects.first()
        index = TournamentIndexPage.objects.child_of(home).first() if home else None
        if not index:
            self.stderr.write("Сначала seed_site.")
            return

        payload = json.loads(MAP.read_text(encoding="utf-8"))
        tournaments = payload["tournaments"]

        for roman in ("I", "II", "III", "IV", "V", "VI", "VII", "VIII", "IX"):
            meta = tournaments[roman]
            year = meta["year"]
            folder = SCANS_ROOT / f"{year}_{roman}"
            if not folder.exists():
                self.stderr.write(f"{year}: нет папки {folder}")
                continue

            roman_auto = year_to_roman(year)
            title = season_title(year, roman_auto)
            page = TournamentPage.objects.child_of(index).filter(slug=str(year)).first()
            if not page:
                page = TournamentPage(
                    title=title,
                    slug=str(year),
                    year=year,
                    roman=roman_auto,
                    is_current=False,
                )
                index.add_child(instance=page)
            else:
                page.title = title
                page.year = year
                page.roman = roman_auto

            page.save()

            # Источник сканов — в материалах, не в «результатах».
            page.links.filter(url=SOURCE_URL).delete()
            TournamentLink.objects.create(
                page=page,
                kind=TournamentLink.REPORT,
                title=SOURCE_LABEL,
                url=SOURCE_URL,
                sort_order=0,
            )

            # Удаляем старые сканы и связанные картинки этого сезона (по title-префиксу).
            page.problem_scans.all().delete()
            Image.objects.filter(title__startswith=f"ТЮФ {roman} {year} scan").delete()

            order = 0
            for view_i, view in enumerate(meta["views"], start=1):
                files = view["files"]
                kind = view["type"]
                left_path = folder / files[0]
                left = ensure_image(
                    left_path,
                    f"ТЮФ {roman} {year} scan {view_i}a",
                )
                right = None
                caption = f"{'Разворот' if kind == 'spread' else 'Страница'} {view_i}"
                if kind == "spread" and len(files) >= 2:
                    right = ensure_image(
                        folder / files[1],
                        f"ТЮФ {roman} {year} scan {view_i}b",
                    )
                TournamentProblemScan.objects.create(
                    page=page,
                    image=left,
                    image_right=right,
                    caption=caption,
                    sort_order=order,
                )
                left.get_rendition("width-1400")
                if right:
                    right.get_rendition("width-1400")
                order += 1

            page.save_revision().publish()
            self.stdout.write(
                self.style.SUCCESS(
                    f"{title}: {order} вид(ов), сканы из {folder.name}"
                )
            )

        self.stdout.write(self.style.SUCCESS("Сезоны I–IX готовы."))
