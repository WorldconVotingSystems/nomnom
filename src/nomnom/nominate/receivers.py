from nomnom.base.signals import index_content_load

from . import models


def add_nominate_content(sender, request, **kwargs):
    return {
        "object_list": models.Election.enrich_with_user_data(
            models.Election.objects.all(), request
        )
    }


index_content_load.connect(add_nominate_content)
