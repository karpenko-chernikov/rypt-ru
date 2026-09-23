from django.conf import settings
from django.urls import include, path

from wagtail import urls as wagtail_urls
from wagtail.documents import urls as wagtaildocs_urls

from search import views as search_views

urlpatterns = [
    # Единственный интерфейс редактирования для людей.
    path("dlya-redaktorov/", include("editor.urls")),
    path("documents/", include(wagtaildocs_urls)),
    path("search/", search_views.search, name="search"),
]

# Wagtail/django-admin — только локально (DEBUG), на сайте их нет.
if settings.DEBUG:
    from django.contrib import admin
    from wagtail.admin import urls as wagtailadmin_urls

    urlpatterns = [
        path("django-admin/", admin.site.urls),
        path("redaktura/", include(wagtailadmin_urls)),
    ] + urlpatterns


if settings.DEBUG:
    from django.conf.urls.static import static
    from django.contrib.staticfiles.urls import staticfiles_urlpatterns

    urlpatterns += staticfiles_urlpatterns()
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

urlpatterns = urlpatterns + [
    path("", include(wagtail_urls)),
]
