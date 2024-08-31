from django import template
from django.contrib.auth.base_user import AbstractBaseUser

import nomnom.advise.models

register = template.Library()


@register.filter(name="proposal_is_open_for")
def proposal_is_open_for(
    proposal: nomnom.advise.models.Proposal, user: AbstractBaseUser
) -> bool:
    return True
