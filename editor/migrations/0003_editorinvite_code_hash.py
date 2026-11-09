from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("editor", "0002_editorinvite_and_editors_group"),
    ]

    operations = [
        migrations.RenameField(
            model_name="editorinvite",
            old_name="code",
            new_name="code_hash",
        ),
        migrations.AlterField(
            model_name="editorinvite",
            name="code_hash",
            field=models.CharField(
                db_index=True, max_length=64, unique=True, verbose_name="Хэш кода"
            ),
        ),
    ]
