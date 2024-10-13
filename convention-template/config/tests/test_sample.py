def test_svcs_configured():
    from django.conf import settings

    assert "django_svcs" in settings.INSTALLED_APPS
    assert "django_svcs.middleware.request_container" in settings.MIDDLEWARE
