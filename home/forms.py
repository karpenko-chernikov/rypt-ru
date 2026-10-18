"""Формы публичной «Доски заявок на тренировочные бои»."""

import random
import time

from django import forms
from django.core.signing import BadSignature, SignatureExpired, TimestampSigner

# Ключи сессии для математической captcha.
CAPTCHA_ANSWER_KEY = "training_board_captcha_answer"
CAPTCHA_QUESTION_KEY = "training_board_captcha_question"

# Задержка перед проверкой пароля при удалении (защита от брутфорса).
DELETE_DELAY_SECONDS = 5
# Токен формы удаления живёт час — дальше просим обновить страницу.
DELETE_TOKEN_MAX_AGE = 3600


def generate_captcha():
    """Возвращает (ответ, текст вопроса) для математической captcha."""
    a = random.randint(2, 9)
    b = random.randint(2, 9)
    return a + b, f"Сколько будет {a} + {b}?"


def delete_token_for(card_id):
    """Подписанный токен формы удаления; несёт время выдачи (для задержки 5 с)."""
    value = f"{card_id}:{int(time.time())}"
    return TimestampSigner().sign(value)


class TrainingBoardCreateForm(forms.Form):
    team_name = forms.CharField(
        label="Название команды",
        max_length=200,
        widget=forms.TextInput(attrs={"autocomplete": "organization"}),
    )
    dates = forms.CharField(
        label="Примерные даты",
        max_length=200,
        help_text="Когда хотели бы провести тренировочный бой",
    )
    city = forms.CharField(
        label="Город (или онлайн)",
        max_length=200,
        help_text="Место проведения боя",
    )
    tasks = forms.CharField(
        label="Пожелания по заданиям",
        required=False,
        widget=forms.Textarea(attrs={"rows": 3}),
        help_text="Какие задания вы бы хотели доложить или прооппонировать",
    )
    comments = forms.CharField(
        label="Комментарии",
        required=False,
        widget=forms.Textarea(attrs={"rows": 3}),
    )
    contact = forms.CharField(
        label="Имя и контакты руководителя команды",
        widget=forms.Textarea(attrs={"rows": 3}),
        help_text="Чтобы с вами могли связаться заинтересованные команды",
    )
    password = forms.CharField(
        label="Пароль",
        widget=forms.PasswordInput(attrs={"autocomplete": "new-password"}),
        help_text=(
            "Чтобы только вы могли удалить своё объявление! "
            "Не забывайте его и не ставьте слишком простой."
        ),
    )
    captcha_answer = forms.CharField(
        label="",
        max_length=10,
        widget=forms.TextInput(
            attrs={"autocomplete": "off", "inputmode": "numeric"}
        ),
    )
    # Honeypot: люди его не видят и не заполняют; боты — заполняют.
    website = forms.CharField(required=False, widget=forms.HiddenInput)

    def __init__(self, *args, captcha_question="", captcha_expected=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.captcha_expected = captcha_expected
        self.fields["captcha_answer"].label = captcha_question or "Сколько будет 2 + 2?"

    def clean_website(self):
        if self.cleaned_data.get("website"):
            raise forms.ValidationError("Похоже, вы робот.")
        return ""

    def clean_captcha_answer(self):
        value = (self.cleaned_data.get("captcha_answer") or "").strip()
        expected = str(self.captcha_expected) if self.captcha_expected is not None else ""
        if not value or not expected or value != expected:
            raise forms.ValidationError("Неверный ответ на проверочный вопрос.")
        return value


class TrainingBoardDeleteForm(forms.Form):
    card_id = forms.IntegerField(widget=forms.HiddenInput)
    token = forms.CharField(widget=forms.HiddenInput)
    password = forms.CharField(
        label="Пароль",
        widget=forms.PasswordInput(attrs={"autocomplete": "current-password"}),
    )

    def clean(self):
        cleaned = super().clean()
        card_id = cleaned.get("card_id")
        token = (cleaned.get("token") or "").strip()
        if not token:
            raise forms.ValidationError(
                "Форма удаления устарела. Обновите страницу и попробуйте снова."
            )
        signer = TimestampSigner()
        try:
            signed_value = signer.unsign(token, max_age=DELETE_TOKEN_MAX_AGE)
        except SignatureExpired:
            raise forms.ValidationError(
                "Форма удаления устарела. Обновите страницу и попробуйте снова."
            )
        except BadSignature:
            raise forms.ValidationError("Некорректная форма удаления. Обновите страницу.")
        try:
            raw_card_id, raw_timestamp = signed_value.rsplit(":", 1)
        except ValueError:
            raise forms.ValidationError("Некорректная форма удаления. Обновите страницу.")
        if raw_card_id != str(card_id):
            raise forms.ValidationError("Некорректная форма удаления. Обновите страницу.")
        elapsed = time.time() - int(raw_timestamp)
        if elapsed < DELETE_DELAY_SECONDS:
            wait = int(DELETE_DELAY_SECONDS - elapsed) + 1
            raise forms.ValidationError(
                f"Слишком быстро. Подождите ещё {wait} с и попробуйте снова."
            )
        self.card_id = card_id
        return cleaned
