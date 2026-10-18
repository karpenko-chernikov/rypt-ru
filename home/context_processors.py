from home.models import (
    ContactsPage,
    ContentPage,
    HomePage,
    MaterialsIndexPage,
    NewsIndexPage,
    NewsPage,
    RussiaTournamentsPage,
    TournamentIndexPage,
    TournamentPage,
    TrainingBoardPage,
    build_russia_problems_matrix,
    load_russia_svg,
)
from home.documents import CHARTER_DOCX, CHARTER_HTML, REGULATION_PDF, VOK
from home.partners import PARTNERS
from home.regions import REGIONS
import json

NAV_SLUGS = [
    ("news", "Новости"),
    ("tournaments", "Сезоны"),
    ("rules", "Документы"),
    ("russia", "Турниры в России"),
    ("training-board", "Доска заявок"),
    ("materials", "Полезные материалы"),
    ("partners", "Партнеры"),
    ("contacts", "Контакты"),
]


def _same_path(a, b):
    return (a or "/").rstrip("/") == (b or "/").rstrip("/")


def _russia_slide(russia_page, request):
    russia_page.regions.prefetch_related("season_problem_links__problem", "photos")
    return {
        "title": "Турниры в России",
        "url": russia_page.get_url(request=request),
        "kind": "russia",
        "intro": russia_page.intro,
        "svg": load_russia_svg(),
        "regions_json": json.dumps(russia_page.regions_payload(), ensure_ascii=False),
        "region_names_json": json.dumps(REGIONS, ensure_ascii=False),
        "problems_matrix": build_russia_problems_matrix(russia_page),
    }


def site_nav(request):
    home = HomePage.objects.live().first()
    news_index = None
    items = []
    slides = []
    if home:
        news_index = NewsIndexPage.objects.child_of(home).live().first()
        pages = {
            page.slug: page
            for page in ContentPage.objects.child_of(home).live().public()
        }
        russia_page = (
            RussiaTournamentsPage.objects.child_of(home).live().public().first()
        )
        materials_page = (
            MaterialsIndexPage.objects.child_of(home).live().public().first()
        )
        contacts_page = ContactsPage.objects.child_of(home).live().public().first()
        training_board = TrainingBoardPage.objects.child_of(home).live().public().first()
        tournament_index = TournamentIndexPage.objects.child_of(home).live().first()
        slides.append(
            {
                "title": "Главная",
                "url": "/",
                "kind": "home",
                "info": home.info_payload(),
            }
        )
        for slug, title in NAV_SLUGS:
            if slug == "news":
                if news_index:
                    items.append({"title": title, "page": news_index, "url": None})
                    slides.append(
                        {
                            "title": title,
                            "url": news_index.get_url(request=request),
                            "kind": "news",
                            "intro": news_index.intro,
                            "news": list(
                                NewsPage.objects.child_of(news_index)
                                .live()
                                .public()
                                .order_by("-date", "-first_published_at")
                            ),
                        }
                    )
                continue
            if slug == "tournaments":
                if tournament_index:
                    items.append({"title": title, "page": tournament_index, "url": None})
                    seasons = list(
                        TournamentPage.objects.child_of(tournament_index)
                        .live()
                        .public()
                        .order_by("-year")
                    )
                    slides.append(
                        {
                            "title": title,
                            "url": tournament_index.get_url(request=request),
                            "kind": "tournaments",
                            "seasons": seasons,
                            "current": next((s for s in seasons if s.is_current), None),
                        }
                    )
                continue
            if slug == "russia":
                if russia_page:
                    items.append({"title": title, "page": russia_page, "url": None})
                    slides.append(_russia_slide(russia_page, request))
                continue
            if slug == "materials":
                if materials_page:
                    items.append({"title": title, "page": materials_page, "url": None})
                    slides.append(
                        {
                            "title": title,
                            "url": materials_page.get_url(request=request),
                            "kind": "materials",
                            "intro": materials_page.intro,
                            "groups": materials_page.groups_data(),
                        }
                    )
                continue
            if slug == "contacts":
                if contacts_page:
                    items.append({"title": title, "page": contacts_page, "url": None})
                    slides.append(
                        {
                            "title": title,
                            "url": contacts_page.get_url(request=request),
                            "kind": "contacts",
                            "sections": contacts_page.sections_data(),
                        }
                    )
                continue
            if slug == "training-board":
                if training_board:
                    items.append({"title": title, "page": training_board, "url": None})
                    slides.append(
                        {
                            "title": title,
                            "url": training_board.get_url(request=request),
                            "kind": "training_board",
                        }
                    )
                continue
            page = pages.get(slug)
            if page:
                items.append({"title": title, "page": page, "url": None})
                if slug == "partners":
                    slides.append(
                        {
                            "title": title,
                            "url": page.get_url(request=request),
                            "kind": "partners",
                            "partners": PARTNERS,
                        }
                    )
                elif slug == "rules":
                    slides.append(
                        {
                            "title": title,
                            "url": page.get_url(request=request),
                            "kind": "documents",
                            "regulation_pdf": REGULATION_PDF,
                            "charter_docx": CHARTER_DOCX,
                            "charter_html": CHARTER_HTML,
                            "vok": VOK,
                        }
                    )
                else:
                    slides.append(
                        {
                            "title": title,
                            "url": page.get_url(request=request),
                            "kind": "page",
                            "body": page.body,
                        }
                    )

    path = request.path
    slide_index = 0
    is_deck = False
    for i, slide in enumerate(slides):
        if _same_path(slide["url"], path):
            slide_index = i
            # PDF/iframe внутри CSS-transform колоды ломает клики и масштаб —
            # документы всегда как обычная страница.
            is_deck = slide.get("kind") not in ("documents", "training_board")
            break
    for i, slide in enumerate(slides):
        url = (slide.get("url") or "/").rstrip("/") or "/"
        current_path = (path or "/").rstrip("/") or "/"
        if is_deck:
            slide["is_now"] = i == slide_index
        elif url == "/":
            slide["is_now"] = current_path == "/"
        else:
            slide["is_now"] = current_path == url or current_path.startswith(url + "/")

    return {
        "nav_home": home,
        "nav_items": items,
        "nav_old_site": "https://old.rypt.ru",
        "slides": slides,
        "slide_index": slide_index,
        "is_deck": is_deck,
    }
