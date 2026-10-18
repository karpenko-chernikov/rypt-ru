# Generated manually: editable homepage block «Информация о ближайшем турнире».

import django.db.models.deletion
import modelcluster.fields
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("home", "0017_regionaltournament_slug"),
        ("wagtaildocs", "__latest__"),
        ("wagtailimages", "__latest__"),
    ]

    operations = [
        migrations.AddField(
            model_name="homepage",
            name="info_title",
            field=models.CharField(
                blank=True,
                default="Информация о ближайшем Открытом Всероссийском Турнире юных физиков",
                max_length=240,
                verbose_name="Заголовок блока",
            ),
        ),
        migrations.AddField(
            model_name="homepage",
            name="info_dates",
            field=models.CharField(
                blank=True,
                help_text="Например: 15–21 марта 2027, Москва.",
                max_length=240,
                verbose_name="Даты",
            ),
        ),
        migrations.AddField(
            model_name="homepage",
            name="info_photo",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="+",
                to="wagtailimages.image",
                verbose_name="Фотография",
            ),
        ),
        migrations.AddField(
            model_name="homepage",
            name="info_photo_caption",
            field=models.CharField(
                blank=True,
                help_text="Например: университет, где пройдёт турнир.",
                max_length=240,
                verbose_name="Подпись к фотографии",
            ),
        ),
        migrations.CreateModel(
            name="HomeInfoFile",
            fields=[
                (
                    "id",
                    models.AutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "sort_order",
                    models.IntegerField(blank=True, editable=False, null=True),
                ),
                (
                    "title",
                    models.CharField(blank=True, max_length=200, verbose_name="Название"),
                ),
                (
                    "url",
                    models.CharField(
                        blank=True,
                        help_text="Внешняя ссылка (https://…) или путь к файлу (/media/…).",
                        max_length=500,
                        verbose_name="Или ссылка",
                    ),
                ),
                (
                    "document",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="+",
                        to="wagtaildocs.document",
                        verbose_name="Файл (документ)",
                    ),
                ),
                (
                    "page",
                    modelcluster.fields.ParentalKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="info_files",
                        to="home.homepage",
                    ),
                ),
            ],
            options={
                "ordering": ["sort_order"],
                "abstract": False,
            },
        ),
        migrations.CreateModel(
            name="HomeInfoButton",
            fields=[
                (
                    "id",
                    models.AutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "sort_order",
                    models.IntegerField(blank=True, editable=False, null=True),
                ),
                (
                    "label",
                    models.CharField(max_length=120, verbose_name="Текст кнопки"),
                ),
                (
                    "url",
                    models.CharField(max_length=500, verbose_name="Ссылка"),
                ),
                (
                    "page",
                    modelcluster.fields.ParentalKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="info_buttons",
                        to="home.homepage",
                    ),
                ),
            ],
            options={
                "ordering": ["sort_order"],
                "abstract": False,
            },
        ),
    ]
