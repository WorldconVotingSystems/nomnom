from django.contrib import admin

from . import models


admin.site.register(models.Election)
admin.site.register(models.Finalist)
admin.site.register(models.NominatingMemberProfile)
admin.site.register(models.VotingMember)
admin.site.register(models.Category)
admin.site.register(models.Nomination)
