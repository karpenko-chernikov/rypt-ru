"""Блокировка Wagtail/django-admin для обычных редакторов кабинета."""

from django.http import HttpResponseForbidden

from editor.authz import user_is_editor


class BlockCmsAdminForEditorsMiddleware:
    """
    Редакторы кабинета не должны попадать в /redaktura/ и /django-admin/.
    Суперадмины — могут (отладка).
    """

    BLOCKED_PREFIXES = ("/redaktura/", "/django-admin/")

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        path = request.path
        if any(path.startswith(p) for p in self.BLOCKED_PREFIXES):
            user = getattr(request, "user", None)
            if user is not None and user.is_authenticated:
                if user_is_editor(user) and not user.is_superuser:
                    return HttpResponseForbidden(
                        "Кабинет редактора — только /dlya-redaktorov/. "
                        "Админка Wagtail закрыта для редакторов."
                    )
        return self.get_response(request)
