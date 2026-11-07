from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("home", "0027_tournamentproblemscan_kind"),
    ]

    operations = [
        migrations.AlterField(
            model_name="tournamentpage",
            name="iypt_more_url",
            field=models.CharField(
                blank=True,
                help_text="Внешняя ссылка (https://…) или путь к файлу (/static/…). Несколько — с новой строки.",
                max_length=500,
                verbose_name="Подробные результаты IYPT, ссылка или файл",
            ),
        ),
    ]
