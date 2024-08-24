from typing import cast

from django import template
from django.http import HttpRequest
from django.utils.safestring import mark_safe
from django_svcs.apps import svcs_from
from nomnom.convention import ConventionTheme, URLSetting

from .helpers import render_link_tag

register = template.Library()

LAYOUT_STYLESHEET: URLSetting = {
    "url": "css/layout.css",
    "static": True,
    "rel": "stylesheet",
}


def layout_stylesheet_url() -> URLSetting:
    return LAYOUT_STYLESHEET


@register.simple_tag(name="site_stylesheet", takes_context=True)
def do_site_stylesheet(context: template.Context) -> str:
    """Return HTML for the site's stylesheet

    This tag is configurable.
    """
    theme = svcs_from(context.request).get(ConventionTheme)

    rendered_urls = [render_link_tag(layout_stylesheet_url())]
    request: HttpRequest | None = None
    if "request" in context:
        request = cast(HttpRequest, context["request"])

    for url in theme.get_stylesheet_settings(request):
        rendered_urls.append(render_link_tag(url))

    for url in theme.get_font_url_settings(request):
        rendered_urls.append(render_link_tag(url))

    return mark_safe(
        f"<!-- Site styles from the site_stylesheet tag -->{' '.join(rendered_urls)}"
    )
