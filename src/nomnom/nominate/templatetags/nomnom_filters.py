import inflect
from bs4 import BeautifulSoup
from django import template
from django.core.exceptions import ObjectDoesNotExist

register = template.Library()


@register.filter(name="strip_html_tags")
def html_text(html: str) -> str:
    if html:
        soup = BeautifulSoup(html, "html.parser")
        return soup.get_text(separator=" ", strip=True)

    return ""


# It is outright ridiculous that this needs to be built in 2024
@register.filter(name="get_item")
def get_item(dictionary, key):
    return dictionary.get(key)


@register.filter(name="user_display_name")
def user_display_name(user):
    try:
        return user.convention_profile.display_name or user.email
    except (AttributeError, ObjectDoesNotExist):
        return user.email


p = inflect.engine()


@register.filter(name="place")
def place(value):
    return f"{p.ordinal(value)} Place"
