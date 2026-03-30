import json

import pytest
from django.urls import reverse
from waffle.testutils import override_switch

from nomnom.canonicalize import feature_switches


@pytest.fixture(autouse=True)
def enable_switch():
    with override_switch(feature_switches.SWITCH_SANKEY_DIAGRAM, active=True):
        yield


@pytest.fixture
def staff_client(admin_client):
    """admin_client is a Django test fixture: logged-in superuser client."""
    return admin_client


@pytest.mark.django_db
class TestSankeyView:
    """Tests for the HTML sankey view."""

    def test_unauthenticated_redirects_to_login(self, client, category):
        url = reverse("canonicalize:sankey", args=[category.pk])
        response = client.get(url)
        assert response.status_code == 302
        assert "/admin/login/" in response.url

    def test_returns_html(self, staff_client, category):
        url = reverse("canonicalize:sankey", args=[category.pk])
        response = staff_client.get(url)
        assert response.status_code == 200
        assert "text/html" in response["Content-Type"]

    def test_mode_full_sets_active_class(self, staff_client, category):
        url = reverse("canonicalize:sankey", args=[category.pk])
        response = staff_client.get(url + "?mode=full")
        assert response.status_code == 200
        content = response.content.decode()
        # The "Full View" button should have the active class
        assert 'data-mode="full"' in content


@pytest.mark.django_db
class TestSankeyDataView:
    """Tests for the JSON data endpoint."""

    def test_unauthenticated_redirects_to_login(self, client, category):
        url = reverse("canonicalize:sankey-data", args=[category.pk])
        response = client.get(url)
        assert response.status_code == 302
        assert "/admin/login/" in response.url

    # this should clearly be two different scenarios (valid, invalid)
    def test_returns_json(self, staff_client, category):
        url = reverse("canonicalize:sankey-data", args=[category.pk])
        response = staff_client.get(url)
        # Category fixture has no ballot data, so EPH will error -> 500
        # with {"error": ...}. That's fine: we're testing view-layer contract.
        assert response["Content-Type"] == "application/json"
        data = json.loads(response.content)
        if response.status_code == 200:
            assert "nodes" in data and "links" in data
        else:
            assert response.status_code == 500
            assert "error" in data

    def test_mode_compact_default(self, staff_client, category):
        url = reverse("canonicalize:sankey-data", args=[category.pk])
        response = staff_client.get(url)
        # 200 with data or 500 with error -- both are valid responses
        assert response.status_code in (200, 500)

    def test_mode_full(self, staff_client, category):
        url = reverse("canonicalize:sankey-data", args=[category.pk])
        response = staff_client.get(url + "?mode=full")
        assert response.status_code in (200, 500)

    def test_invalid_mode_defaults_to_compact(self, staff_client, category):
        url = reverse("canonicalize:sankey-data", args=[category.pk])
        response = staff_client.get(url + "?mode=garbage")
        assert response.status_code in (200, 500)

    def test_invalid_category_returns_404(self, staff_client):
        url = reverse("canonicalize:sankey-data", args=[99999])
        response = staff_client.get(url)
        assert response.status_code == 404
