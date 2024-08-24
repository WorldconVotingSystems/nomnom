from django import template
from django.utils.safestring import mark_safe
from django_bootstrap5.core import get_bootstrap_setting
from django_bootstrap5.templatetags import django_bootstrap5

from nomnom.convention import URLSetting
from .helpers import render_link_tag, render_script_tag

register = template.Library()

STATIC_BOOTSTRAP_STYLESHEET: URLSetting = {
    "url": "css/bootstrap.min.css",
    "static": True,
    "rel": "stylesheet",
}

STATIC_BOOTSTRAP_SCRIPT: URLSetting = {
    "url": "js/bootstrap.min.js",
    "static": True,
}


@register.simple_tag(name="bootstrap_css")
def do_bootstrap_css() -> str:
    return mark_safe(render_link_tag(bootstrap_css_url()))


@register.simple_tag(name="bootstrap_javascript")
def do_bootstrap_js() -> str:
    return mark_safe(render_script_tag(bootstrap_js_url()))


def bootstrap_css_url() -> URLSetting | str:
    # if we have defined a static bootstrap CSS config, return a static URL setting, otherwise
    # return the URL provided by django bootstrap5
    if get_bootstrap_setting("serve_static", False):
        return STATIC_BOOTSTRAP_STYLESHEET
    else:
        return django_bootstrap5.bootstrap_css_url()


def bootstrap_js_url() -> URLSetting | str:
    if get_bootstrap_setting("serve_static", False):
        return STATIC_BOOTSTRAP_SCRIPT
    else:
        return django_bootstrap5.bootstrap_javascript_url()
