from waffle import switch_is_active

from nomnom.base.feature_switches import SWITCH_ADVISORY_VOTES
from nomnom.base.signals import index_content_load

from . import models


def add_advise_content(sender, request, **kwargs):
    if not switch_is_active(SWITCH_ADVISORY_VOTES):
        return {}
    return {"proposals": models.Proposal.open.all()}


index_content_load.connect(add_advise_content)
