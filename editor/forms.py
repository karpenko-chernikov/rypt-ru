from django import forms
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError

from editor.authz import grant_editor
from editor.security import validate_editor_image, validate_public_http_url


class EditorLoginForm(AuthenticationForm):
    username = forms.CharField(label="Логин", widget=forms.TextInput(attrs={"autocomplete": "username"}))
    password = forms.CharField(
        label="Пароль",
        strip=False,
        widget=forms.PasswordInput(attrs={"autocomplete": "current-password"}),
    )


class EditorRegisterForm(UserCreationForm):
    class Meta:
        model = User
        fields = ("username",)

    def save(self, commit=True):
        user = super().save(commit=False)
        user.is_staff = False
        user.is_superuser = False
        if commit:
            user.save()
            grant_editor(user)
        return user


class InviteCreateForm(forms.Form):
    note = forms.CharField(
        label="Заметка (кому)",
        max_length=200,
        required=False,
        help_text="Например: «Иван, оргкомитет». Не попадает в ссылку.",
    )
    days_valid = forms.IntegerField(
        label="Срок действия (дней)",
        min_value=1,
        max_value=30,
        initial=7,
    )


class SeasonCreateForm(forms.Form):
    year = forms.IntegerField(label="Год", min_value=1979, max_value=2100)
    make_current = forms.BooleanField(
        label="Сразу сделать текущим",
        required=False,
        initial=False,
    )


class OpenNewSeasonForm(forms.Form):
    year = forms.IntegerField(label="Год нового сезона", min_value=1979, max_value=2100)
    confirm = forms.BooleanField(
        label="Понимаю: текущий сезон уйдёт в прошедшие, новый станет текущим",
        required=True,
    )


class SeasonMetaForm(forms.Form):
    city = forms.CharField(label="Город", max_length=120, required=False)
    date_start = forms.DateField(label="Начало", required=False, widget=forms.DateInput(attrs={"type": "date"}))
    date_end = forms.DateField(label="Конец", required=False, widget=forms.DateInput(attrs={"type": "date"}))


class ProblemForm(forms.Form):
    number = forms.IntegerField(label="Номер", min_value=1)
    title = forms.CharField(label="Название", max_length=200)
    statement = forms.CharField(label="Условие", widget=forms.Textarea(attrs={"rows": 4}))


class ResultsMoreForm(forms.Form):
    results_more_url = forms.CharField(label="Ссылка или путь подробнее", max_length=500, required=False)
    results_more_label = forms.CharField(label="Подпись ссылки", max_length=160, required=False)

    def clean_results_more_url(self):
        value = (self.cleaned_data.get("results_more_url") or "").strip()
        if not value:
            return ""
        # Относительные медиа-пути сайта (/media/...) разрешены.
        if value.startswith("/media/") or value.startswith("/documents/"):
            if "://" in value or "\\" in value or ".." in value:
                raise ValidationError("Некорректный внутренний путь.")
            return value
        return validate_public_http_url(value, field_name="Ссылка подробнее")


class ResultRowForm(forms.Form):
    kind = forms.ChoiceField(label="Таблица")
    place = forms.CharField(label="Место", max_length=16)
    team = forms.CharField(label="Команда", max_length=200)
    city = forms.CharField(label="Город", max_length=120, required=False)
    points = forms.CharField(label="Сумма", max_length=32, required=False)

    def __init__(self, *args, kind_choices=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["kind"].choices = kind_choices or []


class IyptForm(forms.Form):
    iypt_team = forms.CharField(label="Состав / текст", required=False, widget=forms.Textarea(attrs={"rows": 6}))
    iypt_more_url = forms.CharField(label="Ссылка подробнее", required=False, max_length=500)
    iypt_more_label = forms.CharField(label="Подпись ссылки", max_length=160, required=False)

    def clean_iypt_more_url(self):
        return validate_public_http_url(
            self.cleaned_data.get("iypt_more_url") or "",
            field_name="Ссылка подробнее",
        )


class PhotoAlbumForm(forms.Form):
    photo_album_url = forms.CharField(
        label="Альбомы (по одной ссылке на строку)",
        required=False,
        widget=forms.Textarea(attrs={"rows": 4}),
    )

    def clean_photo_album_url(self):
        raw = (self.cleaned_data.get("photo_album_url") or "").strip()
        if not raw:
            return ""
        lines = []
        for line in raw.splitlines():
            line = line.strip()
            if not line:
                continue
            lines.append(validate_public_http_url(line, field_name="Альбом"))
        return "\n".join(lines)


class LinkForm(forms.Form):
    kind = forms.ChoiceField(label="Тип", choices=[("report", "Отчёт"), ("news", "Новость")])
    title = forms.CharField(label="Название", max_length=200)
    url = forms.URLField(label="Ссылка")

    def clean_url(self):
        return validate_public_http_url(self.cleaned_data.get("url") or "", field_name="Ссылка")


class ScanUploadForm(forms.Form):
    caption = forms.CharField(label="Подпись", max_length=200, required=False)
    image = forms.ImageField(label="Страница или левая полоса")
    image_right = forms.ImageField(label="Правая полоса (разворот)", required=False)

    def clean_image(self):
        return validate_editor_image(self.cleaned_data.get("image"))

    def clean_image_right(self):
        return validate_editor_image(self.cleaned_data.get("image_right"))


class PhotoUploadForm(forms.Form):
    caption = forms.CharField(label="Подпись", max_length=200, required=False)
    image = forms.ImageField(label="Файл", required=False)
    external_url = forms.CharField(label="Или внешняя ссылка", required=False)
    original_url = forms.URLField(label="Оригинал", required=False)

    def clean_image(self):
        return validate_editor_image(self.cleaned_data.get("image"))

    def clean_external_url(self):
        return validate_public_http_url(
            self.cleaned_data.get("external_url") or "",
            field_name="Внешняя ссылка",
        )

    def clean_original_url(self):
        value = self.cleaned_data.get("original_url")
        if not value:
            return ""
        return validate_public_http_url(str(value), field_name="Оригинал")

    def clean(self):
        cleaned = super().clean()
        if not cleaned.get("image") and not cleaned.get("external_url"):
            raise forms.ValidationError("Нужен файл или внешняя ссылка.")
        return cleaned


class RegionalTournamentForm(forms.Form):
    region_code = forms.ChoiceField(label="Субъект РФ", choices=())
    has_tournament = forms.BooleanField(
        label="Есть турнир (золотая подсветка на карте)",
        required=False,
        initial=True,
    )
    title = forms.CharField(label="Название турнира", max_length=200)
    city = forms.CharField(label="Город / площадка", max_length=160, required=False)
    date_start = forms.DateField(
        label="Начало", required=False, widget=forms.DateInput(attrs={"type": "date"})
    )
    date_end = forms.DateField(
        label="Конец", required=False, widget=forms.DateInput(attrs={"type": "date"})
    )
    date_note = forms.CharField(
        label="Когда (свободная формулировка)",
        max_length=200,
        required=False,
        help_text="Например: «март 2026».",
    )
    contacts = forms.CharField(
        label="Контакты",
        required=False,
        widget=forms.Textarea(attrs={"rows": 4}),
    )
    info = forms.CharField(
        label="О турнире (HTML/текст)",
        required=False,
        widget=forms.Textarea(attrs={"rows": 5}),
    )
    results_text = forms.CharField(
        label="Краткие результаты",
        required=False,
        widget=forms.Textarea(attrs={"rows": 4}),
    )
    results_url = forms.CharField(label="Ссылка на оригинал результатов", required=False, max_length=500)
    results_label = forms.CharField(label="Подпись к ссылке", required=False, max_length=160)
    problems_text = forms.CharField(
        label="Задачи (по одной на строку: номер | название | условие)",
        required=False,
        widget=forms.Textarea(attrs={"rows": 8}),
        help_text="Пример: 1 | Маятник | Исследуйте колебания…",
    )
    photos_text = forms.CharField(
        label="Фото (по одной внешней ссылке на строку)",
        required=False,
        widget=forms.Textarea(attrs={"rows": 3}),
    )

    def __init__(self, *args, region_choices=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["region_code"].choices = region_choices or []

    def clean_results_url(self):
        value = (self.cleaned_data.get("results_url") or "").strip()
        if not value:
            return ""
        return validate_public_http_url(value, field_name="Ссылка на результаты")

    def clean_photos_text(self):
        raw = self.cleaned_data.get("photos_text") or ""
        urls = []
        for line in raw.splitlines():
            line = line.strip()
            if not line:
                continue
            urls.append(validate_public_http_url(line, field_name="Фото"))
        return urls

    def clean_problems_text(self):
        raw = self.cleaned_data.get("problems_text") or ""
        rows = []
        for line in raw.splitlines():
            line = line.strip()
            if not line:
                continue
            parts = [p.strip() for p in line.split("|", 2)]
            if len(parts) < 2:
                raise ValidationError("Строка задачи: «номер | название | условие».")
            try:
                number = int(parts[0])
            except ValueError as exc:
                raise ValidationError("Номер задачи должен быть числом.") from exc
            title = parts[1]
            statement = parts[2] if len(parts) > 2 else ""
            if not title:
                raise ValidationError("У задачи нужно название.")
            rows.append({"number": number, "title": title, "statement": statement})
        return rows
