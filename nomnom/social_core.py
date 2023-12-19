from social_core.backends.oauth import BaseOAuth2


class ClydeOAuth2(BaseOAuth2):
    BASE_URL = "https://registration.glasgow2024.org"
    ACCESS_TOKEN_METHOD = "POST"

    # Clyde does not support this CSRF protection
    REDIRECT_STATE = False
    STATE_PARAMETER = False
    SCOPE_SEPARATOR = ","
    DEFAULT_SCOPE = ["view-participant"]
    name = "clyde"

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

        return {
            "id": data["id"],
            "username": f"{self.name}-{data['id']}",
            "email": data["email"],
            "full_name": data["full_name"],
            "preferred_name": data["preferred_name"],
            "alternative_email": data["alternative_email"],
            "badge": data["badge"],
            "badge_title": data["badge_title"],
            "wsfs_status": data["wsfs_status"],
            "ticket_number": data["ticket_number"],
            "attending_status": data["attending_status"],
        }

    def get_user_id(self, details, response):
        return f"{self.name}-${details['id']}"

    def user_data(self, access_token, *args, **kwargs):
        url = f"{self.base_url}/api/v1/me"
        return self.get_json(url, headers={"Authorization": "Bearer " + access_token})


class ClydeStagingOAuth2(ClydeOAuth2):
    BASE_URL = "https://worldcon.staxotest.net"

    # # delete these once I have Clyde demo access
    # def authorization_url(self):
    #     return "https://authorization-server.com/authorize"

    # def access_token_url(self):
    #     return "https://authorization-server.com/token"
