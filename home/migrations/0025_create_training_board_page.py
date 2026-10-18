from django.db import migrations


def _live_parent():
    from home.models import HomePage

    return HomePage.objects.filter(depth=2).order_by("path").first()


def create_training_board_page(apps, schema_editor):
    """Создаёт страницу «Доска заявок» при migrate (без seed_site)."""
    from home.models import HomePage, TrainingBoardPage

    parent = _live_parent()
    if parent is None:
        return

    existing = TrainingBoardPage.objects.filter(
        slug="training-board",
        path__startswith=parent.path,
        depth=parent.depth + 1,
    ).first()
    if existing is not None:
        return

    child = TrainingBoardPage(title="Доска заявок", slug="training-board", intro="")
    parent.add_child(instance=child)
    child.save_revision().publish()


def reverse_training_board_page(apps, schema_editor):
    from home.models import TrainingBoardPage

    parent = _live_parent()
    if parent is None:
        return

    for page in TrainingBoardPage.objects.filter(
        slug="training-board",
        path__startswith=parent.path,
        depth=parent.depth + 1,
    ):
        page.delete()


class Migration(migrations.Migration):

    dependencies = [
        ("home", "0024_trainingboardcard_trainingboardpage"),
    ]

    operations = [
        migrations.RunPython(create_training_board_page, reverse_training_board_page),
    ]
