from django.db import migrations


def _live_parent():
    from home.models import HomePage

    return HomePage.objects.filter(depth=2).order_by("path").first()


def convert_contacts_page(apps, schema_editor):
    """Превращает существующую страницу «Контакты» (ContentPage) в ContactsPage."""
    from home.models import ContactsPage, ContentPage

    parent = _live_parent()
    if parent is None:
        return

    existing = ContactsPage.objects.filter(
        slug="contacts",
        path__startswith=parent.path,
        depth=parent.depth + 1,
    ).first()
    if existing is not None:
        # Конвертация уже выполнена — осталось подчистить возможный дубль.
        ContentPage.objects.filter(
            slug="contacts",
            path__startswith=parent.path,
            depth=parent.depth + 1,
        ).delete()
        return

    title = "Контакты"
    for old in ContentPage.objects.filter(
        slug="contacts",
        path__startswith=parent.path,
        depth=parent.depth + 1,
    ):
        if old.title:
            title = old.title
        old.delete()

    child = ContactsPage(title=title, slug="contacts", sections=[])
    parent.add_child(instance=child)
    child.save_revision().publish()


def reverse_contacts_page(apps, schema_editor):
    from home.models import ContactsPage, ContentPage

    parent = _live_parent()
    if parent is None:
        return

    for page in ContactsPage.objects.filter(
        slug="contacts",
        path__startswith=parent.path,
        depth=parent.depth + 1,
    ):
        page.delete()

    if not ContentPage.objects.filter(
        slug="contacts",
        path__startswith=parent.path,
        depth=parent.depth + 1,
    ).exists():
        child = ContentPage(title="Контакты", slug="contacts", body="")
        parent.add_child(instance=child)
        child.save_revision().publish()


class Migration(migrations.Migration):

    dependencies = [
        ("home", "0022_contactspage"),
    ]

    operations = [
        migrations.RunPython(convert_contacts_page, reverse_contacts_page),
    ]
