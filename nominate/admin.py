from django.contrib import admin

from . import models

admin.site.register(models.Election)
admin.site.register(models.Finalist)
admin.site.register(models.NominatingMember)
admin.site.register(models.VotingMember)
admin.site.register(models.Category)
