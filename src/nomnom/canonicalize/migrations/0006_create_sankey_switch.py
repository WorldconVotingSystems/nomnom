"""Data migration to create a feature flag toggle for the Sankey diagram on the nomination results page."""

from django.db import migrations

from nomnom.canonicalize.feature_switches import SWITCH_SANKEY_DIAGRAM

SWITCHES = [
    {
        "name": SWITCH_SANKEY_DIAGRAM,
        "active": False,
        "note": "Toggle Sankey diagram visibility on nomination results page",
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
        ("canonicalize", "0005_create_csv_switch"),
    ]

    operations = [
        migrations.RunPython(create_switches, delete_switches),
    ]
