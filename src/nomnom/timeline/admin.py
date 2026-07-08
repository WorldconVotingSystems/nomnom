from django.contrib import admin

from . import models


@admin.register(models.TimelineEvent)
class TimelineEventAdmin(admin.ModelAdmin):
    list_display = ["label", "date", "provisional", "position", "complete"]
    list_editable = ["position", "complete"]
    ordering = ["position"]
