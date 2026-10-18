# Generated manually for multiple tournaments per region.

from django.db import migrations, models


def fill_slugs(apps, schema_editor):
    RegionalTournament = apps.get_model("home", "RegionalTournament")
    used = set()
    for reg in RegionalTournament.objects.all().order_by("id"):
        base = (reg.region_code or "tour").lower().replace("_", "-")
        slug = base
        n = 2
        while slug in used:
            slug = f"{base}-{n}"
            n += 1
        reg.slug = slug
        reg.save(update_fields=["slug"])
        used.add(slug)


class Migration(migrations.Migration):

    dependencies = [
        ("home", "0016_regional_tournament_season_problems"),
    ]

    operations = [
        migrations.AddField(
            model_name="regionaltournament",
            name="slug",
            field=models.SlugField(
                default="",
                help_text="Уникальный ключ для матрицы и карточки, напр. sib, mos-mipt, beaver.",
                max_length=64,
                verbose_name="Код турнира",
            ),
        ),
        migrations.RunPython(fill_slugs, migrations.RunPython.noop),
        migrations.AlterUniqueTogether(
            name="regionaltournament",
            unique_together={("page", "slug")},
        ),
        migrations.AlterField(
            model_name="regionaltournament",
            name="region_code",
            field=models.CharField(
                choices=[
                    ("ONLINE", "Онлайн"),
                    ("RU-ALT", "Алтайский край"),
                    ("RU-AMU", "Амурская область"),
                    ("RU-ARK", "Архангельская область"),
                    ("RU-AST", "Астраханская область"),
                    ("RU-BEL", "Белгородская область"),
                    ("RU-BRY", "Брянская область"),
                    ("RU-VLA", "Владимирская область"),
                    ("RU-VGG", "Волгоградская область"),
                    ("RU-VLG", "Вологодская область"),
                    ("RU-VOR", "Воронежская область"),
                    ("RU-YEV", "Еврейская автономная область"),
                    ("RU-ZAB", "Забайкальский край"),
                    ("RU-IVA", "Ивановская область"),
                    ("RU-IRK", "Иркутская область"),
                    ("RU-KB", "Кабардино-Балкарская Республика"),
                    ("RU-KGD", "Калининградская область"),
                    ("RU-KLU", "Калужская область"),
                    ("RU-KAM", "Камчатский край"),
                    ("RU-KC", "Карачаево-Черкесская Республика"),
                    ("RU-KEM", "Кемеровская область"),
                    ("RU-KIR", "Кировская область"),
                    ("RU-KOS", "Костромская область"),
                    ("RU-KDA", "Краснодарский край"),
                    ("RU-KYA", "Красноярский край"),
                    ("RU-KGN", "Курганская область"),
                    ("RU-KRS", "Курская область"),
                    ("RU-LEN", "Ленинградская область"),
                    ("RU-LIP", "Липецкая область"),
                    ("RU-MAG", "Магаданская область"),
                    ("RU-MOW", "Москва"),
                    ("RU-MOS", "Московская область"),
                    ("RU-MUR", "Мурманская область"),
                    ("RU-NEN", "Ненецкий автономный округ"),
                    ("RU-NIZ", "Нижегородская область"),
                    ("RU-NGR", "Новгородская область"),
                    ("RU-NVS", "Новосибирская область"),
                    ("RU-OMS", "Омская область"),
                    ("RU-ORE", "Оренбургская область"),
                    ("RU-ORL", "Орловская область"),
                    ("RU-PNZ", "Пензенская область"),
                    ("RU-PER", "Пермский край"),
                    ("RU-PRI", "Приморский край"),
                    ("RU-PSK", "Псковская область"),
                    ("RU-AD", "Республика Адыгея (Адыгея)"),
                    ("RU-AL", "Республика Алтай"),
                    ("RU-BA", "Республика Башкортостан"),
                    ("RU-BU", "Республика Бурятия"),
                    ("RU-DA", "Республика Дагестан"),
                    ("RU-IN", "Республика Ингушетия"),
                    ("RU-KL", "Республика Калмыкия"),
                    ("RU-KR", "Республика Карелия"),
                    ("RU-KO", "Республика Коми"),
                    ("RU-CR", "Республика Крым"),
                    ("RU-ME", "Республика Марий Эл"),
                    ("RU-MO", "Республика Мордовия"),
                    ("RU-SA", "Республика Саха (Якутия)"),
                    ("RU-SE", "Республика Северная Осетия — Алания"),
                    ("RU-TA", "Республика Татарстан (Татарстан)"),
                    ("RU-TY", "Республика Тыва"),
                    ("RU-KK", "Республика Хакасия"),
                    ("RU-ROS", "Ростовская область"),
                    ("RU-RYA", "Рязанская область"),
                    ("RU-SAM", "Самарская область"),
                    ("RU-SPE", "Санкт-Петербург"),
                    ("RU-SAR", "Саратовская область"),
                    ("RU-SAK", "Сахалинская область"),
                    ("RU-SVE", "Свердловская область"),
                    ("RU-SMO", "Смоленская область"),
                    ("RU-STA", "Ставропольский край"),
                    ("RU-TAM", "Тамбовская область"),
                    ("RU-TVE", "Тверская область"),
                    ("RU-TOM", "Томская область"),
                    ("RU-TUL", "Тульская область"),
                    ("RU-TYU", "Тюменская область"),
                    ("RU-UD", "Удмуртская Республика"),
                    ("RU-ULY", "Ульяновская область"),
                    ("RU-KHA", "Хабаровский край"),
                    ("RU-KHM", "Ханты-Мансийский автономный округ — Югра"),
                    ("RU-CHE", "Челябинская область"),
                    ("RU-CE", "Чеченская Республика"),
                    ("RU-CU", "Чувашская Республика — Чувашия"),
                    ("RU-CHU", "Чукотский автономный округ"),
                    ("RU-YAN", "Ямало-Ненецкий автономный округ"),
                    ("RU-YAR", "Ярославская область"),
                    ("RU-SEV", "Севастополь"),
                ],
                db_index=True,
                max_length=16,
                verbose_name="Субъект РФ / онлайн",
            ),
        ),
    ]
