from django.core.management import call_command
from django.core.management.base import BaseCommand
from wagtail.models import Site

from home.models import (
    ContactsPage,
    ContentPage,
    HomePage,
    MaterialsIndexPage,
    NewsIndexPage,
    NewsPage,
    RussiaTournamentsPage,
    TournamentIndexPage,
    TrainingBoardPage,
)

MENU_PAGES = [
    ("rules", "Правила"),
    ("partners", "Партнеры"),
]

DEFAULT_INTRO = (
    "<p>Турнир юных физиков (ТЮФ) — это ежегодное коллективное состязание "
    "школьников старших классов в умении решать сложные научные проблемы, "
    "убедительно представлять свои решения, отстаивать их в научных дискуссиях — "
    "физбоях. Турнир проходит ежегодно начиная с марта 1979 года, сохраняя свою "
    "суть -- обсуждение общих семнадцати заданий в течение всего года.</p>"
)


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
        home.intro = home.intro or DEFAULT_INTRO
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

        old_russia = ContentPage.objects.child_of(home).filter(slug="russia").first()
        if old_russia:
            old_russia.delete()

        russia = RussiaTournamentsPage.objects.child_of(home).first()
        if not russia:
            russia = RussiaTournamentsPage(
                title="Турниры в России",
                slug="russia",
                intro=(
                    "<p>Региональные турниры по субъектам РФ. "
                    "Наведите на область — справа откроется карточка турнира.</p>"
                ),
            )
            home.add_child(instance=russia)
        else:
            russia.title = "Турниры в России"
            if not russia.intro:
                russia.intro = (
                    "<p>Региональные турниры по субъектам РФ. "
                    "Наведите на область — справа откроется карточка турнира.</p>"
                )
        russia.save_revision().publish()

        old_materials = ContentPage.objects.child_of(home).filter(slug="materials").first()
        old_materials_intro = old_materials.body if old_materials else ""
        if old_materials:
            old_materials.delete()

        materials = MaterialsIndexPage.objects.child_of(home).first()
        if not materials:
            materials = MaterialsIndexPage(
                title="Полезные материалы",
                slug="materials",
                intro=old_materials_intro,
            )
            home.add_child(instance=materials)
        else:
            materials.title = "Полезные материалы"
            if old_materials_intro and not materials.intro:
                materials.intro = old_materials_intro
        materials.save_revision().publish()

        keep = {"news", "russia", *(slug for slug, _title in MENU_PAGES)}
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

        contacts = ContactsPage.objects.child_of(home).first()
        if not contacts:
            contacts = ContactsPage(title="Контакты", slug="contacts")
            home.add_child(instance=contacts)
        else:
            contacts.title = "Контакты"
            contacts.slug = "contacts"
        contacts.save_revision().publish()

        training_board = TrainingBoardPage.objects.child_of(home).first()
        if not training_board:
            training_board = TrainingBoardPage(
                title="Доска заявок",
                slug="training-board",
                intro="",
            )
            home.add_child(instance=training_board)
        else:
            training_board.title = "Доска заявок"
            training_board.slug = "training-board"
        training_board.save_revision().publish()

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

        call_command("fill_russia_regions")
        self.stdout.write(self.style.SUCCESS("Меню обновлено, тексты сняты."))
