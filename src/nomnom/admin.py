from django.contrib import admin
from django.urls import path, reverse

from nomnom.base.admin_views import AdminPasskeyEnrollView, AdminPasskeyManagementView


class NomnomAdminSite(admin.AdminSite):
    site_header = "NomNom Admin"
    site_title = "NomNom Administration Interface"
    index_title = "WSFS Administration"
    login_template = "admin/nomnom_login.html"
    index_template = "admin/nomnom_index.html"

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path(
                "passkeys/",
                self.admin_view(AdminPasskeyManagementView.as_view()),
                name="passkey_management",
            ),
            path(
                "passkeys/enroll/",
                self.admin_view(AdminPasskeyEnrollView.as_view()),
                name="passkey_enroll",
            ),
        ]
        return custom_urls + urls

    def index(self, request, extra_context=None):
        """
        Display the main admin index page, which lists all of the installed
        apps that have been registered in this site.
        """
        extra_context = extra_context or {}

        # Add passkey management link to the extra context
        extra_context["passkey_management_url"] = reverse("admin:passkey_management")

        return super().index(request, extra_context)
