from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("home", "0026_homepage_intro_default"),
    ]

    operations = [
        migrations.AddField(
            model_name="tournamentproblemscan",
            name="kind",
            field=models.CharField(
                choices=[("season", "Задания сезона"), ("final", "Задания финала")],
                default="season",
                max_length=16,
                verbose_name="Раздел",
            ),
        ),
    ]
