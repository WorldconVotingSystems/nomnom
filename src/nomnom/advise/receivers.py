from nomnom.base.signals import index_content_load

from . import models


def add_advise_content(sender, request, **kwargs):
    return {"proposals": models.Proposal.open.all()}


index_content_load.connect(add_advise_content)
