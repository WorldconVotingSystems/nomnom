from typing import Any

from django.forms.utils import flatatt
from django.templatetags.static import static
from django.utils.encoding import force_str
from django.utils.html import format_html
from nomnom.convention import URLSetting


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


def render_script_tag(url: str | URLSetting) -> str:
    if isinstance(url, str):
        attrs = {"url": url}
    else:
        attrs: dict[str, Any] = {k: v for k, v in url.items()}
    attrs["src"] = attrs.pop("url")
    url_is_static = attrs.pop("static", False)
    if url_is_static:
        attrs["src"] = static(attrs["src"])

    return render_tag("script", attrs, close=True)


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
