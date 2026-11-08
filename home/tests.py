"""Тесты защиты региональной карты от XSS.

Проверяют два независимых пути:
1) JSON в <script type="application/json"> больше не выводится через |safe,
   а рендерится через json_script, который экранирует </script>;
2) HTML поля «О турнире» (info) пропускается через allowlist-санитайзер
   на путях записи (форма) и рендера (as_payload).
"""

from django.template import Context, Template
from django.test import SimpleTestCase, TestCase
from wagtail.models import Page, PageViewRestriction
from wagtail.rich_text import expand_db_html

from editor.forms import RegionalTournamentForm
from home.html_sanitize import sanitize_limited_html
from home.models import (
    HomePage,
    TournamentIndexPage,
    TournamentPage,
    current_tournament_season,
    open_all_russia_payload,
    public_current_tournament_season,
)


class SanitizerTests(SimpleTestCase):
    def test_preserves_allowed_formatting(self):
        value = (
            "<p>Привет <strong>мир</strong> и <em>курсив</em></p>"
            "<ul><li>пункт</li></ul>"
            '<a href="https://example.com" title="пример">ссылка</a>'
        )
        out = sanitize_limited_html(value)
        self.assertIn("<strong>", out)
        self.assertIn("<em>", out)
        self.assertIn("<ul>", out)
        self.assertIn("<li>", out)
        self.assertIn('href="https://example.com"', out)

    def test_strips_script_and_event_handlers(self):
        value = '<script>alert(1)</script><img src=x onerror="alert(1)"><p onclick="x">текст</p>'
        out = sanitize_limited_html(value)
        self.assertNotIn("<script", out)
        self.assertNotIn("<img", out)
        self.assertNotIn("onerror", out)
        self.assertNotIn("onclick", out)
        self.assertIn("текст", out)

    def test_strips_javascript_url(self):
        out = sanitize_limited_html('<a href="javascript:alert(1)">x</a>')
        self.assertNotIn("javascript:", out)

    def test_keeps_relative_url(self):
        out = sanitize_limited_html('<a href="/docs">документы</a>')
        self.assertIn('href="/docs"', out)

    def test_empty_input(self):
        self.assertEqual(sanitize_limited_html(""), "")
        self.assertEqual(sanitize_limited_html(None), "")


class FormCleanInfoTests(SimpleTestCase):
    def test_clean_info_sanitizes(self):
        form = RegionalTournamentForm(
            data={"info": '<script>alert(1)</script><p onmouseover="x">текст</p><a href="javascript:alert(1)">ссылка</a>'},
            region_choices=[("77", "Москва")],
            season_problem_choices=[("1", "Задача 1")],
        )
        form.full_clean()
        cleaned = form.cleaned_data["info"]
        self.assertNotIn("<script", cleaned)
        self.assertNotIn("onmouseover", cleaned)
        self.assertNotIn("javascript:", cleaned)
        self.assertIn("текст", cleaned)


class RenderPathSanitizeTests(SimpleTestCase):
    def test_info_html_is_sanitized_after_expand(self):
        raw = '<p onclick="x">текст</p><script>alert(1)</script>'
        out = sanitize_limited_html(expand_db_html(raw))
        self.assertNotIn("onclick", out)
        self.assertNotIn("<script", out)
        self.assertIn("текст", out)


class JsonScriptTests(SimpleTestCase):
    def test_script_tag_sequence_is_escaped(self):
        payload = {"title": "</script><script>alert(1)</script>"}
        out = Template('{{ value|json_script:"russia-data" }}').render(
            Context({"value": payload})
        )
        self.assertNotIn("</script><script>", out)
        self.assertIn("\\u003C/script\\u003E", out)
        self.assertIn('id="russia-data"', out)


class SeasonVisibilityTests(TestCase):
    """SEC-04: публичные данные не раскрывают черновики и закрытые сезоны."""

    def setUp(self):
        root = Page.get_first_root_node()
        self.home = HomePage(title="Главная", slug="home-sec04", intro="")
        root.add_child(instance=self.home)
        self.home.save_revision().publish()

        self.tournament_index = TournamentIndexPage(
            title="Сезоны", slug="tournaments", intro=""
        )
        self.home.add_child(instance=self.tournament_index)
        self.tournament_index.save_revision().publish()

    def _season(self, slug, year, is_current, live=True):
        season = TournamentPage(
            title=f"Сезон {year}",
            slug=slug,
            year=year,
            is_current=is_current,
            live=live,
        )
        self.tournament_index.add_child(instance=season)
        if live:
            season.save_revision().publish()
        return season

    def test_editor_helper_returns_draft_but_public_does_not(self):
        draft = self._season("draft-season", 2027, True, live=False)
        self.assertEqual(current_tournament_season(), draft)
        self.assertIsNone(public_current_tournament_season())

    def test_public_season_helper_excludes_private(self):
        private = self._season("private-season", 2027, True)
        PageViewRestriction.objects.create(
            page=private,
            restriction_type=PageViewRestriction.LOGIN,
        )
        self.assertEqual(current_tournament_season(), private)
        self.assertIsNone(public_current_tournament_season())

    def test_open_all_russia_payload_hides_private_season(self):
        season = self._season("private-season", 2027, True)
        PageViewRestriction.objects.create(
            page=season,
            restriction_type=PageViewRestriction.LOGIN,
        )
        payload = open_all_russia_payload()
        self.assertEqual(payload["problems"], [])
        self.assertEqual(payload["season_label"], "")
