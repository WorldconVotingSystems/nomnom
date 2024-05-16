from django.contrib import admin
from django import forms

from . import models


class PacketFileForm(forms.ModelForm):
    class Meta:
        model = models.PacketFile
        fields = "__all__"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["group"].required = False


admin.site.register(models.ElectionPacket)
admin.site.register(models.PacketFileGroup)


@admin.register(models.PacketFile)
class PacketFileAdmin(admin.ModelAdmin):
    model = models.PacketFile
    form = PacketFileForm
