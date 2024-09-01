# Generated by Django 5.2.dev20240708061027 on 2024-07-22 20:08

import django_fsm
from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("advise", "0002_alter_proposal_options"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="proposal",
            name="vote_closes_at",
        ),
        migrations.RemoveField(
            model_name="proposal",
            name="vote_opens_at",
        ),
        migrations.AddField(
            model_name="proposal",
            name="state",
            field=django_fsm.FSMField(
                choices=[
                    ("preview", "Preview"),
                    ("open", "Open"),
                    ("closed", "Closed"),
                ],
                default="preview",
                max_length=50,
            ),
        ),
    ]