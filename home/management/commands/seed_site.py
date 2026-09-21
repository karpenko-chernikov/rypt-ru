from django.core.management.base import BaseCommand
from wagtail.models import Site

from home.models import (
    ContentPage,
    HomePage,
    NewsIndexPage,
    NewsPage,
    TournamentIndexPage,
)

MENU_PAGES = [
    ("rules", "Правила"),
    ("russia", "Турниры в России"),
    ("materials", "Полезные материалы"),
    ("partners", "Партнеры"),
    ("contacts", "Контакты"),
]


class Command(BaseCommand):
    help = "Создаёт разделы меню и убирает черновые тексты."

    def handle(self, *args, **options):
        home = HomePage.objects.first()
        if not home:
            self.stderr.write("Главная страница не найдена. Сначала сделайте migrate.")
            return

        home.title = "Главная"
        home.draft_title = "Главная"
        home.lead = ""
        home.intro = ""
        home.season_label = ""
        home.reporter_text = ""
        home.opponent_text = ""
        home.reviewer_text = ""
        home.save_revision().publish()

        site = Site.objects.filter(is_default_site=True).first()
        if site:
            site.site_name = "Российский Турнир Юных Физиков"
            site.save()

        news_index = NewsIndexPage.objects.child_of(home).first()
        if not news_index:
            news_index = NewsIndexPage(title="Новости", slug="news", intro="")
            home.add_child(instance=news_index)
        else:
            news_index.title = "Новости"
            news_index.intro = ""
        news_index.save_revision().publish()

        for news in NewsPage.objects.child_of(news_index):
            news.delete()

        keep = {"news", *(slug for slug, _title in MENU_PAGES)}
        for page in ContentPage.objects.child_of(home):
            if page.slug not in keep:
                page.delete()

        for slug, title in MENU_PAGES:
            page = ContentPage.objects.child_of(home).filter(slug=slug).first()
            if not page:
                page = ContentPage(title=title, slug=slug, body="")
                home.add_child(instance=page)
            else:
                page.title = title
                page.body = ""
            page.save_revision().publish()

        tournaments = TournamentIndexPage.objects.child_of(home).first()
        if not tournaments:
            tournaments = TournamentIndexPage(
                title="Сезоны",
                slug="tournaments",
                intro="",
            )
            home.add_child(instance=tournaments)
        else:
            tournaments.title = "Сезоны"
            tournaments.intro = ""
        tournaments.save_revision().publish()

        self.stdout.write(self.style.SUCCESS("Меню обновлено, тексты сняты."))
