import html as html_lib
import json
import re
from pathlib import Path

from django.conf import settings
from django.db import models
from django.core.exceptions import ValidationError
from modelcluster.fields import ParentalKey
from modelcluster.models import ClusterableModel
from wagtail.admin.panels import FieldPanel, InlinePanel, MultiFieldPanel
from wagtail.fields import RichTextField
from wagtail.models import Orderable, Page
from wagtail.rich_text import expand_db_html

from home.regions import REGION_CHOICES, REGIONS


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

    content_panels = Page.content_panels + [
        FieldPanel("date"),
        FieldPanel("body"),
    ]
    parent_page_types = ["home.NewsIndexPage"]
    subpage_types = []


class ContentPage(Page):
    body = RichTextField(
        "Текст страницы",
        blank=True,
        features=["h2", "h3", "bold", "italic", "link", "ol", "ul"],
    )

    content_panels = Page.content_panels + [FieldPanel("body")]
    parent_page_types = ["home.HomePage"]
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
        """Данные для JS: код региона → карточка турнира."""
        out = {}
        for reg in self.regions.all():
            out[reg.region_code] = reg.as_payload()
        return out

    def get_context(self, request):
        context = super().get_context(request)
        context["russia_svg"] = load_russia_svg()
        context["regions_json"] = json.dumps(self.regions_payload(), ensure_ascii=False)
        context["region_names_json"] = json.dumps(REGIONS, ensure_ascii=False)
        context["active_region_codes"] = [
            r.region_code for r in self.regions.all() if r.has_tournament
        ]
        return context


class RegionalTournament(ClusterableModel, Orderable):
    page = ParentalKey(
        RussiaTournamentsPage,
        on_delete=models.CASCADE,
        related_name="regions",
    )
    region_code = models.CharField(
        "Субъект РФ",
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
        unique_together = [("page", "region_code")]

    def __str__(self):
        return f"{self.region_name}: {self.title}"

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

    def as_payload(self):
        return {
            "code": self.region_code,
            "region": self.region_name,
            "has_tournament": self.has_tournament,
            "title": self.title,
            "city": self.city,
            "when": self.when_label(),
            "contacts": self.contacts,
            "info_html": expand_db_html(self.info) if self.info else "",
            "problems": [
                {
                    "number": p.number,
                    "title": p.title,
                    "statement": p.statement,
                }
                for p in self.problems.all().order_by("number", "sort_order")
            ],
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


class RegionalProblem(Orderable):
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
