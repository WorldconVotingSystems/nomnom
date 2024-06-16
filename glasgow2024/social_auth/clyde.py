import logging
from typing import Any

from social_core.backends.oauth import BaseOAuth2

logger = logging.getLogger("clyde")


class ClydeOAuth2(BaseOAuth2):
    BASE_URL = "https://registration.glasgow2024.org"
    ACCESS_TOKEN_METHOD = "POST"

    # Clyde does not support this CSRF protection
    REDIRECT_STATE = False
    STATE_PARAMETER = False
    SCOPE_SEPARATOR = ","
    DEFAULT_SCOPE = ["view-participant"]
    name = "clyde"
    USER_ID_PREFIX = "clyde"

    @property
    def base_url(self):
        if self.setting("BASE_URL"):
            return self.setting("BASE_URL")

        return self.BASE_URL

    def authorization_url(self):
        return f"{self.base_url}/oauth/authorize"

    def access_token_url(self):
        return f"{self.base_url}/api/v1/oauth/token"

    def get_user_details(self, response):
        data = response["data"]
        user_id = f"{self.USER_ID_PREFIX}-{data['ticket_number'].strip('#')}"

        def clean_value(v: Any) -> Any:
            return v.strip() if isinstance(v, str) else v

        full_details = {
            k: clean_value(v)
            for k, v in {
                "id": data["id"],
                "username": user_id,
                "email": data["email"],
                "full_name": data["full_name"],
                "preferred_name": data["preferred_name"],
                "alternative_email": data["alternative_email"],
                "badge": data["badge"],
                "badge_title": data["badge_title"],
                # This is going to be a problem
                "wsfs_status": data["wsfs_status"],
                "ticket_number": data["ticket_number"],
                "attending_status": data["attending_status"],
                "date_added": data.get("date_added", None),
                "date_updated": data.get("date_updated", None),
            }.items()
        }
        logger.info(f"Full details: {full_details}")
        return full_details

    def get_user_id(self, details, response):
        return details["username"]

    def user_data(self, access_token, *args, **kwargs):
        url = f"{self.base_url}/api/v1/me"
        response = self.request(
            url, headers={"Authorization": "Bearer " + access_token}
        )
        logger.debug(f"Response headers: {response.headers}")
        return response.json()


class ClydeStagingOAuth2(ClydeOAuth2):
    BASE_URL = "https://worldcon.staxotest.net"
    USER_ID_PREFIX = "clyde-staging"
