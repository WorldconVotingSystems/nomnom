from typing import Any

from django.contrib import admin
from django.http import HttpRequest


class NomnomAdminSite(admin.AdminSite):
    site_header = "NomNom Admin"
    site_title = "NomNom Administration Interface"
    index_title = "WSFS Administration"

    def get_app_list(
        self, request: HttpRequest, app_label: str | None = None
    ) -> list[Any]:
        apps = super().get_app_list(request, app_label)

        # relabel some of the apps
        retitle = {
            "admin": "System Admin",
            "waffle": "System Configuration",
            "auth": "User Management",
            "django_celery_results": "Background Task Results",
            "django_celery_beat": "Background Task Scheduling",
            "social_django": "Convention Authentication",
        }

        for app in apps:
            if app["app_label"] in retitle:
                app["name"] = retitle[app["app_label"]]

        # bubble the main admin apps up to the top, in order "nominate", "canonicalize", "hugopacket", "advise"
        app_order = ["nominate", "canonicalize", "hugopacket", "advise"]
        apps.sort(
            key=lambda app: (
                app_order.index(app["app_label"])
                if app["app_label"] in app_order
                else len(app_order)
            )
        )

        return apps
