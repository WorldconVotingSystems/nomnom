# Migration to enable pg_trgm extension for similarity searches
from django.contrib.postgres.operations import TrigramExtension
from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("canonicalize", "0003_alter_canonicalizednomination_options_and_more"),
    ]

    operations = [
        TrigramExtension(),
    ]
