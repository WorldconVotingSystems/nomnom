# Generated by Django 5.0 on 2024-01-13 18:54

import django.utils.timezone
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("nominate", "0011_rank_voter_ip_address"),
    ]

    operations = [
        migrations.AddField(
            model_name="nominatingmemberprofile",
            name="created_at",
            field=models.DateTimeField(
                auto_now_add=True, default=django.utils.timezone.now
            ),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name="nominatingmemberprofile",
            name="updated_at",
            field=models.DateTimeField(auto_now=True),
        ),
    ]
