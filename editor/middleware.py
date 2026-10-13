"""На staging/production /redaktura/ и /django-admin/ не монтируются.
Middleware — страховка, если маршруты когда-нибудь снова появятся.
Локально (DEBUG=True) админка нужна, поэтому блокируем только вне DEBUG."""

from django.conf import settings
from django.http import HttpResponseNotFound


class BlockCmsAdminForEditorsMiddleware:
    BLOCKED_PREFIXES = ("/redaktura/", "/django-admin/")

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if not settings.DEBUG:
            path = request.path
            if any(path.startswith(p) for p in self.BLOCKED_PREFIXES):
                return HttpResponseNotFound()
        return self.get_response(request)
