"""/django-admin/ вне DEBUG недоступен всегда.
/redaktura/ (Wagtail) вне DEBUG доступна только при ENABLE_WAGTAIL_ADMIN (staging).
Middleware — страховка, если маршруты когда-нибудь появятся без флага.
Локально (DEBUG=True) обе админки нужны, поэтому блокируем только вне DEBUG."""

from django.conf import settings
from django.http import HttpResponseNotFound


class BlockCmsAdminForEditorsMiddleware:
    BLOCKED_PREFIXES = ("/django-admin/",)
    WAGTAIL_ADMIN_PREFIX = "/redaktura/"

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if not settings.DEBUG:
            path = request.path
            if any(path.startswith(p) for p in self.BLOCKED_PREFIXES):
                return HttpResponseNotFound()
            if (
                path.startswith(self.WAGTAIL_ADMIN_PREFIX)
                and not getattr(settings, "ENABLE_WAGTAIL_ADMIN", False)
            ):
                return HttpResponseNotFound()
        return self.get_response(request)
