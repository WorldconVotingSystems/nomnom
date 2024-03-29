# Generated by Django 5.0 on 2024-01-12 05:17

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("nominate", "0006_votinginformation"),
    ]

    operations = [
        migrations.AlterModelOptions(
            name="category",
            options={
                "ordering": ["ballot_position"],
                "verbose_name_plural": "categories",
            },
        ),
        migrations.AlterField(
            model_name="category",
            name="details",
            field=models.TextField(blank=True),
        ),
        migrations.AlterField(
            model_name="category",
            name="field_2_description",
            field=models.CharField(blank=True, max_length=100, null=True),
        ),
        migrations.AlterField(
            model_name="category",
            name="field_3_description",
            field=models.CharField(blank=True, max_length=100, null=True),
        ),
    ]
