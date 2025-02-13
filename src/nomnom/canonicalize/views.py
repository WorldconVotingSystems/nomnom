from django.db import transaction
from django.http import Http404, HttpRequest, HttpResponse

from nomnom.canonicalize.models import Work, group_nominations
from nomnom.nominate import models as nominate


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
    work = None
    if work_id is not None:
        try:
            work = Work.objects.get(pk=work_id)
        except Work.DoesNotExist:
            # this is a 404 because the user is asking for something that doesn't exist.
            raise Http404(
                "The work you're trying to associate nominations with does not exist."
            )

    work = group_nominations(nominations, work)

    work.save()

    return HttpResponse("done")
