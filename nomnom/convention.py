# Convention-specific functions for NomNom live in this file. It provides very generic
# implementations, but convention-specific implementations can override it by setting the
# `NOMNOM_CONVENTION_*` settings via the environment.

from collections.abc import Iterable
from dataclasses import dataclass
from typing import TypedDict
from urllib.parse import urlparse

from django.http import HttpRequest


class ConventionException(Exception):
    ...


class ConfigurationError(ConventionException):
    ...


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
    nominating_group: str = "Nominator"
    voting_group: str = "Voter"

    def get_hugo_help_email(self, request: HttpRequest | None = None) -> str:
        return self.hugo_help_email

    def get_hugo_admin_email(self, request: HttpRequest | None = None) -> str:
        return self.hugo_admin_email

    def get_registration_email(self, request: HttpRequest | None = None) -> str:
        return self.registration_email
