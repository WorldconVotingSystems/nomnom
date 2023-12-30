from unittest.mock import patch

import pytest
import social_core.strategy
from nomnom.social_core import ClydeOAuth2


class DictStrategy(social_core.strategy.BaseStrategy):
    def __init__(self, settings=None):
        self.settings = {} if settings is None else settings

    def setting(self, name, default=None, backend=None):
        return self.settings.get(name, default)

    def request_data(self, merge=True):
        return {}

    def build_absolute_uri(self, path=None):
        return path


@pytest.fixture
def clyde_oauth2(strategy):
    # we need to do a bit more for the strategy here, because the oauth implementation
    # delegates to it for a LOT of things.

    return ClydeOAuth2(strategy=strategy)


@pytest.fixture
def settings():
    return {}


@pytest.fixture
def strategy(settings):
    return DictStrategy(settings)


def test_base_url(clyde_oauth2):
    assert clyde_oauth2.base_url == "https://registration.glasgow2024.org"
    with patch.object(ClydeOAuth2, "setting", return_value="https://custom-url.org"):
        assert clyde_oauth2.base_url == "https://custom-url.org"


def test_authorization_url(clyde_oauth2):
    expected_url = "https://registration.glasgow2024.org/oauth/authorize"
    assert clyde_oauth2.authorization_url() == expected_url


def test_access_token_url(clyde_oauth2):
    expected_url = "https://registration.glasgow2024.org/api/v1/oauth/token"
    assert clyde_oauth2.access_token_url() == expected_url


def test_get_user_details(clyde_oauth2):
    response = {
        "data": {
            "id": " 123 ",
            "ticket_number": "#456",
            "email": "user@example.com ",
            "full_name": " Example User ",
            "preferred_name": "User ",
            "alternative_email": " alt@example.com",
            "badge": "True",
            "badge_title": "Dr. ",
            "wsfs_status": "Active",
            "attending_status": " Yes ",
            "date_added": "2022-08-26T12:25:18.000000Z",
            "date_updated": "2022-10-29T22:53:08.000000Z",
        }
    }

    details = clyde_oauth2.get_user_details(response)
    assert details["id"] == "123"
    assert details["username"] == "clyde-456"
    assert details["email"] == "user@example.com"
    assert details["full_name"] == "Example User"
    assert details["preferred_name"] == "User"
    assert details["alternative_email"] == "alt@example.com"
    assert details["badge"] == "True"
    assert details["badge_title"] == "Dr."
    assert details["wsfs_status"] == "Active"
    assert details["ticket_number"] == "#456"
    assert details["attending_status"] == "Yes"
    assert details["date_added"] == "2022-08-26T12:25:18.000000Z"
    assert details["date_updated"] == "2022-10-29T22:53:08.000000Z"


def test_get_user_details_missing_date(clyde_oauth2):
    response = {
        "data": {
            "id": " 123 ",
            "ticket_number": "#456",
            "email": "user@example.com ",
            "full_name": " Example User ",
            "preferred_name": "User ",
            "alternative_email": " alt@example.com",
            "badge": "True",
            "badge_title": "Dr. ",
            "wsfs_status": "Active",
            "attending_status": " Yes ",
        }
    }

    details = clyde_oauth2.get_user_details(response)
    assert details["id"] == "123"
    assert details["username"] == "clyde-456"
    assert details["email"] == "user@example.com"
    assert details["full_name"] == "Example User"
    assert details["preferred_name"] == "User"
    assert details["alternative_email"] == "alt@example.com"
    assert details["badge"] == "True"
    assert details["badge_title"] == "Dr."
    assert details["wsfs_status"] == "Active"
    assert details["ticket_number"] == "#456"
    assert details["attending_status"] == "Yes"
    assert details["date_added"] is None
    assert details["date_updated"] is None


def test_get_user_id(clyde_oauth2):
    details = {"username": "clyde-456"}
    response = {}
    user_id = clyde_oauth2.get_user_id(details, response)
    assert user_id == "clyde-456"


def test_user_data(clyde_oauth2):
    access_token = "testtoken123"
    with patch.object(
        ClydeOAuth2, "get_json", return_value={"data": "user_data"}
    ) as mock_get_json:
        user_data = clyde_oauth2.user_data(access_token)
        mock_get_json.assert_called_once_with(
            "https://registration.glasgow2024.org/api/v1/me",
            headers={"Authorization": "Bearer testtoken123"},
        )
    assert user_data == {"data": "user_data"}
