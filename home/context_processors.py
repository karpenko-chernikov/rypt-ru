from home.models import ContentPage, HomePage, NewsIndexPage, NewsPage, TournamentIndexPage, TournamentPage

NAV_SLUGS = [
    ("news", "Новости"),
    ("tournaments", "Сезоны"),
    ("rules", "Правила"),
    ("russia", "Турниры в России"),
    ("materials", "Полезные материалы"),
    ("partners", "Партнеры"),
    ("contacts", "Контакты"),
]


def _same_path(a, b):
    return (a or "/").rstrip("/") == (b or "/").rstrip("/")


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
        tournament_index = TournamentIndexPage.objects.child_of(home).live().first()
        slides.append(
            {
                "title": "Главная",
                "url": "/",
                "kind": "home",
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
            page = pages.get(slug)
            if page:
                items.append({"title": title, "page": page, "url": None})
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
            is_deck = True
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
