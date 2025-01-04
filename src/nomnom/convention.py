# Convention-specific functions for NomNom live in this file. It provides very generic
# implementations, but convention-specific implementations can override it by setting the
# `NOMNOM_CONVENTION_*` settings via the environment.

import subprocess
from collections.abc import Iterable
from dataclasses import dataclass
from datetime import date, datetime
from pathlib import Path
from typing import Protocol, TypedDict
from urllib.parse import urlparse

from django.http import HttpRequest
from django.utils.timezone import is_aware, make_aware
from environ import bool_var, config, group, to_config, var
from pyrankvote import Ballot, Candidate
from pyrankvote.helpers import ElectionResults


class ConventionException(Exception): ...


class ConfigurationError(ConventionException): ...


BASE_DIR = Path(__file__).resolve().parent.parent


def comma_separated_string(env_val: str) -> list[str]:
    return [v.strip() for v in env_val.strip().split(",") if v.strip()]


def get_compose_port(service: str, base_port: int, default: int | None = None) -> int:
    port_cmd = f"docker compose port '{service}' '{base_port}'"
    try:
        interface = subprocess.run(
            port_cmd, shell=True, capture_output=True, check=True
        )
        port_str = interface.stdout.decode().strip().split(":")[-1]
        return int(port_str)
    except (subprocess.CalledProcessError, ValueError, IndexError, TypeError):
        if default is not None:
            return default
        raise

    assert False, "Unreachable"


@config(prefix="NOM")
class SystemConfiguration:
    convention_app = var(default=None)

    @config
    class DB:
        name = var()
        host = var()
        port = var(get_compose_port("db", 5432, 5432), converter=int)
        user = var()
        password = var()

    @config
    class REDIS:
        host = var()
        port = var(get_compose_port("redis", 6379, 6379), converter=int)

    @config
    class EMAIL:
        host = var()
        port = var(get_compose_port("mailcatcher", 1025, 1025), converter=int)
        host_user = var(default=None)
        host_password = var(default=None)
        use_tls = bool_var(default=True)

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

    @config
    class LOGGING:
        oauth_debug = bool_var(False)

    oauth = group(OAUTH, optional=True)

    secret_key = var()

    static_file_root = var(BASE_DIR / "staticfiles")

    allowed_hosts: list[str] = var("", converter=comma_separated_string)

    allow_username_login: bool = bool_var(False)

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

    @property
    def functional_stylesheets(self) -> list[str]:
        return ["css/advise.css"]

    def get_stylesheets(self, request: HttpRequest | None = None) -> list[str]:
        if isinstance(self.stylesheets, str):
            instance_sheets = [self.stylesheets]
        else:
            instance_sheets = self.stylesheets[:]
        instance_sheets.extend(self.functional_stylesheets)
        return instance_sheets

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
    hugo_packet_backend: str | None = None
    advisory_votes_enabled: bool = False

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

    @property
    def packet_enabled(self):
        return self.hugo_packet_backend is not None


class HugoCounter(Protocol):
    def __call__(
        self,
        candidates: list[Candidate],
        ballots: list[Ballot],
        runoff_candidate: Candidate | None = None,
    ) -> ElectionResults: ...


@dataclass
class HugoAwards:
    results_class: type[ElectionResults]
    counter: HugoCounter
    hugo_nominations_per_member: int
