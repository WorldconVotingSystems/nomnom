from typing import Any, cast

from django import template
from django.forms.utils import flatatt
from django.http import HttpRequest
from django.templatetags.static import static
from django.utils.encoding import force_str
from django.utils.html import format_html
from django.utils.safestring import mark_safe
from django_svcs.apps import svcs_from
from nomnom.convention import ConventionTheme, URLSetting

register = template.Library()

LAYOUT_STYLESHEET: URLSetting = {
    "url": "css/layout.css",
    "static": True,
    "rel": "stylesheet",
}


def layout_stylesheet_url() -> URLSetting:
    return LAYOUT_STYLESHEET


def render_link_tag(url: str | URLSetting) -> str:
    if isinstance(url, str):
        attrs = {"url": url}
    else:
        attrs: dict[str, Any] = {k: v for k, v in url.items()}

    attrs["href"] = attrs.pop("url")
    url_is_static = attrs.pop("static", False)
    if url_is_static:
        attrs["href"] = static(attrs["href"])

    return render_tag("link", attrs, close=False)


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


def render_tag(tag, attrs=None, content=None, close=True):
    """Render an HTML tag."""
    attrs_string = flatatt(attrs) if attrs else ""
    builder = "<{tag}{attrs}>{content}"
    content_string = text_value(content)
    if content_string or close:
        builder += "</{tag}>"
    return format_html(builder, tag=tag, attrs=attrs_string, content=content_string)


def text_value(value):
    """Force a value to text, render None as an empty string."""
    if value is None:
        return ""
    return force_str(value)
