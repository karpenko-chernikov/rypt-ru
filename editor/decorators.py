from functools import wraps

from django.contrib.auth.views import redirect_to_login
from django.http import HttpResponseForbidden

from editor.authz import user_is_editor


def staff_required(view):
    """Доступ в кабинет: группа Editors (или superuser). Имя сохранено для совместимости."""

    @wraps(view)
    def wrapped(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect_to_login(request.get_full_path(), login_url="editor:login")
        if not user_is_editor(request.user):
            return HttpResponseForbidden("Нужны права редактора.")
        return view(request, *args, **kwargs)

    return wrapped


editor_required = staff_required
