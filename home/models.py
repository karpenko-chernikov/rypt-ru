import html as html_lib
import json
import re
from datetime import date
from pathlib import Path

from django.conf import settings
from django.db import models
from django.core.exceptions import ValidationError
from modelcluster.fields import ParentalKey
from modelcluster.models import ClusterableModel
from wagtail.admin.panels import FieldPanel, InlinePanel, MultiFieldPanel
from wagtail.fields import RichTextField, StreamField
from wagtail.models import Orderable, Page
from wagtail.rich_text import expand_db_html

from home.blocks import ContactsSectionBlock
from home.regions import REGION_CHOICES, REGIONS

# Синтетический столбец матрицы / карточка (не субъект РФ на карте).
OPEN_ALL_RUSSIA_CODE = "OPEN"
OPEN_ALL_RUSSIA_TITLE = "Открытый всероссийский турнир"

_MONTH_SORT = (
    ("январ", 1),
    ("феврал", 2),
    ("март", 3),
    ("весн", 3),  # «весной», «весна»
    ("апрел", 4),
    ("ма[йя]", 5),
    ("июн", 6),
    ("июл", 7),
    ("август", 8),
    ("сентябр", 9),
    ("октябр", 10),
    ("ноябр", 11),
    ("декабр", 12),
)


def ranking_score(row):
    raw = str(row.points or "").replace(",", ".").replace(" ", "")
    try:
        return float(raw)
    except ValueError:
        return float("-inf")


def vk_sized(url, cs):
    if not url:
        return ""
    url = html_lib.unescape(url)
    if re.search(r"cs=[^&]+", url):
        return re.sub(r"cs=[^&]+", f"cs={cs}", url)
    return url


def year_to_roman(year):
    # Как на МТИ: 2009 = XXXI → год минус 1978.
    n = year - 1978
    if n <= 0:
        return ""
    parts = (
        (1000, "M"), (900, "CM"), (500, "D"), (400, "CD"),
        (100, "C"), (90, "XC"), (50, "L"), (40, "XL"),
        (10, "X"), (9, "IX"), (5, "V"), (4, "IV"), (1, "I"),
    )
    out = []
    for value, symbol in parts:
        while n >= value:
            out.append(symbol)
            n -= value
    return "".join(out)


def season_title(year, roman=None):
    roman = roman or year_to_roman(year)
    if roman:
        return f"{roman} · {year}"
    return str(year)


def academic_season_label(year):
    """Подпись сезона вида 2026/2027 (year — второй календарный год сезона)."""
    try:
        y = int(year)
    except (TypeError, ValueError):
        return str(year or "")
    return f"{y - 1}/{y}"


def current_tournament_season():
    return TournamentPage.objects.filter(is_current=True).first()


def _season_spring_year(current) -> int:
    try:
        return int(current.year)
    except (TypeError, ValueError, AttributeError):
        return date.today().year


def _month_day_from_note(note: str) -> tuple[int, int] | None:
    """Грубая дата из свободной формулировки («конец февраля», «март 2027»)."""
    text = (note or "").lower().replace("ё", "е")
    if not text.strip():
        return None
    month = None
    for pattern, num in _MONTH_SORT:
        if re.search(pattern, text):
            month = num
            break
    if not month:
        return None
    if "конец" in text:
        day = 25
    elif "начал" in text or "серед" in text:
        day = 10 if "начал" in text else 15
    else:
        day = 15
    # «февраль–март» / «февраль-март» — ориентир на более поздний месяц диапазона
    months_found = [n for p, n in _MONTH_SORT if re.search(p, text)]
    if len(months_found) >= 2:
        month = months_found[-1]
        day = 1
    return month, day


def open_all_russia_payload(current=None):
    """Карточка открытого всероссийского турнира для панели и матрицы."""
    current = current or current_tournament_season()
    season_label = academic_season_label(current.year) if current else ""
    problems = []
    if current:
        problems = [
            {"number": p.number, "title": p.title, "statement": p.statement}
            for p in current.problems.all().order_by("number")
        ]
    return {
        "code": OPEN_ALL_RUSSIA_CODE,
        "region_code": OPEN_ALL_RUSSIA_CODE,
        "region": OPEN_ALL_RUSSIA_TITLE,
        "has_tournament": True,
        "title": OPEN_ALL_RUSSIA_TITLE,
        "city": "Москва",
        "when": "15–21 марта",
        "contacts": "",
        "info_html": (
            "<p>Открытый всероссийский турнир юных физиков — финал сезона. "
            "Играются все задачи списка.</p>"
        ),
        "problems": problems,
        "problems_pending": bool(current) and len(problems) == 0,
        "problems_pending_text": (
            f"Задачи на сезон «{season_label}» ещё не опубликованы."
            if current
            else "Текущий сезон не задан."
        ),
        "season_label": season_label,
        "results_text": "",
        "results_url": "",
        "results_label": "",
        "photos": [],
        "is_national": True,
    }


def matrix_tournament_label(title: str, fallback: str = "") -> str:
    """Короткое имя для столбца: «Сибирский турнир юных физиков» → «Сибирский»."""
    text = (title or "").strip()
    for suffix in (
        " турнир юных физиков",
        " Турнир юных физиков",
        " турнир юных физиков.",
    ):
        if len(text) > len(suffix) and text.casefold().endswith(suffix.casefold()):
            short = text[: -len(suffix)].strip(" —–-")
            if short:
                return short[:40]
    return (text or fallback)[:40]


def matrix_column_when(city: str, when: str) -> str:
    parts = [p for p in (city.strip() if city else "", when.strip() if when else "") if p]
    return " · ".join(parts)


def build_russia_problems_matrix(russia_page):
    """Матрица задач текущего сезона × турниры (регионы по датам, всероссийский — последний)."""
    current = current_tournament_season()
    if not current:
        return None
    problems = list(current.problems.all().order_by("number"))
    if not problems:
        return None
    tours = list(
        russia_page.regions.filter(has_tournament=True)
        .prefetch_related(
            models.Prefetch(
                "season_problem_links",
                queryset=RegionalTournamentProblem.objects.filter(
                    problem__page=current
                ).select_related("problem"),
            )
        )
    )
    tours.sort(key=lambda t: (t.matrix_sort_date(_season_spring_year(current)), t.region_code))
    linked = {
        t.pk: {link.problem_id for link in t.season_problem_links.all()}
        for t in tours
    }
    # В матрице только турниры, у которых уже выбраны задачи сезона.
    tours = [t for t in tours if linked.get(t.pk)]

    columns = [
        {
            "code": t.payload_code,
            "label": matrix_tournament_label(t.title, t.city or t.region_name),
            "title": t.title,
            "region": t.region_name,
            "region_code": t.region_code,
            "when": matrix_column_when(t.city, t.when_label()),
            "is_national": False,
        }
        for t in tours
    ]

    # Открытый всероссийский — все задачи сезона, всегда последний столбец.
    national = open_all_russia_payload(current)
    columns.append(
        {
            "code": OPEN_ALL_RUSSIA_CODE,
            "label": OPEN_ALL_RUSSIA_TITLE,
            "title": OPEN_ALL_RUSSIA_TITLE,
            "region": OPEN_ALL_RUSSIA_TITLE,
            "when": f"{national['city']} · {national['when']}",
            "is_national": True,
        }
    )

    rows = [
        {
            "number": p.number,
            "title": p.title,
            "cells": [p.id in linked[t.pk] for t in tours] + [True],
        }
        for p in problems
    ]
    return {
        "season_label": academic_season_label(current.year),
        "season_title": current.display_title,
        "columns": columns,
        "rows": rows,
    }


class HomePage(Page):
    lead = models.CharField(
        "Главная фраза",
        max_length=240,
        blank=True,
        help_text="Одно предложение под названием. Его видно первым на сайте.",
    )
    intro = RichTextField(
        "Коротко о турнире",
        blank=True,
        features=["bold", "italic", "link"],
    )
    season_label = models.CharField(
        "Сезон",
        max_length=80,
        blank=True,
        help_text="Например: 2025/26",
    )
    reporter_text = models.TextField("Докладчик", blank=True)
    opponent_text = models.TextField("Оппонент", blank=True)
    reviewer_text = models.TextField("Рецензент", blank=True)
    info_title = models.CharField(
        "Заголовок блока",
        max_length=240,
        blank=True,
        default="Информация о ближайшем Открытом Всероссийском Турнире юных физиков",
    )
    info_dates = models.CharField(
        "Даты",
        max_length=240,
        blank=True,
        help_text="Например: 15–21 марта 2027, Москва.",
    )
    info_text = RichTextField(
        "Информация",
        blank=True,
        features=["bold", "italic", "link", "image", "ol", "ul"],
    )
    info_photo = models.ForeignKey(
        "wagtailimages.Image",
        on_delete=models.SET_NULL,
        related_name="+",
        verbose_name="Фотография",
        null=True,
        blank=True,
    )
    info_photo_caption = models.CharField(
        "Подпись к фотографии",
        max_length=240,
        blank=True,
        help_text="Например: университет, где пройдёт турнир.",
    )

    content_panels = Page.content_panels + [
        FieldPanel("lead"),
        FieldPanel("intro"),
        FieldPanel("season_label"),
        MultiFieldPanel(
            [
                FieldPanel("reporter_text"),
                FieldPanel("opponent_text"),
                FieldPanel("reviewer_text"),
            ],
            heading="Три роли физбоя",
        ),
        MultiFieldPanel(
            [
                FieldPanel("info_title"),
                FieldPanel("info_dates"),
                FieldPanel("info_text"),
                FieldPanel("info_photo"),
                FieldPanel("info_photo_caption"),
            ],
            heading="Информация о ближайшем турнире",
        ),
        InlinePanel("info_files", label="Файлы"),
        InlinePanel("info_buttons", label="Кнопки"),
    ]

    max_count = 1
    parent_page_types = ["wagtailcore.Page"]

    def get_context(self, request):
        context = super().get_context(request)
        news_index = NewsIndexPage.objects.child_of(self).live().first()
        news = NewsPage.objects.none()
        if news_index:
            news = (
                NewsPage.objects.child_of(news_index)
                .live()
                .public()
                .order_by("-date", "-first_published_at")[:8]
            )
        context["news"] = news
        context["news_index"] = news_index
        context["pages"] = (
            ContentPage.objects.child_of(self).live().public().order_by("path")
        )
        return context

    def info_payload(self):
        """Данные блока «Информация о ближайшем турнире» для главной страницы."""
        files = []
        for item in self.info_files.all():
            url = item.url or (item.document.file.url if item.document else "")
            if not url:
                continue
            files.append(
                {
                    "title": item.title or (item.document.title if item.document else ""),
                    "url": url,
                    "download": bool(item.document),
                }
            )
        return {
            "title": self.info_title
            or "Информация о ближайшем Открытом Всероссийском Турнире юных физиков",
            "dates": self.info_dates,
            "text": self.info_text,
            "photo_url": self.info_photo.file.url if self.info_photo else "",
            "photo_caption": self.info_photo_caption,
            "files": files,
            "buttons": [
                {"label": btn.label, "url": btn.url}
                for btn in self.info_buttons.all()
                if btn.label and btn.url
            ],
        }


class HomeInfoFile(Orderable):
    """Файл в блоке информации на главной (загруженный документ или ссылка)."""

    page = ParentalKey(HomePage, on_delete=models.CASCADE, related_name="info_files")
    title = models.CharField("Название", max_length=200, blank=True)
    document = models.ForeignKey(
        "wagtaildocs.Document",
        on_delete=models.SET_NULL,
        related_name="+",
        verbose_name="Файл (документ)",
        null=True,
        blank=True,
    )
    url = models.CharField(
        "Или ссылка",
        max_length=500,
        blank=True,
        help_text="Внешняя ссылка (https://…) или путь к файлу (/media/…).",
    )

    panels = [
        FieldPanel("title"),
        FieldPanel("document"),
        FieldPanel("url"),
    ]


class HomeInfoButton(Orderable):
    """Кнопка-действие в блоке информации (предрегистрация, регистрация, МТИ и т.д.)."""

    page = ParentalKey(HomePage, on_delete=models.CASCADE, related_name="info_buttons")
    label = models.CharField("Текст кнопки", max_length=120)
    url = models.CharField("Ссылка", max_length=500)

    panels = [FieldPanel("label"), FieldPanel("url")]


class NewsIndexPage(Page):
    intro = RichTextField("Вступление", blank=True, features=["bold", "italic"])

    content_panels = Page.content_panels + [FieldPanel("intro")]
    parent_page_types = ["home.HomePage"]
    subpage_types = ["home.NewsPage"]
    max_count = 1

    def get_context(self, request):
        context = super().get_context(request)
        context["news"] = (
            NewsPage.objects.child_of(self)
            .live()
            .public()
            .order_by("-date", "-first_published_at")
        )
        return context


class NewsPage(Page):
    date = models.DateField("Дата")
    body = RichTextField("Текст", features=["h2", "h3", "bold", "italic", "link", "ol", "ul"])
    telegram_channel = models.CharField(
        "Telegram-канал",
        max_length=64,
        blank=True,
        editable=False,
    )
    telegram_message_id = models.BigIntegerField(
        "ID поста в Telegram",
        null=True,
        blank=True,
        editable=False,
    )

    content_panels = Page.content_panels + [
        FieldPanel("date"),
        FieldPanel("body"),
        InlinePanel("attachments", label="Вложения (фото и видео)"),
    ]
    parent_page_types = ["home.NewsIndexPage"]
    subpage_types = []

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["telegram_channel", "telegram_message_id"],
                condition=models.Q(telegram_message_id__isnull=False),
                name="news_telegram_post_unique",
            ),
        ]

    @property
    def short_title(self, max_words=5, max_chars=50):
        """Короткий заголовок для списков и детальной страницы."""
        title = (self.title or "").strip()
        if not title:
            return title
        words = title.split()
        short = " ".join(words[:max_words])
        if len(short) > max_chars:
            short = short[:max_chars].rstrip()
        if short != title:
            short = short.rstrip(".,;:!?—–-") + "…"
        return short


class NewsAttachment(Orderable):
    KIND_PHOTO = "photo"
    KIND_VIDEO = "video"
    KIND_CHOICES = [(KIND_PHOTO, "Фото"), (KIND_VIDEO, "Видео")]

    page = ParentalKey(NewsPage, on_delete=models.CASCADE, related_name="attachments")
    kind = models.CharField(
        "Тип",
        max_length=8,
        choices=KIND_CHOICES,
        default=KIND_PHOTO,
    )
    image = models.ForeignKey(
        "wagtailimages.Image",
        on_delete=models.SET_NULL,
        related_name="+",
        verbose_name="Фото",
        null=True,
        blank=True,
    )
    video_file = models.FileField(
        "Видеофайл",
        upload_to="news/videos/%Y/%m",
        blank=True,
    )
    original_url = models.URLField("Оригинал (t.me)", blank=True)
    caption = models.CharField("Подпись", max_length=300, blank=True)

    panels = [
        FieldPanel("kind"),
        FieldPanel("image"),
        FieldPanel("video_file"),
        FieldPanel("original_url"),
        FieldPanel("caption"),
    ]

    @property
    def is_video(self):
        return self.kind == self.KIND_VIDEO


class NewsSyncState(models.Model):
    channel = models.CharField("Telegram-канал", max_length=64, blank=True)
    last_message_id = models.BigIntegerField("Последний обработанный ID", default=0)

    class Meta:
        verbose_name = "Состояние синхронизации Telegram"
        verbose_name_plural = "Состояние синхронизации Telegram"

    def __str__(self):
        return f"Telegram sync: {self.channel}@{self.last_message_id}"

    @classmethod
    def get(cls):
        return cls.objects.get_or_create(pk=1)[0]


class ContentPage(Page):
    body = RichTextField(
        "Текст страницы",
        blank=True,
        features=["h2", "h3", "bold", "italic", "link", "ol", "ul"],
    )

    content_panels = Page.content_panels + [FieldPanel("body")]
    parent_page_types = ["home.HomePage"]
    subpage_types = []

    def get_template(self, request, *args, **kwargs):
        if self.slug == "partners":
            return "home/partners_page.html"
        if self.slug == "rules":
            return "home/documents_page.html"
        return super().get_template(request, *args, **kwargs)

    def get_context(self, request, *args, **kwargs):
        context = super().get_context(request, *args, **kwargs)
        if self.slug == "partners":
            from home.partners import PARTNERS

            context["partners"] = PARTNERS
        if self.slug == "rules":
            from home.documents import CHARTER_DOCX, CHARTER_HTML, REGULATION_PDF, VOK

            context["regulation_pdf"] = REGULATION_PDF
            context["charter_docx"] = CHARTER_DOCX
            context["charter_html"] = CHARTER_HTML
            context["vok"] = VOK
        return context


class ContactsPage(Page):
    """Страница «Контакты»: блоки с контактами, заполняемые через Wagtail."""

    sections = StreamField(
        [("contacts_section", ContactsSectionBlock())],
        verbose_name="Блоки",
        blank=True,
    )

    content_panels = Page.content_panels + [FieldPanel("sections")]
    parent_page_types = ["home.HomePage"]
    subpage_types = []
    max_count = 1

    def sections_data(self):
        """Список блоков с контактами и готовыми URL аватарок для шаблона."""
        data = []
        for block in self.sections:
            if block.block_type != "contacts_section":
                continue
            contacts = []
            for contact in block.value.get("contacts") or []:
                methods = [
                    {"type": method.get("type", ""), "value": method.get("value", "")}
                    for method in contact.get("methods") or []
                ]
                photo = contact.get("photo")
                contacts.append(
                    {
                        "name": contact.get("name", ""),
                        "subtitle": contact.get("subtitle", ""),
                        "photo_url": (
                            photo.get_rendition("fill-256x256-c100").url
                            if photo
                            else ""
                        ),
                        "methods": methods,
                    }
                )
            data.append(
                {
                    "title": block.value.get("title", ""),
                    "contacts": contacts,
                }
            )
        return data


class MaterialsIndexPage(Page):
    """Раздел «Полезные материалы»: группы, внутри — карточки материалов."""

    intro = RichTextField(
        "Вступление",
        blank=True,
        features=["bold", "italic", "link"],
    )

    content_panels = Page.content_panels + [FieldPanel("intro")]
    parent_page_types = ["home.HomePage"]
    subpage_types = ["home.MaterialGroupPage"]
    max_count = 1

    def groups_data(self):
        """Список групп с материалами для шаблонов (индекс и слайд в колоде)."""
        data = []
        groups = (
            MaterialGroupPage.objects.child_of(self)
            .live()
            .public()
            .order_by("path")
        )
        for group in groups:
            data.append(
                {
                    "title": group.title,
                    "materials": list(
                        MaterialPage.objects.child_of(group)
                        .live()
                        .public()
                        .order_by("path")
                    ),
                }
            )
        return data

    def get_context(self, request):
        context = super().get_context(request)
        context["groups"] = self.groups_data()
        return context


class MaterialGroupPage(Page):
    """Заголовок группы материалов (Header)."""

    content_panels = Page.content_panels
    parent_page_types = ["home.MaterialsIndexPage"]
    subpage_types = ["home.MaterialPage"]

    def get_context(self, request):
        context = super().get_context(request)
        context["groups"] = [
            {
                "title": self.title,
                "materials": list(
                    MaterialPage.objects.child_of(self).live().public().order_by("path")
                ),
            }
        ]
        return context


class MaterialPage(Page):
    summary = models.CharField(
        "Краткое описание",
        max_length=240,
        blank=True,
        help_text="Показывается на карточке под названием.",
    )
    body = RichTextField(
        "Текст материала",
        blank=True,
        features=[
            "h1",
            "h2",
            "h3",
            "bold",
            "italic",
            "underline",
            "link",
            "image",
            "document-link",
            "ol",
            "ul",
        ],
    )

    content_panels = Page.content_panels + [
        FieldPanel("summary"),
        FieldPanel("body"),
    ]
    parent_page_types = ["home.MaterialGroupPage"]
    subpage_types = []


class TournamentIndexPage(Page):
    intro = RichTextField("Вступление", blank=True, features=["bold", "italic", "link"])

    content_panels = Page.content_panels + [FieldPanel("intro")]
    parent_page_types = ["home.HomePage"]
    subpage_types = ["home.TournamentPage"]
    max_count = 1

    def get_context(self, request):
        context = super().get_context(request)
        seasons = TournamentPage.objects.child_of(self).live().public().order_by("-year")
        context["current"] = seasons.filter(is_current=True).first()
        context["seasons"] = seasons
        return context


class TournamentPage(Page):
    year = models.PositiveIntegerField("Год")
    roman = models.CharField("Римский номер", max_length=16, blank=True)
    is_current = models.BooleanField("Текущий сезон", default=False)
    city = models.CharField("Город", max_length=120, blank=True)
    date_start = models.DateField("Начало", blank=True, null=True)
    date_end = models.DateField("Конец", blank=True, null=True)
    iypt_team = models.TextField("Кто поехал на IYPT", blank=True)
    iypt_more_url = models.URLField("Подробные результаты IYPT, ссылка", blank=True)
    iypt_more_label = models.CharField(
        "Подпись к ссылке на IYPT",
        max_length=160,
        blank=True,
        default="Оригинал",
    )
    results_more_url = models.CharField(
        "Подробные результаты, ссылка или файл",
        max_length=500,
        blank=True,
        help_text="Внешняя ссылка (https://…) или путь к файлу (/media/…).",
    )
    results_more_label = models.CharField(
        "Подпись к ссылке на результаты",
        max_length=160,
        blank=True,
        default="Подробнее",
    )
    photo_album_url = models.TextField(
        "Альбомы фото (ссылки, по одной на строку)",
        blank=True,
        help_text="Файлы на сервер не копируются. Можно несколько альбомов ВК.",
    )

    content_panels = Page.content_panels + [
        MultiFieldPanel(
            [
                FieldPanel("year"),
                FieldPanel("roman"),
                FieldPanel("is_current"),
                FieldPanel("city"),
                FieldPanel("date_start"),
                FieldPanel("date_end"),
            ],
            heading="Сезон",
        ),
        MultiFieldPanel(
            [
                FieldPanel("iypt_team"),
                FieldPanel("iypt_more_url"),
                FieldPanel("iypt_more_label"),
            ],
            heading="IYPT",
        ),
        InlinePanel("problems", label="Задачи"),
        InlinePanel("problem_scans", label="Сканы задач (страница / разворот)"),
        InlinePanel("ranking", label="Итоговая таблица"),
        MultiFieldPanel(
            [
                FieldPanel("results_more_url"),
                FieldPanel("results_more_label"),
            ],
            heading="Подробные результаты",
        ),
        InlinePanel("photos", label="Фото (файлы или внешние ссылки)"),
        FieldPanel("photo_album_url"),
        InlinePanel("links", label="Отчёты и новости"),
    ]

    parent_page_types = ["home.TournamentIndexPage"]
    subpage_types = []

    def clean(self):
        super().clean()
        if self.is_current:
            others = TournamentPage.objects.filter(is_current=True)
            if self.pk:
                others = others.exclude(pk=self.pk)
            if others.exists():
                raise ValidationError({"is_current": "Текущим может быть только один сезон."})

    def save(self, *args, **kwargs):
        if self.year:
            self.roman = year_to_roman(self.year)
            wanted = season_title(self.year, self.roman)
            if self.title != wanted:
                self.title = wanted
        super().save(*args, **kwargs)

    @property
    def display_title(self):
        return season_title(self.year, self.roman or year_to_roman(self.year))

    def album_urls(self):
        text = self.photo_album_url or ""
        return [line.strip() for line in text.splitlines() if line.strip()]

    def album_ref(self):
        urls = self.album_urls()
        if not urls:
            return None
        match = re.search(r"album(-?\d+)_(\d+)", urls[0])
        if not match:
            return None
        return match.group(1), match.group(2)

    def get_context(self, request):
        context = super().get_context(request)
        context["problems"] = self.problems.all().order_by("number")
        context["problem_scans"] = list(self.problem_scans.all())
        context["has_problem_scans"] = bool(context["problem_scans"])
        rows = list(self.ranking.all())
        by_kind = {}
        for row in rows:
            by_kind.setdefault(row.kind, []).append(row)

        def table(kind):
            return sorted(by_kind.get(kind, []), key=ranking_score, reverse=True)

        context["ranking"] = table(TournamentResultRow.KIND_RANKING)
        context["league_a"] = table(TournamentResultRow.KIND_LEAGUE_A)
        context["league_b"] = table(TournamentResultRow.KIND_LEAGUE_B)
        context["finals"] = table(TournamentResultRow.KIND_FINAL)
        context["finals_b"] = table(TournamentResultRow.KIND_FINAL_B)
        context["iypt_ranking"] = table(TournamentResultRow.KIND_IYPT_RANKING)
        context["iypt_final"] = table(TournamentResultRow.KIND_IYPT_FINAL)
        context["has_result_tables"] = bool(
            context["ranking"]
            or context["league_a"]
            or context["league_b"]
            or context["finals"]
            or context["finals_b"]
        )
        context["has_leagues"] = bool(
            context["league_a"] or context["league_b"] or context["finals_b"]
        )
        context["has_iypt_tables"] = bool(context["iypt_ranking"] or context["iypt_final"])
        context["has_iypt"] = bool(
            self.iypt_team or self.iypt_more_url or context["has_iypt_tables"]
        )
        for key in (
            "ranking",
            "league_a",
            "league_b",
            "finals",
            "finals_b",
            "iypt_ranking",
            "iypt_final",
        ):
            context[f"{key}_has_city"] = any(row.city for row in context[key])
        context["photos"] = list(self.photos.all())
        context["album_urls"] = self.album_urls()
        context["has_photos"] = bool(context["album_urls"]) or bool(context["photos"])
        context["news_links"] = self.links.filter(kind="news")
        context["report_links"] = self.links.filter(kind="report")
        return context


class TournamentProblem(Orderable):
    page = ParentalKey(TournamentPage, on_delete=models.CASCADE, related_name="problems")
    number = models.PositiveIntegerField("Номер")
    title = models.CharField("Название", max_length=200)
    statement = models.TextField("Условие")

    panels = [FieldPanel("number"), FieldPanel("title"), FieldPanel("statement")]


class TournamentProblemScan(Orderable):
    """Скан страницы или разворота условий (без чужих турниров на одном кадре)."""

    page = ParentalKey(TournamentPage, on_delete=models.CASCADE, related_name="problem_scans")
    image = models.ForeignKey(
        "wagtailimages.Image",
        on_delete=models.CASCADE,
        related_name="+",
        verbose_name="Страница или левая полоса",
    )
    image_right = models.ForeignKey(
        "wagtailimages.Image",
        on_delete=models.SET_NULL,
        related_name="+",
        verbose_name="Правая полоса (разворот)",
        null=True,
        blank=True,
    )
    caption = models.CharField("Подпись", max_length=200, blank=True)

    panels = [
        FieldPanel("image"),
        FieldPanel("image_right"),
        FieldPanel("caption"),
    ]

    @property
    def is_spread(self):
        return bool(self.image_right_id)


class TournamentResultRow(Orderable):
    KIND_RANKING = "ranking"
    KIND_FINAL = "final"
    KIND_LEAGUE_A = "league_a"
    KIND_LEAGUE_B = "league_b"
    KIND_FINAL_B = "final_b"
    KIND_IYPT_RANKING = "iypt_ranking"
    KIND_IYPT_FINAL = "iypt_final"
    KIND_CHOICES = [
        (KIND_RANKING, "Общий рейтинг"),
        (KIND_LEAGUE_A, "Высшая лига"),
        (KIND_LEAGUE_B, "Первая лига"),
        (KIND_FINAL, "Финал высшей лиги"),
        (KIND_FINAL_B, "Финал первой лиги"),
        (KIND_IYPT_RANKING, "IYPT: рейтинг"),
        (KIND_IYPT_FINAL, "IYPT: финал"),
    ]

    page = ParentalKey(TournamentPage, on_delete=models.CASCADE, related_name="ranking")
    kind = models.CharField("Таблица", max_length=16, choices=KIND_CHOICES, default=KIND_RANKING)
    place = models.CharField("Место", max_length=16)
    team = models.CharField("Команда", max_length=200)
    city = models.CharField("Город", max_length=120, blank=True)
    points = models.CharField("Сумма", max_length=32, blank=True)

    panels = [
        FieldPanel("kind"),
        FieldPanel("place"),
        FieldPanel("team"),
        FieldPanel("city"),
        FieldPanel("points"),
    ]


class TournamentPhoto(Orderable):
    page = ParentalKey(TournamentPage, on_delete=models.CASCADE, related_name="photos")
    image = models.ForeignKey(
        "wagtailimages.Image",
        on_delete=models.SET_NULL,
        related_name="+",
        verbose_name="Файл на сервере",
        null=True,
        blank=True,
    )
    external_url = models.TextField("Ссылка на фото", blank=True)
    original_url = models.URLField("Оригинал", blank=True)
    caption = models.CharField("Подпись", max_length=200, blank=True)

    panels = [
        FieldPanel("image"),
        FieldPanel("external_url"),
        FieldPanel("original_url"),
        FieldPanel("caption"),
    ]

    @property
    def src(self):
        if self.external_url:
            return vk_sized(self.external_url, "1280x0")
        if self.image:
            return self.image.file.url
        return ""

    @property
    def thumb_src(self):
        if self.external_url:
            return vk_sized(self.external_url, "240x0")
        if self.image:
            return self.image.file.url
        return ""

    @property
    def original(self):
        return self.original_url or ""


class TournamentLink(Orderable):
    NEWS = "news"
    REPORT = "report"
    KIND_CHOICES = [(NEWS, "Новость"), (REPORT, "Отчёт")]

    page = ParentalKey(TournamentPage, on_delete=models.CASCADE, related_name="links")
    kind = models.CharField("Тип", max_length=16, choices=KIND_CHOICES, default=NEWS)
    title = models.CharField("Название", max_length=200)
    url = models.URLField("Ссылка")

    panels = [FieldPanel("kind"), FieldPanel("title"), FieldPanel("url")]


def load_russia_svg() -> str:
    """SVG карты субъектов; стили снимаем — рисуем через CSS."""
    path = Path(settings.PROJECT_DIR) / "static" / "maps" / "russia.svg"
    if not path.exists():
        return ""
    raw = path.read_text(encoding="utf-8")
    raw = re.sub(r"<\?xml[^?]*\?>", "", raw).strip()
    raw = re.sub(r'\sstyle="[^"]*"', "", raw)
    raw = re.sub(r"\sstyle='[^']*'", "", raw)
    return raw


class RussiaTournamentsPage(Page):
    """Раздел «Турниры в России» с интерактивной картой."""

    intro = RichTextField(
        "Вступление",
        blank=True,
        features=["bold", "italic", "link"],
        help_text="Короткий текст над картой.",
    )

    content_panels = Page.content_panels + [
        FieldPanel("intro"),
        InlinePanel("regions", label="Региональные турниры"),
    ]

    parent_page_types = ["home.HomePage"]
    subpage_types = []
    max_count = 1

    def regions_payload(self):
        """Данные для JS: slug турнира → карточка (+ открытый всероссийский)."""
        out = {}
        for reg in self.regions.all():
            out[reg.payload_code] = reg.as_payload()
        out[OPEN_ALL_RUSSIA_CODE] = open_all_russia_payload()
        return out

    def get_context(self, request):
        context = super().get_context(request)
        context["russia_svg"] = load_russia_svg()
        context["regions_json"] = json.dumps(self.regions_payload(), ensure_ascii=False)
        context["region_names_json"] = json.dumps(REGIONS, ensure_ascii=False)
        context["active_region_codes"] = list(
            {
                r.region_code
                for r in self.regions.all()
                if r.has_tournament and r.region_code and r.region_code != "ONLINE"
            }
        )
        context["problems_matrix"] = build_russia_problems_matrix(self)
        return context


class RegionalTournament(ClusterableModel, Orderable):
    page = ParentalKey(
        RussiaTournamentsPage,
        on_delete=models.CASCADE,
        related_name="regions",
    )
    slug = models.SlugField(
        "Код турнира",
        max_length=64,
        help_text="Уникальный ключ для матрицы и карточки, напр. sib, mos-mipt, beaver.",
    )
    region_code = models.CharField(
        "Субъект РФ / онлайн",
        max_length=16,
        choices=REGION_CHOICES,
        db_index=True,
    )
    has_tournament = models.BooleanField(
        "Есть турнир (подсветка на карте)",
        default=True,
    )
    title = models.CharField("Название турнира", max_length=200)
    city = models.CharField("Город / площадка", max_length=160, blank=True)
    date_start = models.DateField("Начало", blank=True, null=True)
    date_end = models.DateField("Конец", blank=True, null=True)
    date_note = models.CharField(
        "Когда (свободная формулировка)",
        max_length=200,
        blank=True,
        help_text="Например: «март 2026» или «даты уточняются».",
    )
    contacts = models.TextField("Контакты", blank=True)
    info = RichTextField(
        "О турнире",
        blank=True,
        features=["bold", "italic", "link", "ol", "ul"],
    )
    results_url = models.CharField(
        "Результаты: ссылка на оригинал",
        max_length=500,
        blank=True,
    )
    results_label = models.CharField(
        "Подпись к результатам",
        max_length=160,
        blank=True,
        default="Оригинал результатов",
    )
    results_text = models.TextField(
        "Краткие результаты",
        blank=True,
        help_text="Можно списком: место — команда.",
    )

    panels = [
        MultiFieldPanel(
            [
                FieldPanel("slug"),
                FieldPanel("region_code"),
                FieldPanel("has_tournament"),
                FieldPanel("title"),
                FieldPanel("city"),
                FieldPanel("date_start"),
                FieldPanel("date_end"),
                FieldPanel("date_note"),
            ],
            heading="Регион и даты",
        ),
        FieldPanel("contacts"),
        FieldPanel("info"),
        InlinePanel("problems", label="Задачи года"),
        MultiFieldPanel(
            [
                FieldPanel("results_text"),
                FieldPanel("results_url"),
                FieldPanel("results_label"),
            ],
            heading="Результаты",
        ),
        InlinePanel("photos", label="Фото"),
    ]

    class Meta(Orderable.Meta):
        verbose_name = "Региональный турнир"
        verbose_name_plural = "Региональные турниры"
        unique_together = [("page", "slug")]

    def __str__(self):
        return f"{self.region_name}: {self.title}"

    @property
    def payload_code(self):
        return self.slug or self.region_code

    @property
    def region_name(self):
        return REGIONS.get(self.region_code, self.region_code)

    def when_label(self):
        if self.date_note:
            return self.date_note
        if self.date_start and self.date_end:
            if self.date_start == self.date_end:
                return self.date_start.strftime("%d.%m.%Y")
            return f"{self.date_start.strftime('%d.%m.%Y')} – {self.date_end.strftime('%d.%m.%Y')}"
        if self.date_start:
            return self.date_start.strftime("%d.%m.%Y")
        return ""

    def matrix_sort_date(self, spring_year: int) -> date:
        """Дата для порядка столбцов матрицы (раньше → левее)."""
        if self.date_start:
            return self.date_start
        parsed = _month_day_from_note(self.date_note)
        if parsed:
            month, day = parsed
            # Сезон: сент–дек относятся к первому календарному году.
            year = spring_year - 1 if month >= 9 else spring_year
            try:
                return date(year, month, day)
            except ValueError:
                return date(year, month, 28)
        # Без даты — в конце региональных (перед всероссийским).
        return date(spring_year, 12, 31)

    def current_season_problem_rows(self):
        """Задачи текущего сезона, отмеченные для этого регионального турнира."""
        current = current_tournament_season()
        if not current:
            return [], None
        qs = (
            TournamentProblem.objects.filter(
                page=current,
                regional_links__tournament=self,
            )
            .order_by("number")
            .distinct()
        )
        return list(qs), current

    def as_payload(self):
        problems_qs, current = self.current_season_problem_rows()
        season_label = academic_season_label(current.year) if current else ""
        problems = [
            {
                "number": p.number,
                "title": p.title,
                "statement": p.statement,
            }
            for p in problems_qs
        ]
        pending = bool(current) and len(problems) == 0
        if pending:
            pending_text = f"Задачи на сезон «{season_label}» ещё не выбраны."
        elif not current:
            pending_text = "Текущий сезон не задан — задачи регионального турнира пока не привязаны."
            pending = True
        else:
            pending_text = ""
        return {
            "code": self.payload_code,
            "region_code": self.region_code,
            "region": self.region_name,
            "has_tournament": self.has_tournament,
            "title": self.title,
            "city": self.city,
            "when": self.when_label(),
            "contacts": self.contacts,
            "info_html": expand_db_html(self.info) if self.info else "",
            "problems": problems,
            "problems_pending": pending,
            "problems_pending_text": pending_text,
            "season_label": season_label,
            "results_text": self.results_text,
            "results_url": self.results_url,
            "results_label": self.results_label or "Оригинал результатов",
            "photos": [
                {
                    "src": ph.src,
                    "thumb": ph.thumb_src,
                    "caption": ph.caption,
                    "original": ph.original,
                }
                for ph in self.photos.all()
                if ph.src
            ],
        }


class RegionalTournamentProblem(models.Model):
    """Какие задачи текущего (или прошлого) сезона играют на региональном турнире."""

    tournament = models.ForeignKey(
        RegionalTournament,
        on_delete=models.CASCADE,
        related_name="season_problem_links",
        verbose_name="Региональный турнир",
    )
    problem = models.ForeignKey(
        "home.TournamentProblem",
        on_delete=models.CASCADE,
        related_name="regional_links",
        verbose_name="Задача сезона",
    )

    class Meta:
        verbose_name = "Задача регионального турнира"
        verbose_name_plural = "Задачи региональных турниров"
        unique_together = [("tournament", "problem")]

    def __str__(self):
        return f"{self.tournament_id}: задача {self.problem_id}"


class RegionalProblem(Orderable):
    """Устарело: свободный текст задач. Сайт использует RegionalTournamentProblem."""

    tournament = ParentalKey(
        RegionalTournament,
        on_delete=models.CASCADE,
        related_name="problems",
    )
    number = models.PositiveIntegerField("Номер")
    title = models.CharField("Название", max_length=200)
    statement = models.TextField("Условие", blank=True)

    panels = [FieldPanel("number"), FieldPanel("title"), FieldPanel("statement")]


class RegionalPhoto(Orderable):
    tournament = ParentalKey(
        RegionalTournament,
        on_delete=models.CASCADE,
        related_name="photos",
    )
    image = models.ForeignKey(
        "wagtailimages.Image",
        on_delete=models.SET_NULL,
        related_name="+",
        verbose_name="Файл",
        null=True,
        blank=True,
    )
    external_url = models.TextField("Или внешняя ссылка", blank=True)
    original_url = models.URLField("Оригинал", blank=True)
    caption = models.CharField("Подпись", max_length=200, blank=True)

    panels = [
        FieldPanel("image"),
        FieldPanel("external_url"),
        FieldPanel("original_url"),
        FieldPanel("caption"),
    ]

    @property
    def src(self):
        if self.external_url:
            return vk_sized(self.external_url, "1280x0")
        if self.image:
            return self.image.file.url
        return ""

    @property
    def thumb_src(self):
        if self.external_url:
            return vk_sized(self.external_url, "240x0")
        if self.image:
            return self.image.file.url
        return ""

    @property
    def original(self):
        return self.original_url or ""
