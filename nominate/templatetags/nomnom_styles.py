from typing import Any

from django import template
from django.conf import settings
from django.forms.utils import flatatt
from django.templatetags.static import static
from django.utils.encoding import force_str
from django.utils.html import format_html
from django.utils.safestring import mark_safe

register = template.Library()

LAYOUT_STYLESHEET = {"url": "css/layout.css", "static": True}
STYLESHEET_DEFAULT = {"url": "css/nominate.css", "static": True}
FONT_DEFAULT = {
    "url": "https://fonts.googleapis.com/css2?family=Roboto&family=Roboto+Slab&display=swap",
    "static": False,
}
DEFAULTS = {
    "stylesheet": STYLESHEET_DEFAULT,
    "font": FONT_DEFAULT,
}


def get_url_setting(name: str, static: bool = True) -> dict[str, Any]:
    setting_name = f"NOMNOM_SITE_{name.upper()}"
    setting = getattr(settings, setting_name, None)
    if setting is None:
        # setting is now a link dict
        setting = DEFAULTS[name]
    elif isinstance(setting, str):
        setting = {
            "url": setting,
            "static": static,
        }
    return setting


def site_stylesheet_setting() -> dict[str, Any]:
    return get_url_setting("stylesheet", static=True)


def site_font_setting() -> dict[str, Any]:
    return get_url_setting("font", static=False)


def stylesheet_url(attrs: dict[str, Any]) -> dict[str, Any]:
    if "rel" not in attrs:
        attrs["rel"] = "stylesheet"
    return attrs


def layout_stylesheet_url() -> dict[str, Any]:
    return stylesheet_url(LAYOUT_STYLESHEET)


def site_stylesheet_url() -> dict[str, Any]:
    return stylesheet_url(site_stylesheet_setting())


def site_font_url() -> dict[str, Any]:
    return stylesheet_url(site_font_setting())


def render_link_tag(url: str | dict[str, Any]) -> str:
    if isinstance(url, str):
        attrs = {"url": url}
    else:
        attrs = url.copy()

    attrs["href"] = attrs.pop("url")
    url_is_static = attrs.pop("static", False)
    if url_is_static:
        attrs["href"] = static(attrs["href"])

    return render_tag("link", attrs, close=False)


@register.simple_tag(name="site_stylesheet")
def do_site_stylesheet() -> str:
    """Return HTML for the site's stylesheet

    This tag is configurable.
    """
    rendered_urls = [render_link_tag(layout_stylesheet_url())]

    if site_stylesheet_url():
        rendered_urls.append(render_link_tag(site_stylesheet_url()))

    if site_font_url():
        rendered_urls.append(render_link_tag(site_font_url()))

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
