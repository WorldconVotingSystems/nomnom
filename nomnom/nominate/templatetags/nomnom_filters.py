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
        return user.profile.display_name or user.email
    except (AttributeError, ObjectDoesNotExist):
        return user.email


@register.filter(name="place")
def place(value):
    if value in (1, 21, 31):
        return f"{value}st Place"
    elif value in (2, 22):
        return f"{value}nd Place"
    elif value in (3, 23):
        return f"{value}rd Place"
    else:
        return f"{value}th Place"
