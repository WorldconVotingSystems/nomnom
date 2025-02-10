from django.db import transaction
from django.http import Http404, HttpRequest, HttpResponse
from django.shortcuts import render
from django.views.generic import ListView

from nomnom.canonicalize.models import Work
from nomnom.nominate import models as nominate


class NominationGroupingView(ListView):
    def get_queryset(self):
        #
        return nominate.Nomination.objects.all()


@transaction.atomic
def group_works(request: HttpRequest, work_id: int | None = None) -> HttpResponse:
    """Group a set of nominations into a single Work.

    The outcome of this is that every nomination in the group will be
    associated with the single work referenced in the invocation.
    """
    # two things to consider here:
    #
    # 1. We will associate both invalid and valid nominations; even if the admin has invalidated a nomination, we want it to be associated with the Work.
    # 2. If we get a request for a nomination that doesn't exist, we need to respond with an error; that's an indication that something is wrong.
    nomination_ids = request.POST.getlist("nominations")
    if not nominate.Nomination.objects.filter(pk__in=nomination_ids).count() == len(
        nomination_ids
    ):
        # this is a 404 because the user is asking for something that doesn't exist.
        raise Http404("Some of the nominations you're trying to group do not exist.")

    nominations = nominate.Nomination.objects.filter(pk__in=nomination_ids)

    # if we have a work ID, we are going to attempt to associate the nominations with that work.
    if work_id is not None:
        try:
            work = Work.objects.get(pk=work_id)
        except Work.DoesNotExist:
            # this is a 404 because the user is asking for something that doesn't exist.
            raise Http404(
                "The work you're trying to associate nominations with does not exist."
            )

        # if any of those nominations are already associated with a work, we need to remove them from that work.
        for nomination in nominations:
            if nomination.work is not None:
                nomination.work.nominations.remove(nomination)

    else:
        works = set()
        for nomination in nominations:
            if nomination.work is not None:
                works.add(nomination.work)

        if len(set(works)) > 1:
            # this is a 400 because the user is trying to associate nominations with multiple works.
            return HttpResponse(
                "You cannot associate nominations with multiple works.", status=400
            )

        if set(works):
            work = works.pop()

        else:
            work = Work.objects.create(
                name=nominations.first().pretty_fields(),
                category=nominations.first().category,
            )

    work.nominations.add(*nominations)
    work.save()

    return render(request, "canonicalize/group_works.html")
