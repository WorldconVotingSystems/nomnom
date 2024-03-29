# Generated by Django 5.0.1 on 2024-01-27 17:19

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("nominate", "0012_nominatingmemberprofile_created_at_and_more"),
    ]

    operations = [
        migrations.AlterField(
            model_name="category",
            name="field_1_description",
            field=models.CharField(max_length=200),
        ),
        migrations.AlterField(
            model_name="category",
            name="field_2_description",
            field=models.CharField(blank=True, max_length=200, null=True),
        ),
        migrations.AlterField(
            model_name="category",
            name="field_3_description",
            field=models.CharField(blank=True, max_length=200, null=True),
        ),
        migrations.AlterField(
            model_name="category",
            name="name",
            field=models.CharField(max_length=200),
        ),
    ]
