from django.conf import settings
from django.db import models
from django.utils import timezone


class EditorChangeLog(models.Model):
    ACTION_CREATE = "create"
    ACTION_UPDATE = "update"
    ACTION_PUBLISH = "publish"
    ACTION_ENABLE_SECTION = "enable_section"
    ACTION_DELETE = "delete"
    ACTION_MAKE_CURRENT = "make_current"
    ACTION_ARCHIVE_CURRENT = "archive_current"
    ACTION_INVITE = "invite"
    ACTION_CHOICES = [
        (ACTION_CREATE, "Создание"),
        (ACTION_UPDATE, "Изменение"),
        (ACTION_PUBLISH, "Публикация"),
        (ACTION_ENABLE_SECTION, "Включение раздела"),
        (ACTION_DELETE, "Удаление"),
        (ACTION_MAKE_CURRENT, "Сделать текущим"),
        (ACTION_ARCHIVE_CURRENT, "В прошедшие"),
        (ACTION_INVITE, "Приглашение"),
    ]

    TAB_META = "meta"
    TAB_ZADACHI = "zadachi"
    TAB_REZULTATY = "rezultaty"
    TAB_IYPT = "iypt"
    TAB_FOTO = "foto"
    TAB_MATERIALY = "materialy"
    TAB_OTHER = "other"
    TAB_CHOICES = [
        (TAB_META, "Мета"),
        (TAB_ZADACHI, "Задачи"),
        (TAB_REZULTATY, "Результаты"),
        (TAB_IYPT, "IYPT"),
        (TAB_FOTO, "Фото"),
        (TAB_MATERIALY, "Материалы"),
        (TAB_OTHER, "Прочее"),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="editor_changes",
        verbose_name="Кто",
    )
    created_at = models.DateTimeField("Когда", auto_now_add=True, db_index=True)
    object_type = models.CharField("Тип объекта", max_length=32, default="season")
    object_id = models.PositiveIntegerField("ID объекта", null=True, blank=True, db_index=True)
    object_label = models.CharField("Объект", max_length=200, blank=True)
    tab = models.CharField("Раздел", max_length=32, choices=TAB_CHOICES, default=TAB_OTHER)
    action = models.CharField("Действие", max_length=32, choices=ACTION_CHOICES)
    summary = models.CharField("Кратко", max_length=400)
    payload = models.JSONField("Снимок", default=dict, blank=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Запись журнала"
        verbose_name_plural = "Журнал правок"

    def __str__(self):
        who = self.user.get_username() if self.user else "—"
        return f"{self.created_at:%d.%m.%Y %H:%M} · {who} · {self.summary}"


class EditorInvite(models.Model):
    code = models.CharField("Код", max_length=64, unique=True, db_index=True)
    note = models.CharField("Заметка", max_length=200, blank=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="editor_invites_created",
        verbose_name="Кто создал",
    )
    created_at = models.DateTimeField("Создано", auto_now_add=True)
    expires_at = models.DateTimeField("Истекает", db_index=True)
    used_at = models.DateTimeField("Использовано", null=True, blank=True)
    used_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="editor_invites_used",
        verbose_name="Кто зарегистрировался",
    )
    revoked = models.BooleanField("Отозвано", default=False)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Приглашение редактора"
        verbose_name_plural = "Приглашения редакторов"

    def __str__(self):
        return self.code

    @property
    def is_usable(self) -> bool:
        if self.revoked or self.used_at is not None:
            return False
        return self.expires_at > timezone.now()
