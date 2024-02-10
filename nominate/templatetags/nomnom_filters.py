from bs4 import BeautifulSoup
from django import template

register = template.Library()


@register.filter(name="strip_html_tags")
def html_text(html: str) -> str:
    if html:
        soup = BeautifulSoup(html, "html.parser")
        return soup.get_text(separator=" ", strip=True)

    return ""


@register.filter(name="get_item")
def get_item(dictionary, key):
    return dictionary.get(key)
