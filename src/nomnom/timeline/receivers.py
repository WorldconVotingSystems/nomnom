from waffle import switch_is_active

from nomnom.base.signals import index_content_load
from nomnom.timeline.feature_switches import SWITCH_TIMELINE

from . import models


def add_timeline_content(sender, request, **kwargs):
    if not switch_is_active(SWITCH_TIMELINE):
        return {}
    timeline_events = list(models.TimelineEvent.objects.all())
    _annotate_collapsed_visibility(timeline_events)
    return {
        "timeline_events": timeline_events,
        "any_provisional": any(e.provisional for e in timeline_events),
    }


def _annotate_collapsed_visibility(events):
    boundary = next(
        (i - 1 for i, e in enumerate(events) if not e.complete),
        len(events) - 1,
    )
    for i, event in enumerate(events):
        event.shown_collapsed = i in (boundary, boundary + 1, boundary + 2)


index_content_load.connect(add_timeline_content)
