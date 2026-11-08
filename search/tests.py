"""Регрессионные тесты SEC-04: приватность Wagtail в поиске.

Проверяют, что анонимный поиск не раскрывает:
- черновики (live=False),
- страницы с прямым ограничением доступа,
- страницы с унаследованным ограничением доступа (потомки закрытых страниц),
при этом публичные страницы остаются в выдаче.
"""

from django.test import TestCase
from wagtail.models import Page, PageViewRestriction, Site

from home.models import ContentPage, HomePage


class SearchPrivacyTests(TestCase):
    def setUp(self):
        root = Page.get_first_root_node()
        self.home = HomePage(title="Главная", slug="home-sec04", intro="")
        root.add_child(instance=self.home)
        self.home.save_revision().publish()

        Site.objects.all().delete()
        Site.objects.create(
            hostname="testserver",
            root_page=self.home,
            is_default_site=True,
        )

        self.public_page = self._add_content_page("Публичная страница", "public-page")

        self.private_page = self._add_content_page("Закрытая страница", "private-page")
        PageViewRestriction.objects.create(
            page=self.private_page,
            restriction_type=PageViewRestriction.LOGIN,
        )

        self.draft_page = self._add_content_page(
            "Черновая страница", "draft-page", live=False
        )

        private_parent = self._add_plain_page("Закрытый раздел", "private-section")
        PageViewRestriction.objects.create(
            page=private_parent,
            restriction_type=PageViewRestriction.LOGIN,
        )
        self.inherited_page = self._add_plain_page(
            "Наследуемая страница", "inherited-page", parent=private_parent
        )

    def _add_content_page(self, title, slug, live=True):
        page = ContentPage(title=title, slug=slug, body="", live=live)
        self.home.add_child(instance=page)
        if live:
            page.save_revision().publish()
        return page

    def _add_plain_page(self, title, slug, parent=None, live=True):
        parent = parent or self.home
        page = Page(title=title, slug=slug, live=live)
        parent.add_child(instance=page)
        if live:
            page.save_revision().publish()
        return page

    def test_anonymous_search_hides_private_draft_and_inherited(self):
        response = self.client.get("/search/", {"query": "страница"})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Публичная страница")
        self.assertNotContains(response, "Закрытая страница")
        self.assertNotContains(response, "Черновая страница")
        self.assertNotContains(response, "Наследуемая страница")
