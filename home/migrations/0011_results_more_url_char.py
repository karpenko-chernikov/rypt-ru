# Generated manually for CharField results_more_url (local file downloads).

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("home", "0010_iypt_fields_and_kinds"),
    ]

    operations = [
        migrations.AlterField(
            model_name="tournamentpage",
            name="results_more_url",
            field=models.CharField(
                blank=True,
                help_text="Внешняя ссылка (https://…) или путь к файлу (/media/…).",
                max_length=500,
                verbose_name="Подробные результаты, ссылка или файл",
            ),
        ),
    ]
