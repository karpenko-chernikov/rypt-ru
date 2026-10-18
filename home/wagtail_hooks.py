"""Регистрация дополнительных rich-text возможностей редактора Wagtail."""

from wagtail import hooks
from wagtail.admin.rich_text.converters.html_to_contentstate import (
    InlineStyleElementHandler,
)
from wagtail.admin.rich_text.editors.draftail.features import InlineStyleFeature
from wagtail.snippets.models import register_snippet
from wagtail.snippets.views.snippets import SnippetViewSet

from home.models import TrainingBoardCard


class TrainingBoardCardViewSet(SnippetViewSet):
    """Админка Wagtail: список и удаление объявлений с доски заявок."""

    model = TrainingBoardCard
    list_display = ("team_name", "dates", "city", "created_at")
    ordering = ("-created_at",)
    search_fields = ("team_name", "city", "contact", "comments")


register_snippet(TrainingBoardCard, viewset=TrainingBoardCardViewSet)


@hooks.register("register_rich_text_features")
def register_underline_feature(features):
    """Подчёркнутый текст: кнопка «U» в панели Draftail, рендер в <u>."""
    feature_name = "underline"
    type_ = "UNDERLINE"
    tag = "u"

    control = {
        "type": type_,
        "label": "U",
        "description": "Подчёркнутый текст",
        "style": {"textDecoration": "underline"},
    }

    features.register_editor_plugin(
        "draftail", feature_name, InlineStyleFeature(control)
    )

    db_conversion = {
        "from_database_format": {tag: InlineStyleElementHandler(type_)},
        "to_database_format": {"style_map": {type_: {"element": tag}}},
    }

    features.register_converter_rule("contentstate", feature_name, db_conversion)
