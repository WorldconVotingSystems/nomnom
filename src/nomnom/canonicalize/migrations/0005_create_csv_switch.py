"""Data migration to create a feature flag toggle for the Sankey diagram on the nomination results page."""

from django.db import migrations

from nomnom.canonicalize.feature_switches import SWITCH_FINALIST_CSV_TABLE

SWITCHES = [
    {
        "name": SWITCH_FINALIST_CSV_TABLE,
        "active": False,
        "note": "Toggle EPH table access on nomination results page",
    },
]


def create_switches(apps, schema_editor):
    Switch = apps.get_model("waffle", "Switch")
    for switch in SWITCHES:
        Switch.objects.get_or_create(
            name=switch["name"],
            defaults={"active": switch["active"], "note": switch["note"]},
        )


def delete_switches(apps, schema_editor):
    Switch = apps.get_model("waffle", "Switch")
    Switch.objects.filter(name__in=[s["name"] for s in SWITCHES]).delete()


class Migration(migrations.Migration):
    dependencies = [
        ("waffle", "0004_update_everyone_nullbooleanfield"),
        ("base", "0001_create_waffle_switches"),
        # to enforce ordering
        ("canonicalize", "0004_enable_pg_trgm"),
    ]

    operations = [
        migrations.RunPython(create_switches, delete_switches),
    ]
