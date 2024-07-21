from django.contrib.admin.apps import AdminConfig


class NomnomAdminConfig(AdminConfig):
    default_site = "nomnom.admin.NomnomAdminSite"
