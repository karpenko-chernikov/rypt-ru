from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("home", "0007_finals_and_photo_original"),
    ]

    operations = [
        migrations.AlterField(
            model_name="tournamentpage",
            name="photo_album_url",
            field=models.TextField(
                blank=True,
                help_text="Файлы на сервер не копируются. Можно несколько альбомов ВК.",
                verbose_name="Альбомы фото (ссылки, по одной на строку)",
            ),
        ),
    ]
