from django.contrib import admin


class NomnomAdminSite(admin.AdminSite):
    site_header = "NomNom Admin"
    site_title = "NomNom Administration Interface"
    index_title = "WSFS Administration"
