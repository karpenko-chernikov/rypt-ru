from __future__ import annotations

from datetime import timedelta

from django.contrib import messages
from django.contrib.auth import login, logout
from django.core.files.images import ImageFile
from django.db import transaction
from django.http import Http404, HttpResponseForbidden
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_http_methods, require_POST
from wagtail.images.models import Image

from editor.authz import user_is_editor
from editor.decorators import staff_required
from editor.forms import (
    EditorLoginForm,
    EditorRegisterForm,
    InviteCreateForm,
    IyptForm,
    LinkForm,
    OpenNewSeasonForm,
    PhotoAlbumForm,
    PhotoUploadForm,
    ProblemForm,
    RegionalTournamentForm,
    ResultRowForm,
    ResultsMoreForm,
    ScanUploadForm,
    SeasonCreateForm,
    SeasonMetaForm,
)
from editor.models import EditorChangeLog, EditorInvite
from editor.security import client_ip, invite_code, safe_redirect_url, throttle
from editor.services import (
    archive_current,
    create_season,
    log_change,
    make_current,
    open_new_season,
    publish_page,
)
from home.models import (
    RegionalPhoto,
    RegionalProblem,
    RegionalTournament,
    RussiaTournamentsPage,
    TournamentLink,
    TournamentPage,
    TournamentPhoto,
    TournamentProblem,
    TournamentProblemScan,
    TournamentResultRow,
)
from home.regions import REGION_CHOICES, REGIONS

RESULT_KINDS = [
    (TournamentResultRow.KIND_RANKING, "Общий рейтинг"),
    (TournamentResultRow.KIND_LEAGUE_A, "Высшая лига"),
    (TournamentResultRow.KIND_LEAGUE_B, "Первая лига"),
    (TournamentResultRow.KIND_FINAL, "Финал высшей лиги"),
    (TournamentResultRow.KIND_FINAL_B, "Финал первой лиги"),
]

IYPT_KINDS = [
    (TournamentResultRow.KIND_IYPT_RANKING, "IYPT: рейтинг"),
    (TournamentResultRow.KIND_IYPT_FINAL, "IYPT: финал"),
]


def get_season(year: int) -> TournamentPage:
    page = TournamentPage.objects.filter(year=year).first()
    if not page:
        raise Http404("Сезон не найден")
    return page


def login_view(request):
    if user_is_editor(request.user):
        return redirect("editor:dashboard")
    form = EditorLoginForm(request, data=request.POST or None)
    if request.method == "POST":
        ip = client_ip(request)
        if throttle(f"editor-login:{ip}", limit=12, window=3600):
            return HttpResponseForbidden("Слишком много попыток входа. Подождите час.")
        if form.is_valid():
            user = form.get_user()
            if not user_is_editor(user):
                messages.error(request, "У этого пользователя нет прав редактора.")
            else:
                login(request, user)
                request.session.cycle_key()
                return redirect(safe_redirect_url(request, request.GET.get("next")))
        else:
            # Неудачный логин тоже крутит счётчик (уже учтён выше).
            pass
    return render(request, "editor/login.html", {"form": form})


def logout_view(request):
    logout(request)
    return redirect("editor:login")


def register_view(request, code):
    """Регистрация только по одноразовому приглашению."""
    invite = EditorInvite.objects.filter(code=code).first()
    if not invite or not invite.is_usable:
        raise Http404()
    if user_is_editor(request.user):
        return redirect("editor:dashboard")
    form = EditorRegisterForm(request.POST or None)
    if request.method == "POST":
        ip = client_ip(request)
        if throttle(f"editor-reg:{ip}", limit=5, window=3600):
            return HttpResponseForbidden("Слишком много регистраций с этого адреса.")
        if form.is_valid():
            with transaction.atomic():
                locked = EditorInvite.objects.select_for_update().filter(pk=invite.pk).first()
                if not locked or not locked.is_usable:
                    raise Http404()
                user = form.save()
                locked.used_at = timezone.now()
                locked.used_by = user
                locked.save(update_fields=["used_at", "used_by"])
            login(request, user, backend="django.contrib.auth.backends.ModelBackend")
            request.session.cycle_key()
            log_change(
                user=user,
                action=EditorChangeLog.ACTION_CREATE,
                summary=f"Регистрация редактора «{user.username}» по приглашению",
                object_type="user",
                object_id=user.pk,
                object_label=user.username,
            )
            messages.success(request, "Аккаунт создан. Добро пожаловать в кабинет.")
            return redirect("editor:dashboard")
    return render(
        request,
        "editor/register.html",
        {"form": form, "invite_note": invite.note, "expires_at": invite.expires_at},
    )


@staff_required
def dashboard(request):
    current = TournamentPage.objects.filter(is_current=True).first()
    past = TournamentPage.objects.filter(is_current=False).order_by("-year")
    return render(
        request,
        "editor/dashboard.html",
        {"current": current, "past": past},
    )


@staff_required
@require_http_methods(["GET", "POST"])
def invites(request):
    form = InviteCreateForm(request.POST or None)
    created_url = None
    if request.method == "POST" and form.is_valid():
        ip = client_ip(request)
        if throttle(f"editor-invite:{request.user.pk}:{ip}", limit=20, window=3600):
            messages.error(request, "Слишком много приглашений за час.")
        else:
            days = form.cleaned_data["days_valid"]
            invite = EditorInvite.objects.create(
                code=invite_code(),
                note=form.cleaned_data.get("note") or "",
                created_by=request.user,
                expires_at=timezone.now() + timedelta(days=days),
            )
            created_url = request.build_absolute_uri(
                f"/dlya-redaktorov/priglashenie/{invite.code}/"
            )
            log_change(
                user=request.user,
                action=EditorChangeLog.ACTION_INVITE,
                summary=f"Приглашение создано"
                + (f" ({invite.note})" if invite.note else ""),
                object_type="invite",
                object_id=invite.pk,
                object_label=invite.code[:12] + "…",
                payload={"days": days, "note": invite.note},
            )
            messages.success(request, "Одноразовая ссылка создана. Передайте её лично.")
            form = InviteCreateForm()
    active = EditorInvite.objects.filter(revoked=False, used_at__isnull=True).order_by(
        "-created_at"
    )[:50]
    recent = (
        EditorInvite.objects.filter(used_at__isnull=False)
        | EditorInvite.objects.filter(revoked=True)
    ).distinct().order_by("-created_at")[:30]
    return render(
        request,
        "editor/invites.html",
        {
            "form": form,
            "created_url": created_url,
            "active": active,
            "recent": recent,
            "now": timezone.now(),
        },
    )


@staff_required
@require_POST
def invite_revoke(request, pk):
    invite = get_object_or_404(EditorInvite, pk=pk)
    if invite.used_at:
        messages.error(request, "Приглашение уже использовано.")
    else:
        invite.revoked = True
        invite.save(update_fields=["revoked"])
        log_change(
            user=request.user,
            action=EditorChangeLog.ACTION_INVITE,
            summary="Приглашение отозвано",
            object_type="invite",
            object_id=invite.pk,
            object_label=invite.code[:12] + "…",
        )
        messages.success(request, "Приглашение отозвано.")
    return redirect("editor:invites")


@staff_required
def journal(request):
    qs = EditorChangeLog.objects.select_related("user")
    year = request.GET.get("year")
    author = request.GET.get("author")
    if year and year.isdigit():
        page = TournamentPage.objects.filter(year=int(year)).first()
        if page:
            qs = qs.filter(object_type="season", object_id=page.pk)
    if author:
        qs = qs.filter(user__username=author)
    return render(
        request,
        "editor/journal.html",
        {
            "entries": qs[:200],
            "filter_year": year or "",
            "filter_author": author or "",
            "years": TournamentPage.objects.order_by("-year").values_list("year", flat=True),
        },
    )


@staff_required
def journal_detail(request, pk):
    import json

    entry = get_object_or_404(EditorChangeLog, pk=pk)
    payload_pretty = json.dumps(entry.payload, ensure_ascii=False, indent=2) if entry.payload else ""
    return render(
        request,
        "editor/journal_detail.html",
        {"entry": entry, "payload_pretty": payload_pretty},
    )


@staff_required
@require_http_methods(["GET", "POST"])
def season_create(request):
    form = SeasonCreateForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        year = form.cleaned_data["year"]
        try:
            page = create_season(
                year,
                make_current=form.cleaned_data["make_current"],
                user=request.user,
            )
        except ValueError as exc:
            messages.error(request, str(exc))
        else:
            messages.success(request, f"Сезон {page.display_title} создан.")
            return redirect("editor:season_detail", year=page.year)
    return render(request, "editor/season_create.html", {"form": form})


@staff_required
@require_http_methods(["GET", "POST"])
def season_open_new(request):
    form = OpenNewSeasonForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        year = form.cleaned_data["year"]
        try:
            page = open_new_season(year, user=request.user)
        except ValueError as exc:
            messages.error(request, str(exc))
        else:
            messages.success(
                request,
                f"Открыт новый сезон {page.display_title}. Прежний текущий перенесён в прошедшие.",
            )
            return redirect("editor:season_detail", year=page.year)
    return render(request, "editor/season_open_new.html", {"form": form})


@staff_required
def season_detail(request, year):
    page = get_season(year)
    return render(
        request,
        "editor/season_detail.html",
        {
            "page": page,
            "problems_count": page.problems.count(),
            "scans_count": page.problem_scans.count(),
            "results_count": page.ranking.exclude(
                kind__in=[
                    TournamentResultRow.KIND_IYPT_RANKING,
                    TournamentResultRow.KIND_IYPT_FINAL,
                ]
            ).count(),
            "iypt_rows": page.ranking.filter(
                kind__in=[
                    TournamentResultRow.KIND_IYPT_RANKING,
                    TournamentResultRow.KIND_IYPT_FINAL,
                ]
            ).count(),
            "photos_count": page.photos.count(),
            "links_count": page.links.count(),
            "has_iypt_text": bool(page.iypt_team or page.iypt_more_url),
            "has_albums": bool(page.album_urls()),
        },
    )


@staff_required
@require_http_methods(["GET", "POST"])
def season_meta(request, year):
    page = get_season(year)
    initial = {
        "city": page.city,
        "date_start": page.date_start,
        "date_end": page.date_end,
    }
    form = SeasonMetaForm(request.POST or None, initial=initial)
    if request.method == "POST" and form.is_valid():
        page.city = form.cleaned_data["city"]
        page.date_start = form.cleaned_data["date_start"]
        page.date_end = form.cleaned_data["date_end"]
        page.save()
        publish_page(page, user=request.user, summary=f"Обновлена шапка {page.display_title}")
        payload = {
            "city": form.cleaned_data["city"],
            "date_start": form.cleaned_data["date_start"].isoformat()
            if form.cleaned_data["date_start"]
            else None,
            "date_end": form.cleaned_data["date_end"].isoformat()
            if form.cleaned_data["date_end"]
            else None,
        }
        log_change(
            user=request.user,
            action=EditorChangeLog.ACTION_UPDATE,
            summary=f"Мета сезона {page.display_title}",
            object_id=page.pk,
            object_label=page.display_title,
            tab=EditorChangeLog.TAB_META,
            payload=payload,
        )
        messages.success(request, "Сохранено и опубликовано.")
        return redirect("editor:season_detail", year=year)
    return render(request, "editor/season_meta.html", {"page": page, "form": form})


@staff_required
@require_POST
def season_archive(request, year):
    page = get_season(year)
    if not page.is_current:
        messages.info(request, "Этот сезон уже не текущий.")
        return redirect("editor:season_detail", year=year)
    archive_current(user=request.user)
    messages.success(request, f"{page.display_title} перенесён в прошедшие.")
    return redirect("editor:dashboard")


@staff_required
@require_POST
def season_make_current(request, year):
    page = get_season(year)
    make_current(page, user=request.user)
    messages.success(request, f"{page.display_title} теперь текущий.")
    return redirect("editor:dashboard")


# ----- Задачи -----


@staff_required
def season_problems(request, year):
    page = get_season(year)
    return render(
        request,
        "editor/season_problems.html",
        {
            "page": page,
            "problems": page.problems.all().order_by("number"),
            "scans": page.problem_scans.all(),
            "scan_form": ScanUploadForm(),
            "problem_form": ProblemForm(),
        },
    )


@staff_required
@require_http_methods(["GET", "POST"])
def problem_add(request, year):
    page = get_season(year)
    form = ProblemForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        TournamentProblem.objects.create(
            page=page,
            number=form.cleaned_data["number"],
            title=form.cleaned_data["title"],
            statement=form.cleaned_data["statement"],
            sort_order=form.cleaned_data["number"] - 1,
        )
        publish_page(page, user=request.user, tab=EditorChangeLog.TAB_ZADACHI)
        log_change(
            user=request.user,
            action=EditorChangeLog.ACTION_CREATE,
            summary=f"Задача {form.cleaned_data['number']}. {form.cleaned_data['title']}",
            object_id=page.pk,
            object_label=page.display_title,
            tab=EditorChangeLog.TAB_ZADACHI,
            payload=form.cleaned_data,
        )
        messages.success(request, "Задача добавлена.")
        return redirect("editor:season_problems", year=year)
    return render(request, "editor/problem_form.html", {"page": page, "form": form, "title": "Новая задача"})


@staff_required
@require_http_methods(["GET", "POST"])
def problem_edit(request, year, pk):
    page = get_season(year)
    problem = get_object_or_404(TournamentProblem, pk=pk, page=page)
    form = ProblemForm(
        request.POST or None,
        initial={"number": problem.number, "title": problem.title, "statement": problem.statement},
    )
    if request.method == "POST" and form.is_valid():
        problem.number = form.cleaned_data["number"]
        problem.title = form.cleaned_data["title"]
        problem.statement = form.cleaned_data["statement"]
        problem.sort_order = form.cleaned_data["number"] - 1
        problem.save()
        publish_page(page, user=request.user, tab=EditorChangeLog.TAB_ZADACHI)
        log_change(
            user=request.user,
            action=EditorChangeLog.ACTION_UPDATE,
            summary=f"Изменена задача {problem.number}",
            object_id=page.pk,
            object_label=page.display_title,
            tab=EditorChangeLog.TAB_ZADACHI,
            payload=form.cleaned_data,
        )
        messages.success(request, "Задача сохранена.")
        return redirect("editor:season_problems", year=year)
    return render(request, "editor/problem_form.html", {"page": page, "form": form, "title": "Правка задачи"})


@staff_required
@require_POST
def problem_delete(request, year, pk):
    page = get_season(year)
    problem = get_object_or_404(TournamentProblem, pk=pk, page=page)
    num = problem.number
    problem.delete()
    publish_page(page, user=request.user, tab=EditorChangeLog.TAB_ZADACHI)
    log_change(
        user=request.user,
        action=EditorChangeLog.ACTION_DELETE,
        summary=f"Удалена задача {num}",
        object_id=page.pk,
        object_label=page.display_title,
        tab=EditorChangeLog.TAB_ZADACHI,
    )
    messages.success(request, "Задача удалена.")
    return redirect("editor:season_problems", year=year)


def _save_wagtail_image(upload, title: str) -> Image:
    image = Image(title=title, file=ImageFile(upload, name=upload.name))
    image.save()
    return image


@staff_required
@require_http_methods(["GET", "POST"])
def scan_add(request, year):
    page = get_season(year)
    form = ScanUploadForm(request.POST or None, request.FILES or None)
    if request.method == "POST" and form.is_valid():
        left = _save_wagtail_image(form.cleaned_data["image"], f"{page.display_title} скан")
        right = None
        if form.cleaned_data.get("image_right"):
            right = _save_wagtail_image(
                form.cleaned_data["image_right"],
                f"{page.display_title} скан R",
            )
        order = page.problem_scans.count()
        TournamentProblemScan.objects.create(
            page=page,
            image=left,
            image_right=right,
            caption=form.cleaned_data.get("caption") or "",
            sort_order=order,
        )
        publish_page(page, user=request.user, tab=EditorChangeLog.TAB_ZADACHI)
        log_change(
            user=request.user,
            action=EditorChangeLog.ACTION_CREATE,
            summary="Добавлен скан задач",
            object_id=page.pk,
            object_label=page.display_title,
            tab=EditorChangeLog.TAB_ZADACHI,
        )
        messages.success(request, "Скан добавлен.")
        return redirect("editor:season_problems", year=year)
    return render(request, "editor/scan_form.html", {"page": page, "form": form})


@staff_required
@require_POST
def scan_delete(request, year, pk):
    page = get_season(year)
    scan = get_object_or_404(TournamentProblemScan, pk=pk, page=page)
    scan.delete()
    publish_page(page, user=request.user, tab=EditorChangeLog.TAB_ZADACHI)
    log_change(
        user=request.user,
        action=EditorChangeLog.ACTION_DELETE,
        summary="Удалён скан задач",
        object_id=page.pk,
        object_label=page.display_title,
        tab=EditorChangeLog.TAB_ZADACHI,
    )
    messages.success(request, "Скан удалён.")
    return redirect("editor:season_problems", year=year)


# ----- Результаты -----


def _result_rows(page):
    return page.ranking.exclude(
        kind__in=[TournamentResultRow.KIND_IYPT_RANKING, TournamentResultRow.KIND_IYPT_FINAL]
    ).order_by("kind", "sort_order")


@staff_required
def season_results(request, year):
    page = get_season(year)
    rows = list(_result_rows(page))
    return render(
        request,
        "editor/season_results.html",
        {
            "page": page,
            "rows": rows,
            "has_results": bool(rows) or bool(page.results_more_url),
            "more_form": ResultsMoreForm(
                initial={
                    "results_more_url": page.results_more_url,
                    "results_more_label": page.results_more_label,
                }
            ),
            "row_form": ResultRowForm(kind_choices=RESULT_KINDS),
            "kinds": RESULT_KINDS,
        },
    )


@staff_required
@require_http_methods(["GET", "POST"])
def result_row_add(request, year):
    page = get_season(year)
    form = ResultRowForm(request.POST or None, kind_choices=RESULT_KINDS)
    if request.method == "POST" and form.is_valid():
        order = page.ranking.count()
        TournamentResultRow.objects.create(
            page=page,
            kind=form.cleaned_data["kind"],
            place=form.cleaned_data["place"],
            team=form.cleaned_data["team"],
            city=form.cleaned_data["city"],
            points=form.cleaned_data["points"],
            sort_order=order,
        )
        publish_page(page, user=request.user, tab=EditorChangeLog.TAB_REZULTATY)
        log_change(
            user=request.user,
            action=EditorChangeLog.ACTION_CREATE,
            summary=f"Строка результатов: {form.cleaned_data['team']}",
            object_id=page.pk,
            object_label=page.display_title,
            tab=EditorChangeLog.TAB_REZULTATY,
            payload=form.cleaned_data,
        )
        messages.success(request, "Строка добавлена. Вкладка «Результаты» появится на сайте.")
        return redirect("editor:season_results", year=year)
    return render(
        request,
        "editor/result_row_form.html",
        {"page": page, "form": form, "title": "Строка результатов"},
    )


@staff_required
@require_http_methods(["GET", "POST"])
def result_row_edit(request, year, pk):
    page = get_season(year)
    row = get_object_or_404(TournamentResultRow, pk=pk, page=page)
    if row.kind in (TournamentResultRow.KIND_IYPT_RANKING, TournamentResultRow.KIND_IYPT_FINAL):
        raise Http404()
    form = ResultRowForm(
        request.POST or None,
        kind_choices=RESULT_KINDS,
        initial={
            "kind": row.kind,
            "place": row.place,
            "team": row.team,
            "city": row.city,
            "points": row.points,
        },
    )
    if request.method == "POST" and form.is_valid():
        for field in ("kind", "place", "team", "city", "points"):
            setattr(row, field, form.cleaned_data[field])
        row.save()
        publish_page(page, user=request.user, tab=EditorChangeLog.TAB_REZULTATY)
        log_change(
            user=request.user,
            action=EditorChangeLog.ACTION_UPDATE,
            summary=f"Правка строки: {row.team}",
            object_id=page.pk,
            object_label=page.display_title,
            tab=EditorChangeLog.TAB_REZULTATY,
            payload=form.cleaned_data,
        )
        messages.success(request, "Строка сохранена.")
        return redirect("editor:season_results", year=year)
    return render(
        request,
        "editor/result_row_form.html",
        {"page": page, "form": form, "title": "Правка строки"},
    )


@staff_required
@require_POST
def result_row_delete(request, year, pk):
    page = get_season(year)
    row = get_object_or_404(TournamentResultRow, pk=pk, page=page)
    team = row.team
    row.delete()
    publish_page(page, user=request.user, tab=EditorChangeLog.TAB_REZULTATY)
    log_change(
        user=request.user,
        action=EditorChangeLog.ACTION_DELETE,
        summary=f"Удалена строка: {team}",
        object_id=page.pk,
        object_label=page.display_title,
        tab=EditorChangeLog.TAB_REZULTATY,
    )
    messages.success(request, "Строка удалена.")
    return redirect("editor:season_results", year=year)


@staff_required
@require_POST
def results_more_save(request, year):
    page = get_season(year)
    form = ResultsMoreForm(request.POST)
    if form.is_valid():
        page.results_more_url = form.cleaned_data["results_more_url"]
        page.results_more_label = form.cleaned_data["results_more_label"] or "Подробнее"
        page.save()
        publish_page(page, user=request.user, tab=EditorChangeLog.TAB_REZULTATY)
        log_change(
            user=request.user,
            action=EditorChangeLog.ACTION_UPDATE,
            summary="Ссылка «подробнее» результатов",
            object_id=page.pk,
            object_label=page.display_title,
            tab=EditorChangeLog.TAB_REZULTATY,
            payload=form.cleaned_data,
        )
        messages.success(request, "Ссылка сохранена.")
    return redirect("editor:season_results", year=year)


@staff_required
@require_POST
def results_clear(request, year):
    page = get_season(year)
    _result_rows(page).delete()
    page.results_more_url = ""
    page.results_more_label = ""
    page.save()
    publish_page(page, user=request.user, tab=EditorChangeLog.TAB_REZULTATY)
    log_change(
        user=request.user,
        action=EditorChangeLog.ACTION_DELETE,
        summary="Очищены результаты сезона",
        object_id=page.pk,
        object_label=page.display_title,
        tab=EditorChangeLog.TAB_REZULTATY,
    )
    messages.success(request, "Результаты очищены. Вкладка на сайте скроется.")
    return redirect("editor:season_results", year=year)


# ----- IYPT -----


@staff_required
@require_http_methods(["GET", "POST"])
def season_iypt(request, year):
    page = get_season(year)
    form = IyptForm(
        request.POST or None,
        initial={
            "iypt_team": page.iypt_team,
            "iypt_more_url": page.iypt_more_url,
            "iypt_more_label": page.iypt_more_label,
        },
    )
    if request.method == "POST" and form.is_valid():
        page.iypt_team = form.cleaned_data["iypt_team"]
        page.iypt_more_url = form.cleaned_data["iypt_more_url"] or ""
        page.iypt_more_label = form.cleaned_data["iypt_more_label"] or "Оригинал"
        page.save()
        publish_page(page, user=request.user, tab=EditorChangeLog.TAB_IYPT)
        log_change(
            user=request.user,
            action=EditorChangeLog.ACTION_UPDATE,
            summary="IYPT: текст и ссылка",
            object_id=page.pk,
            object_label=page.display_title,
            tab=EditorChangeLog.TAB_IYPT,
            payload=form.cleaned_data,
        )
        messages.success(request, "IYPT сохранён.")
        return redirect("editor:season_iypt", year=year)
    rows = page.ranking.filter(
        kind__in=[TournamentResultRow.KIND_IYPT_RANKING, TournamentResultRow.KIND_IYPT_FINAL]
    )
    return render(
        request,
        "editor/season_iypt.html",
        {
            "page": page,
            "form": form,
            "rows": rows,
            "row_form": ResultRowForm(kind_choices=IYPT_KINDS),
        },
    )


@staff_required
@require_http_methods(["GET", "POST"])
def iypt_row_add(request, year):
    page = get_season(year)
    form = ResultRowForm(request.POST or None, kind_choices=IYPT_KINDS)
    if request.method == "POST" and form.is_valid():
        TournamentResultRow.objects.create(
            page=page,
            kind=form.cleaned_data["kind"],
            place=form.cleaned_data["place"],
            team=form.cleaned_data["team"],
            city=form.cleaned_data["city"],
            points=form.cleaned_data["points"],
            sort_order=page.ranking.count(),
        )
        publish_page(page, user=request.user, tab=EditorChangeLog.TAB_IYPT)
        log_change(
            user=request.user,
            action=EditorChangeLog.ACTION_CREATE,
            summary=f"IYPT строка: {form.cleaned_data['team']}",
            object_id=page.pk,
            object_label=page.display_title,
            tab=EditorChangeLog.TAB_IYPT,
            payload=form.cleaned_data,
        )
        messages.success(request, "Строка IYPT добавлена.")
        return redirect("editor:season_iypt", year=year)
    return render(
        request,
        "editor/result_row_form.html",
        {"page": page, "form": form, "title": "Строка IYPT"},
    )


@staff_required
@require_POST
def iypt_row_delete(request, year, pk):
    page = get_season(year)
    row = get_object_or_404(TournamentResultRow, pk=pk, page=page)
    if row.kind not in (TournamentResultRow.KIND_IYPT_RANKING, TournamentResultRow.KIND_IYPT_FINAL):
        raise Http404()
    team = row.team
    row.delete()
    publish_page(page, user=request.user, tab=EditorChangeLog.TAB_IYPT)
    log_change(
        user=request.user,
        action=EditorChangeLog.ACTION_DELETE,
        summary=f"Удалена строка IYPT: {team}",
        object_id=page.pk,
        object_label=page.display_title,
        tab=EditorChangeLog.TAB_IYPT,
    )
    messages.success(request, "Строка удалена.")
    return redirect("editor:season_iypt", year=year)


# ----- Фото -----


@staff_required
@require_http_methods(["GET", "POST"])
def season_photos(request, year):
    page = get_season(year)
    album_form = PhotoAlbumForm(
        request.POST if request.POST.get("form") == "album" else None,
        initial={"photo_album_url": page.photo_album_url},
    )
    if request.method == "POST" and request.POST.get("form") == "album" and album_form.is_valid():
        page.photo_album_url = album_form.cleaned_data["photo_album_url"]
        page.save()
        publish_page(page, user=request.user, tab=EditorChangeLog.TAB_FOTO)
        log_change(
            user=request.user,
            action=EditorChangeLog.ACTION_UPDATE,
            summary="Альбомы фото",
            object_id=page.pk,
            object_label=page.display_title,
            tab=EditorChangeLog.TAB_FOTO,
        )
        messages.success(request, "Альбомы сохранены.")
        return redirect("editor:season_photos", year=year)
    return render(
        request,
        "editor/season_photos.html",
        {
            "page": page,
            "photos": page.photos.all(),
            "album_form": album_form,
            "upload_form": PhotoUploadForm(),
        },
    )


@staff_required
@require_http_methods(["GET", "POST"])
def photo_add(request, year):
    page = get_season(year)
    form = PhotoUploadForm(request.POST or None, request.FILES or None)
    if request.method == "POST" and form.is_valid():
        image = None
        if form.cleaned_data.get("image"):
            image = _save_wagtail_image(form.cleaned_data["image"], f"{page.display_title} фото")
        TournamentPhoto.objects.create(
            page=page,
            image=image,
            external_url=form.cleaned_data.get("external_url") or "",
            original_url=form.cleaned_data.get("original_url") or "",
            caption=form.cleaned_data.get("caption") or "",
            sort_order=page.photos.count(),
        )
        publish_page(page, user=request.user, tab=EditorChangeLog.TAB_FOTO)
        log_change(
            user=request.user,
            action=EditorChangeLog.ACTION_CREATE,
            summary="Добавлено фото",
            object_id=page.pk,
            object_label=page.display_title,
            tab=EditorChangeLog.TAB_FOTO,
        )
        messages.success(request, "Фото добавлено.")
        return redirect("editor:season_photos", year=year)
    return render(request, "editor/photo_form.html", {"page": page, "form": form})


@staff_required
@require_POST
def photo_delete(request, year, pk):
    page = get_season(year)
    photo = get_object_or_404(TournamentPhoto, pk=pk, page=page)
    photo.delete()
    publish_page(page, user=request.user, tab=EditorChangeLog.TAB_FOTO)
    log_change(
        user=request.user,
        action=EditorChangeLog.ACTION_DELETE,
        summary="Удалено фото",
        object_id=page.pk,
        object_label=page.display_title,
        tab=EditorChangeLog.TAB_FOTO,
    )
    messages.success(request, "Фото удалено.")
    return redirect("editor:season_photos", year=year)


# ----- Материалы -----


@staff_required
def season_materials(request, year):
    page = get_season(year)
    return render(
        request,
        "editor/season_materials.html",
        {
            "page": page,
            "links": page.links.all(),
            "form": LinkForm(),
        },
    )


@staff_required
@require_http_methods(["GET", "POST"])
def link_add(request, year):
    page = get_season(year)
    form = LinkForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        TournamentLink.objects.create(
            page=page,
            kind=form.cleaned_data["kind"],
            title=form.cleaned_data["title"],
            url=form.cleaned_data["url"],
            sort_order=page.links.count(),
        )
        publish_page(page, user=request.user, tab=EditorChangeLog.TAB_MATERIALY)
        log_change(
            user=request.user,
            action=EditorChangeLog.ACTION_CREATE,
            summary=f"Материал: {form.cleaned_data['title']}",
            object_id=page.pk,
            object_label=page.display_title,
            tab=EditorChangeLog.TAB_MATERIALY,
            payload=form.cleaned_data,
        )
        messages.success(request, "Ссылка добавлена.")
        return redirect("editor:season_materials", year=year)
    return render(request, "editor/link_form.html", {"page": page, "form": form})


@staff_required
@require_POST
def link_delete(request, year, pk):
    page = get_season(year)
    link = get_object_or_404(TournamentLink, pk=pk, page=page)
    title = link.title
    link.delete()
    publish_page(page, user=request.user, tab=EditorChangeLog.TAB_MATERIALY)
    log_change(
        user=request.user,
        action=EditorChangeLog.ACTION_DELETE,
        summary=f"Удалён материал: {title}",
        object_id=page.pk,
        object_label=page.display_title,
        tab=EditorChangeLog.TAB_MATERIALY,
    )
    messages.success(request, "Ссылка удалена.")
    return redirect("editor:season_materials", year=year)


# ----- Турниры в России -----


def _russia_page() -> RussiaTournamentsPage:
    page = RussiaTournamentsPage.objects.first()
    if not page:
        raise Http404("Страница «Турниры в России» не создана. Запустите seed_site.")
    return page


def _publish_russia(page: RussiaTournamentsPage, user, summary: str):
    revision = page.save_revision(user=user)
    revision.publish(user=user, skip_permission_checks=True)
    log_change(
        user=user,
        action=EditorChangeLog.ACTION_PUBLISH,
        summary=summary,
        object_type="russia",
        object_id=page.pk,
        object_label=page.title,
    )


def _problems_text(reg: RegionalTournament) -> str:
    lines = []
    for p in reg.problems.all().order_by("number", "sort_order"):
        lines.append(f"{p.number} | {p.title} | {p.statement}")
    return "\n".join(lines)


def _save_problems(reg: RegionalTournament, rows: list[dict]):
    reg.problems.all().delete()
    for i, row in enumerate(rows):
        RegionalProblem.objects.create(
            tournament=reg,
            sort_order=i,
            number=row["number"],
            title=row["title"],
            statement=row["statement"],
        )


def _photos_text(reg: RegionalTournament) -> str:
    return "\n".join(p.external_url for p in reg.photos.all() if p.external_url)


def _save_photos(reg: RegionalTournament, urls: list[str]):
    reg.photos.all().delete()
    for i, url in enumerate(urls):
        RegionalPhoto.objects.create(
            tournament=reg,
            sort_order=i,
            external_url=url,
        )


@staff_required
def russia_list(request):
    page = _russia_page()
    return render(
        request,
        "editor/russia_list.html",
        {
            "page": page,
            "regions": page.regions.all().order_by("region_code"),
        },
    )


@staff_required
@require_http_methods(["GET", "POST"])
def russia_edit(request, pk=None):
    page = _russia_page()
    reg = get_object_or_404(RegionalTournament, pk=pk, page=page) if pk else None
    used = set(page.regions.exclude(pk=reg.pk if reg else None).values_list("region_code", flat=True))
    choices = [(c, n) for c, n in REGION_CHOICES if c not in used or (reg and c == reg.region_code)]
    initial = None
    if reg:
        initial = {
            "region_code": reg.region_code,
            "has_tournament": reg.has_tournament,
            "title": reg.title,
            "city": reg.city,
            "date_start": reg.date_start,
            "date_end": reg.date_end,
            "date_note": reg.date_note,
            "contacts": reg.contacts,
            "info": reg.info,
            "results_text": reg.results_text,
            "results_url": reg.results_url,
            "results_label": reg.results_label,
            "problems_text": _problems_text(reg),
            "photos_text": _photos_text(reg),
        }
    form = RegionalTournamentForm(
        request.POST or None,
        region_choices=choices,
        initial=initial,
    )
    if request.method == "POST" and form.is_valid():
        data = form.cleaned_data
        problems = data.pop("problems_text")
        photos = data.pop("photos_text")
        if reg is None:
            reg = RegionalTournament(page=page, sort_order=page.regions.count())
        for key, value in data.items():
            setattr(reg, key, value if key != "has_tournament" else bool(value))
        if not data.get("results_label"):
            reg.results_label = "Оригинал результатов"
        reg.save()
        _save_problems(reg, problems)
        _save_photos(reg, photos)
        _publish_russia(page, request.user, f"Регион: {REGIONS.get(reg.region_code, reg.region_code)}")
        log_change(
            user=request.user,
            action=EditorChangeLog.ACTION_UPDATE if pk else EditorChangeLog.ACTION_CREATE,
            summary=f"{'Правка' if pk else 'Добавлен'} регион {reg.region_name}",
            object_type="russia_region",
            object_id=reg.pk,
            object_label=reg.region_name,
        )
        messages.success(request, "Регион сохранён.")
        return redirect("editor:russia_list")
    return render(
        request,
        "editor/russia_form.html",
        {
            "form": form,
            "reg": reg,
            "title": "Правка региона" if reg else "Новый региональный турнир",
        },
    )


@staff_required
@require_POST
def russia_delete(request, pk):
    page = _russia_page()
    reg = get_object_or_404(RegionalTournament, pk=pk, page=page)
    label = reg.region_name
    reg.delete()
    _publish_russia(page, request.user, f"Удалён регион: {label}")
    log_change(
        user=request.user,
        action=EditorChangeLog.ACTION_DELETE,
        summary=f"Удалён регион {label}",
        object_type="russia_region",
        object_id=pk,
        object_label=label,
    )
    messages.success(request, "Регион удалён с карты.")
    return redirect("editor:russia_list")
