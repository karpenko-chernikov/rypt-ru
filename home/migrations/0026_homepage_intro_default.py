# Generated manually: default text for the editable homepage intro block.

from django.db import migrations

INTRO = (
    "<p>Турнир юных физиков (ТЮФ) — это ежегодное коллективное состязание "
    "школьников старших классов в умении решать сложные научные проблемы, "
    "убедительно представлять свои решения, отстаивать их в научных дискуссиях — "
    "физбоях. Турнир проходит ежегодно начиная с марта 1979 года, сохраняя свою "
    "суть — обсуждение общих семнадцати заданий в течение всего года.</p>"
)


def set_default_intro(apps, schema_editor):
    HomePage = apps.get_model("home", "HomePage")
    HomePage.objects.filter(intro="").update(intro=INTRO)


def unset_default_intro(apps, schema_editor):
    HomePage = apps.get_model("home", "HomePage")
    HomePage.objects.filter(intro=INTRO).update(intro="")


class Migration(migrations.Migration):

    dependencies = [
        ("home", "0025_create_training_board_page"),
    ]

    operations = [
        migrations.RunPython(set_default_intro, unset_default_intro),
    ]
