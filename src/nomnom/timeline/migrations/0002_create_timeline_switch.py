"""Data migration to create a feature flag toggle for the homepage timeline."""

from django.db import migrations

from nomnom.timeline.feature_switches import SWITCH_TIMELINE

SWITCHES = [
    {
        "name": SWITCH_TIMELINE,
        "active": False,
        "note": "Toggle homepage timeline visibility",
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
        ("timeline", "0001_initial"),
    ]

    operations = [
        migrations.RunPython(create_switches, delete_switches),
    ]
