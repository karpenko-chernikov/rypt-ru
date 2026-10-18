# Generated manually: arbitrary text with images for the homepage tournament info block.

import wagtail.fields
from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("home", "0020_merge_20261018_2230"),
    ]

    operations = [
        migrations.AddField(
            model_name="homepage",
            name="info_text",
            field=wagtail.fields.RichTextField(
                blank=True,
                verbose_name="Информация",
            ),
        ),
    ]
