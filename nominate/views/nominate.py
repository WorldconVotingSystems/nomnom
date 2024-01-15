from django.contrib import messages
from django.db import transaction
from django.http import HttpRequest
from django.shortcuts import redirect
from django.utils.translation import gettext as _
from ipware import get_client_ip

from nominate import models
from nominate.forms import NominationFormset
from nominate.tasks import send_ballot

from .base import NominatorView


class NominationView(NominatorView):
    template_name = "nominate/nominate.html"

    def build_ballot_forms(self, data=None):
        args = [] if data is None else [data]
        return {
            category: NominationFormset(
                *args,
                form_kwargs={"category": category},
                queryset=models.Nomination.objects.filter(
                    category=category, nominator=self.profile()
                ),
                prefix=str(category.id),
            )
            for category in self.categories()
        }

    def get_context_data(self, **kwargs):
        formsets = kwargs.pop("formsets", None)
        if formsets is None:
            formsets = self.build_ballot_forms()
        ctx = {"formsets": formsets}
        ctx.update(super().get_context_data(**kwargs))
        return ctx

    def get(self, request: HttpRequest, *args, **kwargs):
        if not self.election().user_can_nominate(request.user):
            self.template_name = "nominate/election_closed.html"
            self.extra_context = {"object": self.election()}

        return super().get(request, *args, **kwargs)

    @transaction.atomic
    def post(self, request: HttpRequest, *args, **kwargs):
        if not self.election().user_can_nominate(request.user):
            messages.error(
                request, f"You do not have nominating rights for {self.election()}"
            )
            return redirect("election:index")

        profile = self.profile()
        had_errors = False
        client_ip_address, _ = get_client_ip(request=request)
        formsets = {
            category: NominationFormset(
                request.POST,
                request.FILES,
                form_kwargs={"category": category},
                prefix=str(category.id),
            )
            for category in self.categories()
        }

        for category, formset in formsets.items():
            if formset.is_valid():
                for nomination_record in formset.save(commit=False):
                    nomination_record.category = category
                    nomination_record.nominator = profile
                    nomination_record.nomination_ip_address = client_ip_address
                    nomination_record.save()

                for deleted in formset.deleted_objects:
                    deleted.delete()
            else:
                had_errors = True

        if not had_errors:
            messages.success(request, "Your set of nominations was saved")
            return redirect(
                "election:nominate", election_id=self.kwargs.get("election_id")
            )
        else:
            messages.warning(request, "Something wasn't quite right with your ballot")
            return self.render_to_response(self.get_context_data(formsets=formsets))


class EmailNominations(NominatorView):
    def post(self, request: HttpRequest, *args, **kwargs):
        send_ballot.delay(
            self.election().id,
            self.profile().id,
        )
        messages.success(request, _("An email will be sent to you with your ballot"))

        return redirect("election:nominate", election_id=self.kwargs.get("election_id"))
