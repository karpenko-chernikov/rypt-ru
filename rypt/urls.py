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

# Wagtail/django-admin — локально (DEBUG) или когда явно включено (staging).
# На боевом сайте их нет: ENABLE_WAGTAIL_ADMIN там не ставится.
if settings.DEBUG:
    from django.contrib import admin
    from wagtail.admin import urls as wagtailadmin_urls

    urlpatterns = [
        path("django-admin/", admin.site.urls),
        path("redaktura/", include(wagtailadmin_urls)),
    ] + urlpatterns
elif getattr(settings, "ENABLE_WAGTAIL_ADMIN", False):
    from wagtail.admin import urls as wagtailadmin_urls

    urlpatterns = [
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
