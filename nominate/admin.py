from django.contrib import admin

from . import models


# Yeah, I'm sorry about this name too.
class NominationAdminDataAdmin(admin.StackedInline):
    model = models.NominationAdminData


class ExtendedNominationAdmin(admin.ModelAdmin):
    model = models.Nomination
    inlines = [NominationAdminDataAdmin]


admin.site.register(models.Election)
admin.site.register(models.Finalist)
admin.site.register(models.NominatingMemberProfile)
admin.site.register(models.VotingMember)
admin.site.register(models.Category)
admin.site.register(models.Nomination, ExtendedNominationAdmin)
admin.site.register(models.ReportRecipient)
