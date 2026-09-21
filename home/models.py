import html as html_lib
import re

from django.db import models
from django.core.exceptions import ValidationError
from modelcluster.fields import ParentalKey
from wagtail.admin.panels import FieldPanel, InlinePanel, MultiFieldPanel
from wagtail.fields import RichTextField
from wagtail.models import Orderable, Page


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
    results_more_url = models.URLField("Подробные результаты, ссылка", blank=True)
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
