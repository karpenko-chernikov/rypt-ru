import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


def migrate_editors_group(apps, schema_editor):
    Group = apps.get_model("auth", "Group")
    User = apps.get_model(settings.AUTH_USER_MODEL)
    group, _ = Group.objects.get_or_create(name="Editors")
    for user in User.objects.filter(is_staff=True, is_superuser=False):
        user.groups.add(group)
        user.is_staff = False
        user.save(update_fields=["is_staff"])


def noop_reverse(apps, schema_editor):
    pass


class Migration(migrations.Migration):
    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("editor", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="EditorInvite",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("code", models.CharField(db_index=True, max_length=64, unique=True, verbose_name="Код")),
                ("note", models.CharField(blank=True, max_length=200, verbose_name="Заметка")),
                ("created_at", models.DateTimeField(auto_now_add=True, verbose_name="Создано")),
                ("expires_at", models.DateTimeField(db_index=True, verbose_name="Истекает")),
                ("used_at", models.DateTimeField(blank=True, null=True, verbose_name="Использовано")),
                ("revoked", models.BooleanField(default=False, verbose_name="Отозвано")),
                (
                    "created_by",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="editor_invites_created",
                        to=settings.AUTH_USER_MODEL,
                        verbose_name="Кто создал",
                    ),
                ),
                (
                    "used_by",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="editor_invites_used",
                        to=settings.AUTH_USER_MODEL,
                        verbose_name="Кто зарегистрировался",
                    ),
                ),
            ],
            options={
                "verbose_name": "Приглашение редактора",
                "verbose_name_plural": "Приглашения редакторов",
                "ordering": ["-created_at"],
            },
        ),
        migrations.AlterField(
            model_name="editorchangelog",
            name="action",
            field=models.CharField(
                choices=[
                    ("create", "Создание"),
                    ("update", "Изменение"),
                    ("publish", "Публикация"),
                    ("enable_section", "Включение раздела"),
                    ("delete", "Удаление"),
                    ("make_current", "Сделать текущим"),
                    ("archive_current", "В прошедшие"),
                    ("invite", "Приглашение"),
                ],
                max_length=32,
                verbose_name="Действие",
            ),
        ),
        migrations.RunPython(migrate_editors_group, noop_reverse),
    ]
