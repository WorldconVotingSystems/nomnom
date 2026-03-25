"""Data migration to create waffle switches for feature toggles.

Creates the advisory_votes and hugo_packet switches with active=True
so existing deployments retain current behavior after migration.
"""

from django.db import migrations

from nomnom.base.feature_switches import SWITCH_ADVISORY_VOTES, SWITCH_HUGO_PACKET

SWITCHES = [
    {
        "name": SWITCH_ADVISORY_VOTES,
        "active": True,
        "note": "Toggle advisory votes feature visibility",
    },
    {
        "name": SWITCH_HUGO_PACKET,
        "active": True,
        "note": "Toggle Hugo Award packet download feature visibility",
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
    ]

    operations = [
        migrations.RunPython(create_switches, delete_switches),
    ]
