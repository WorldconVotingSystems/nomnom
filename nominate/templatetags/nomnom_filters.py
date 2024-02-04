from bs4 import BeautifulSoup
from django import template

register = template.Library()


@register.filter(name="strip_html_tags")
def strip_tags(value):
    if value:
        soup = BeautifulSoup(value, "html.parser")
        return soup.get_text(separator=" ", strip=True)

    return ""
