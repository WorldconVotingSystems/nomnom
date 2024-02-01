# Convention-specific functions for NomNom live in this file. It provides very generic
# implementations, but convention-specific implementations can override it by setting the
# `NOMNOM_CONVENTION_*` settings via the environment.

from collections.abc import Iterable
from dataclasses import dataclass, field
from datetime import date, datetime
from pathlib import Path
from typing import TypedDict
from urllib.parse import urlparse

from django.http import HttpRequest
from django.utils.timezone import is_aware, make_aware
from environ import bool_var, config, group, to_config, var


class ConventionException(Exception):
    ...


class ConfigurationError(ConventionException):
    ...


BASE_DIR = Path(__file__).resolve().parent.parent


def comma_separated_string(env_val: str) -> list[str]:
    return [v.strip() for v in env_val.strip().split(",") if v.strip()]


@config(prefix="NOM")
class SystemConfiguration:
    convention_app = var(default=None)

    @config
    class DB:
        name = var()
        host = var()
        port = var(5432, converter=int)
        user = var()
        password = var()

    @config
    class REDIS:
        host = var()
        port = var(6379, converter=int)

    @config
    class EMAIL:
        host = var()
        port = var(587, converter=int)
        host_user = var(default=None)
        host_password = var(default=None)
        use_tls = bool_var(default=True)

    @config
    class CONVENTION:
        hugo_packet = var(default=False)

    @config
    class SENTRY_SDK:
        dsn = var(default=None)
        environment = var(default="production")

    debug = bool_var(default=False)
    sentry_sdk = group(SENTRY_SDK)
    db = group(DB)
    redis = group(REDIS)
    email = group(EMAIL)

    @config
    class OAUTH:
        key = var()
        secret = var()
        backend = var("nomnom.social_core.ClydeOAuth2")

    @config
    class LOGGING:
        oauth_debug = bool_var(False)

    oauth = group(OAUTH)

    secret_key = var()

    static_file_root = var(BASE_DIR / "staticfiles")

    allowed_hosts: list[str] = var("", converter=comma_separated_string)

    allow_username_login: bool = bool_var(False)

    convention = group(CONVENTION)

    logging = group(LOGGING)


system_configuration = to_config(SystemConfiguration)


class URLSetting(TypedDict):
    url: str
    rel: str | None
    static: bool


def url_settings(
    urls: Iterable[str], rel: str | None = "stylesheet"
) -> list[URLSetting]:
    settings = []
    for url in urls:
        parsed = urlparse(url)
        static = not bool(parsed.scheme)
        setting = {"url": url, "static": static}
        if rel is not None:
            setting["rel"] = rel
        settings.append(setting)
    return settings


@dataclass
class ConventionTheme:
    stylesheets: str | list[str]
    font_urls: str | list[str]

    def get_stylesheets(self, request: HttpRequest | None = None) -> list[str]:
        if isinstance(self.stylesheets, str):
            return [self.stylesheets]
        return self.stylesheets

    def get_stylesheet_settings(
        self, request: HttpRequest | None = None
    ) -> list[URLSetting]:
        return url_settings(self.get_stylesheets(request))

    def get_font_urls(self, request: HttpRequest | None = None) -> list[str]:
        if isinstance(self.font_urls, str):
            return [self.font_urls]

        return self.font_urls

    def get_font_url_settings(
        self, request: HttpRequest | None = None
    ) -> list[URLSetting]:
        return url_settings(self.get_font_urls(request))


@dataclass
class ConventionConfiguration:
    name: str
    subtitle: str | None
    slug: str
    site_url: str
    hugo_help_email: str
    hugo_admin_email: str
    registration_email: str
    logo: str = "images/logo_blue.png"
    logo_alt_text: str = "NomNom Logo"
    nomination_eligibility_cutoff: date | datetime | None = None
    nominating_group: str = "Nominator"
    voting_group: str = "Voter"
    urls_app_name: str | None = None
    authentication_backends: list[str] = field(default_factory=list)

    def __post_init__(self):
        # Ensure that the nomination eligibility cutoff is a timezone-aware datetime, if set.
        if self.nomination_eligibility_cutoff is not None:
            if isinstance(self.nomination_eligibility_cutoff, date):
                self.nomination_eligibility_cutoff = datetime.combine(
                    self.nomination_eligibility_cutoff, datetime.min.time()
                )

            if not is_aware(self.nomination_eligibility_cutoff):
                self.nomination_eligibility_cutoff = make_aware(
                    self.nomination_eligibility_cutoff
                )

    def get_hugo_help_email(self, request: HttpRequest | None = None) -> str:
        return self.hugo_help_email

    def get_hugo_admin_email(self, request: HttpRequest | None = None) -> str:
        return self.hugo_admin_email

    def get_registration_email(self, request: HttpRequest | None = None) -> str:
        return self.registration_email
