from waffle import switch_is_active

from nomnom.base.signals import index_content_load
from nomnom.timeline.feature_switches import SWITCH_TIMELINE

from . import models


def add_timeline_content(sender, request, **kwargs):
    if not switch_is_active(SWITCH_TIMELINE):
        return {}
    timeline_events = list(models.TimelineEvent.objects.all())
    return {
        "timeline_events": timeline_events,
        "any_provisional": any(e.provisional for e in timeline_events),
    }


index_content_load.connect(add_timeline_content)
