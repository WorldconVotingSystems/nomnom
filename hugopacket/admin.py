from django.contrib import admin

from . import models

admin.site.register(models.ElectionPacket)
admin.site.register(models.PacketFile)
