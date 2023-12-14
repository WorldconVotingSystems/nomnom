from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from . import models

# Register your models here.
admin.site.register(models.NomNomUser, UserAdmin)
