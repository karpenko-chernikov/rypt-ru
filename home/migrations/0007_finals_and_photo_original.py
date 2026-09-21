from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("home", "0006_tournamentpage_photo_album_url"),
    ]

    operations = [
        migrations.AddField(
            model_name="tournamentresultrow",
            name="kind",
            field=models.CharField(
                choices=[("ranking", "Итог"), ("final", "Финал")],
                default="ranking",
                max_length=16,
                verbose_name="Таблица",
            ),
        ),
        migrations.AlterField(
            model_name="tournamentphoto",
            name="external_url",
            field=models.TextField(blank=True, verbose_name="Ссылка на фото"),
        ),
        migrations.AddField(
            model_name="tournamentphoto",
            name="original_url",
            field=models.URLField(blank=True, verbose_name="Оригинал"),
        ),
    ]
