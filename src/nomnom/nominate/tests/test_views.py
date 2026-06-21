import itertools
from collections.abc import Iterable
from unittest import mock

import pytest
from django.contrib.auth.models import Permission
from django.contrib.messages import get_messages
from django.core import mail
from django.test import TestCase
from django.urls import reverse

from nomnom.nominate import factories, models

pytestmark = pytest.mark.usefixtures("db")


class TestElectionView(TestCase):
    def setup_method(self, test_method):
        self.member = factories.NominatingMemberProfileFactory.create()
        self.user = self.member.user

    def test_get_queryset(self):
        self.client.force_login(self.user)
        response = self.client.get(reverse("election:index"))
        assert response.status_code == 200


class TestElectionModeView(TestCase):
    def setup_method(self, test_method):
        self.election = factories.ElectionFactory.create()
        self.member = factories.NominatingMemberProfileFactory.create()
        self.user = self.member.user

    def redirect_url(self):
        return reverse("election:redirect", kwargs={"election_id": self.election.slug})

    def grant(self, codename):
        self.user.user_permissions.add(
            Permission.objects.get(
                codename=codename, content_type__app_label="nominate"
            )
        )

    def test_get_nominating_redirect_url(self):
        self.election.state = models.Election.STATE.NOMINATIONS_OPEN
        self.election.save()
        self.grant("nominate")
        self.client.force_login(self.user)
        response = self.client.get(self.redirect_url())
        expected_url = reverse(
            "election:nominate", kwargs={"election_id": self.election.slug}
        )
        assert response.status_code == 302
        assert response.url == expected_url

    def test_get_nominating_redirect_url_without_rights(self):
        self.election.state = models.Election.STATE.NOMINATIONS_OPEN
        self.election.save()
        self.client.force_login(self.user)
        response = self.client.get(self.redirect_url())
        expected_url = reverse(
            "election:closed", kwargs={"election_id": self.election.slug}
        )
        assert response.status_code == 302
        assert response.url == expected_url

    def test_get_voting_redirect_url(self):
        self.election.state = models.Election.STATE.VOTING
        self.election.save()
        self.grant("vote")
        self.client.force_login(self.user)
        response = self.client.get(self.redirect_url())
        expected_url = reverse(
            "election:vote", kwargs={"election_id": self.election.slug}
        )
        assert response.status_code == 302
        assert response.url == expected_url

    def test_get_voting_redirect_url_without_rights(self):
        self.election.state = models.Election.STATE.VOTING
        self.election.save()
        self.client.force_login(self.user)
        response = self.client.get(self.redirect_url())
        expected_url = reverse(
            "election:closed", kwargs={"election_id": self.election.slug}
        )
        assert response.status_code == 302
        assert response.url == expected_url

    def test_get_redirect_url_closed(self):
        self.election.state = models.Election.STATE.PRE_NOMINATION
        self.election.save()
        self.client.force_login(self.user)
        response = self.client.get(self.redirect_url())
        expected_url = reverse(
            "election:closed", kwargs={"election_id": self.election.slug}
        )
        assert response.status_code == 302
        assert response.url == expected_url


class TestClosedElectionView(TestCase):
    def setup_method(self, test_method):
        self.election = factories.ElectionFactory.create(
            state=models.Election.STATE.NOMINATIONS_CLOSED
        )
        self.member = factories.NominatingMemberProfileFactory.create()
        self.user = self.member.user
        self.view_url = reverse(
            "election:nominate", kwargs={"election_id": self.election.slug}
        )

    def test_get_anonymous(self):
        url = self.view_url
        response = self.client.get(url)
        assert response.status_code == 302

    def test_get_nominator(self):
        url = self.view_url
        self.client.force_login(self.user)
        response = self.client.get(url)
        assert response.status_code == 200
        template_names = [t.name for t in response.templates]
        assert "nominate/show_nominations.html" in template_names

    def test_nominations_includes_only_logged_in_member(self):
        c1 = factories.CategoryFactory.create(
            election=self.election,
            fields=2,
            ballot_position=1,
        )
        other_member = factories.NominatingMemberProfileFactory.create()
        factories.NominationFactory.create_batch(
            2,
            category=c1,
            nominator=other_member,
        )
        factories.NominationFactory.create_batch(
            2,
            category=c1,
            nominator=self.member,
        )
        self.client.force_login(self.user)
        response = self.client.get(self.view_url)
        nominations: Iterable[models.Nomination] = itertools.chain.from_iterable(
            response.context_data["nominations"].values()
        )

        assert all(n.nominator == self.member for n in nominations)


class NominationViewSubmitMixin:
    def submit_nominations(self, data, extra=None):
        extra = extra or {}
        headers = {}
        url = self.view_url()
        self.client.force_login(self.user)
        response = self.client.post(url, data=data, headers=headers, **extra)
        return response


class NominationHTMXSubmitMixin:
    def submit_nominations(self, data, extra=None):
        extra = extra or {}
        headers = {"HX-Request": "true"}
        url = self.view_url()
        self.client.force_login(self.user)
        response = self.client.post(url, data=data, headers=headers, **extra)
        return response


class NominationViewInvariants(TestCase):
    __test__ = False

    def setup_method(self, test_method):
        self.election = factories.ElectionFactory.create(state="nominating")
        self.member = factories.NominatingMemberProfileFactory.create()
        self.user = self.member.user
        # The profile whose ballot is being edited. For the regular nominating
        # views this is the logged-in member themselves; admin subclasses
        # override this so the invariants run against a *different* member's
        # ballot than the logged-in actor.
        self.nominating_profile = self.member
        self.user.user_permissions.add(
            Permission.objects.get(
                codename="nominate", content_type__app_label="nominate"
            )
        )
        self.c1 = factories.CategoryFactory.create(
            election=self.election,
            fields=2,
            ballot_position=1,
        )
        self.c2 = factories.CategoryFactory.create(
            election=self.election,
            fields=2,
            ballot_position=2,
        )

    def test_get_anonymous(self):
        url = self.view_url()
        response = self.client.get(url)
        assert response.status_code == 302
        assert response.url == f"{reverse('login')}?next={url}"

    def test_get_form(self):
        self.client.force_login(self.user)
        response = self.client.get(self.view_url())
        assert response.status_code == 200

    def test_submitting_valid_data_does_not_remove_other_members_nominations(self):
        other_member = factories.NominatingMemberProfileFactory.create()
        factories.NominationFactory.create_batch(
            2,
            category=self.c1,
            nominator=other_member,
        )
        assert models.Nomination.objects.count() == 2
        valid_data = {
            f"{self.c1.id}-0-field_1": "t1",
            f"{self.c1.id}-0-field_2": "a1",
        }
        response = self.submit_nominations(valid_data)
        assert response.status_code == self.success_status_code
        assert models.Nomination.objects.count() == 3

    def test_submitting_data_with_ip_headers_from_proxy_persists_ip(self):
        valid_data = {
            f"{self.c1.id}-0-field_1": "t1",
            f"{self.c1.id}-0-field_2": "a1",
        }

        self.submit_nominations(
            valid_data, extra={"HTTP_X_FORWARDED_FOR": "111.111.111.111"}
        )
        assert models.Nomination.objects.count() == 1
        assert all(
            ip == "111.111.111.111"
            for ip in models.Nomination.objects.all().values_list(
                "nomination_ip_address", flat=True
            )
        )

    def test_submitting_valid_data_clears_previous_nominations_for_member(self):
        factories.NominationFactory.create_batch(
            2,
            category=self.c1,
            nominator=self.nominating_profile,
        )
        assert models.Nomination.objects.count() == 2
        valid_data = {
            f"{self.c1.id}-0-field_1": "t1",
            f"{self.c1.id}-0-field_2": "a1",
        }
        response = self.submit_nominations(valid_data)
        assert response.status_code == self.success_status_code
        assert models.Nomination.objects.count() == 1

    def test_submitting_invalid_data_does_not_save(self):
        # Define your initial form data that is invalid
        invalid_data = {
            f"{self.c1.id}-0-field_1": "title 1",
            f"{self.c1.id}-0-field_2": "",
            f"{self.c1.id}-1-field_1": "title 2",
            f"{self.c1.id}-1-field_2": "",
            f"{self.c2.id}-0-field_1": "title 1",
            f"{self.c2.id}-0-field_2": "",
            f"{self.c2.id}-2-field_1": "title 3",
            f"{self.c2.id}-2-field_2": "",
        }
        # Submit the form for the first time
        response = self.submit_nominations(invalid_data)
        assert response.status_code == 200
        assert models.Nomination.objects.count() == 0

    def test_submitting_invalid_data_is_nondestructive(self):
        factories.NominationFactory.create(category=self.c1)
        factories.NominationFactory.create(category=self.c2)

        # Define your initial form data that is invalid
        invalid_data = {
            f"{self.c1.id}-0-field_1": "title 1",
            f"{self.c1.id}-0-field_2": "",
            f"{self.c1.id}-1-field_1": "title 2",
            f"{self.c1.id}-1-field_2": "",
            f"{self.c2.id}-0-field_1": "title 1",
            f"{self.c2.id}-0-field_2": "",
            f"{self.c2.id}-2-field_1": "title 3",
            f"{self.c2.id}-2-field_2": "",
        }
        # Submit the form for the first time
        response = self.submit_nominations(invalid_data)
        assert response.status_code == 200
        assert models.Nomination.objects.count() == 2

    def test_series_of_submission_consistency(self):
        # Define your initial form data that is invalid
        invalid_data = {
            f"{self.c1.id}-0-field_1": "novel title 1",
            f"{self.c1.id}-0-field_2": "",
            f"{self.c1.id}-1-field_1": "novel title 2",
            f"{self.c1.id}-1-field_2": "",
            f"{self.c2.id}-0-field_1": "novella title 1",
            f"{self.c2.id}-0-field_2": "",
            f"{self.c2.id}-2-field_1": "novella title 3",
            f"{self.c2.id}-2-field_2": "",
        }

        # Submit the form for the first time
        response = self.submit_nominations(invalid_data)
        assert response.status_code == 200
        assert models.Nomination.objects.count() == 0

        # Modify invalid_data if necessary based on the response
        invalid_data.update(
            {
                f"{self.c1.id}-0-field_2": "novel author 1",
                f"{self.c1.id}-1-field_2": "novel author 2",
            }
        )

        # Submit the form for the second time
        response = self.submit_nominations(invalid_data)
        assert response.status_code == 200
        assert models.Nomination.objects.count() == 0

        # Now define valid data, could be the modifications needed after two invalid attempts
        valid_data = invalid_data.copy()  # Start with the last invalid data
        valid_data.update(
            {
                f"{self.c2.id}-0-field_2": "novella author 1",
                f"{self.c2.id}-2-field_2": "novella author 2",
            }
        )

        # Submit the form for the third time, now with valid data
        response = self.submit_nominations(valid_data)
        assert response.status_code == self.success_status_code
        assert models.Nomination.objects.count() == 4

    def test_order_of_values_is_preserved(self):
        data = field_data(self.c1, 0, "title 1", "author 1")
        data.update(field_data(self.c1, 1, "title 2", "author 2"))
        data.update(field_data(self.c1, 2, "title 3", "author 3"))

        self.submit_nominations(data)

        assert self.nominating_profile.nomination_set.count() == 3
        assert self.nominating_profile.nomination_set.first().field_1 == "title 1"
        assert self.nominating_profile.nomination_set.last().field_1 == "title 3"


class TestNominationViewFull(NominationViewInvariants, NominationViewSubmitMixin):
    __test__ = True
    success_status_code = 302

    def view_url(self):
        return reverse("election:nominate", kwargs={"election_id": self.election.slug})


class TestNominationViewHTMX(NominationViewInvariants, NominationHTMXSubmitMixin):
    __test__ = True
    success_status_code = 200

    def view_url(self):
        return reverse("election:nominate", kwargs={"election_id": self.election.slug})


class AdminNominationInvariants(NominationViewInvariants):
    """Run the shared ballot-submission invariants against the admin edit view.

    The logged-in actor is a staff member with the ``edit_ballot`` permission,
    while the ballot being edited belongs to a *different* member
    (``self.member``). This ensures the admin view honours the same
    save/clear/ordering/validation guarantees as the member-facing view.
    """

    __test__ = False

    def setup_method(self, test_method):
        self.election = factories.ElectionFactory.create(state="nominating")
        # The member whose ballot is being edited by the admin.
        self.member = factories.NominatingMemberProfileFactory.create()
        self.nominating_profile = self.member

        # The logged-in actor: a staff user with edit_ballot rights.
        staff_user = factories.UserFactory.create(is_staff=True)
        self.staff = factories.NominatingMemberProfileFactory.create(user=staff_user)
        self.user = self.staff.user
        self.user.user_permissions.add(
            Permission.objects.get(
                codename="edit_ballot", content_type__app_label="nominate"
            )
        )

        self.c1 = factories.CategoryFactory.create(
            election=self.election,
            fields=2,
            ballot_position=1,
        )
        self.c2 = factories.CategoryFactory.create(
            election=self.election,
            fields=2,
            ballot_position=2,
        )

    def view_url(self):
        return reverse(
            "election:edit_nominations",
            kwargs={"election_id": self.election.slug, "member_id": self.member.id},
        )


class TestAdminNominationViewFull(AdminNominationInvariants, NominationViewSubmitMixin):
    __test__ = True
    success_status_code = 302


class TestAdminNominationViewHTMX(AdminNominationInvariants, NominationHTMXSubmitMixin):
    __test__ = True
    success_status_code = 200


class TestAdminNominationView(TestCase):
    def setup_method(self, test_method):
        self.election = factories.ElectionFactory(state="nominating")
        self.member = factories.NominatingMemberProfileFactory.create()
        staff_user = factories.UserFactory.create(is_staff=True)
        self.staff = factories.NominatingMemberProfileFactory.create(user=staff_user)
        self.c1 = factories.CategoryFactory.create(
            election=self.election,
            fields=2,
            ballot_position=1,
        )

    @property
    def url(self):
        return reverse(
            "election:edit_nominations",
            kwargs={"election_id": self.election.slug, "member_id": self.member.id},
        )

    def submit_nominations(self, data, extra=None):
        extra = extra or {}
        headers = {}
        response = self.client.post(self.url, data=data, headers=headers, **extra)
        return response

    def read_nominations(self, extra=None):
        extra = extra or {}
        headers = {}
        return self.client.get(self.url, headers=headers, **extra)

    def test_unauthenticated_access_is_denied(self):
        response = self.submit_nominations({})
        assert response.status_code == 302

    def test_unauthenticated_read_is_denied(self):
        response = self.read_nominations()
        assert response.status_code == 302

    def test_staff_access_is_denied_without_permission(self):
        self.client.force_login(self.staff.user)
        response = self.submit_nominations({})
        assert response.status_code == 403

    def test_staff_read_is_denied(self):
        self.client.force_login(self.staff.user)
        response = self.read_nominations()
        assert response.status_code == 403

    def test_affected_member_access_is_denied(self):
        self.client.force_login(self.member.user)
        response = self.submit_nominations({})
        assert response.status_code == 403

    def test_affected_member_read_is_denied(self):
        self.client.force_login(self.member.user)
        response = self.read_nominations()
        assert response.status_code == 403

    def enable_staff_access(self):
        self.staff.user.user_permissions.add(
            Permission.objects.get(
                codename="edit_ballot", content_type__app_label="nominate"
            )
        )
        self.client.force_login(self.staff.user)

    def test_saves_nomination_for_profile(self):
        valid_data = {
            f"{self.c1.id}-0-field_1": "t1",
            f"{self.c1.id}-0-field_2": "a1",
        }

        self.enable_staff_access()

        self.submit_nominations(valid_data)
        assert models.Nomination.objects.count() == 1
        assert self.member.nomination_set.count() == 1

    def test_does_not_affect_logged_in_user_nominations(self):
        factories.NominationFactory.create_batch(
            2,
            category=self.c1,
            nominator=self.staff,
        )
        valid_data = {
            f"{self.c1.id}-0-field_1": "t1",
            f"{self.c1.id}-0-field_2": "a1",
        }

        self.enable_staff_access()
        self.submit_nominations(valid_data)
        assert self.staff.nomination_set.count() == 2

    def test_saving_sends_notification_to_member_if_they_have_an_email(self):
        valid_data = {
            f"{self.c1.id}-0-field_1": "t1",
            f"{self.c1.id}-0-field_2": "a1",
        }

        self.enable_staff_access()
        with self.captureOnCommitCallbacks(execute=True):
            self.submit_nominations(valid_data)
        assert len(mail.outbox) == 1
        assert mail.outbox[0].to == [self.member.user.email]

    def test_saving_sends_no_notification_if_email_unset(self):
        valid_data = {
            f"{self.c1.id}-0-field_1": "t1",
            f"{self.c1.id}-0-field_2": "a1",
        }
        self.member.user.email = ""
        self.member.user.save()

        self.enable_staff_access()
        with self.captureOnCommitCallbacks(execute=True):
            self.submit_nominations(valid_data)
        assert len(mail.outbox) == 0


class TestNominationViewOnCommit(TestCase):
    """Exercise the post-commit side effects of submitting a ballot.

    The existing invariant suites never run the ``transaction.on_commit``
    callback (they don't wrap submission in ``captureOnCommitCallbacks``), so the
    work scheduled there - linking nominations to works and running the
    post-save hook - is entirely untested. These tests post to the member-facing
    nominate view, execute the on-commit callbacks, and assert the observable
    behaviour without reaching into the view's internals.
    """

    def setup_method(self, test_method):
        self.election = factories.ElectionFactory.create(state="nominating")
        self.member = factories.NominatingMemberProfileFactory.create()
        self.user = self.member.user
        self.user.user_permissions.add(
            Permission.objects.get(
                codename="nominate", content_type__app_label="nominate"
            )
        )
        self.c1 = factories.CategoryFactory.create(
            election=self.election,
            fields=2,
            ballot_position=1,
        )

    def view_url(self):
        return reverse("election:nominate", kwargs={"election_id": self.election.slug})

    def valid_data(self):
        return {
            f"{self.c1.id}-0-field_1": "t1",
            f"{self.c1.id}-0-field_2": "a1",
        }

    def test_submitting_triggers_link_nominations_to_works_task(self):
        self.client.force_login(self.user)
        with mock.patch(
            "nomnom.nominate.tasks.link_nominations_to_works.delay"
        ) as delay:
            with self.captureOnCommitCallbacks(execute=True):
                response = self.client.post(self.view_url(), data=self.valid_data())

        assert response.status_code == 302
        assert delay.called

    def test_submitting_runs_post_save_hook(self):
        self.client.force_login(self.user)
        with self.captureOnCommitCallbacks(execute=True):
            response = self.client.post(self.view_url(), data=self.valid_data())

        messages = [str(m) for m in get_messages(response.wsgi_request)]
        assert any("Your set of nominations was saved" in m for m in messages)


class TestNominationViewClosed(TestCase):
    """When a member with nominating rights POSTs to an election whose
    nominations have closed, the view rejects the submission with an error
    message and saves nothing.
    """

    def setup_method(self, test_method):
        self.election = factories.ElectionFactory.create(state="nominating_closed")
        self.member = factories.NominatingMemberProfileFactory.create()
        self.user = self.member.user
        self.user.user_permissions.add(
            Permission.objects.get(
                codename="nominate", content_type__app_label="nominate"
            )
        )
        self.c1 = factories.CategoryFactory.create(
            election=self.election,
            fields=2,
            ballot_position=1,
        )

    def view_url(self):
        return reverse("election:nominate", kwargs={"election_id": self.election.slug})

    def test_posting_to_closed_election_reports_closed(self):
        self.client.force_login(self.user)
        response = self.client.post(
            self.view_url(),
            data={
                f"{self.c1.id}-0-field_1": "t1",
                f"{self.c1.id}-0-field_2": "a1",
            },
        )

        assert response.status_code == 302
        messages = [str(m) for m in get_messages(response.wsgi_request)]
        assert any("Nominations have closed" in m for m in messages)
        assert models.Nomination.objects.count() == 0


class TestAdminNominationViewGet(TestCase):
    """The admin edit view renders the admin template on GET, even though the
    logged-in staff actor has no nominating rights of their own.
    """

    def setup_method(self, test_method):
        self.election = factories.ElectionFactory.create(state="nominating")
        self.member = factories.NominatingMemberProfileFactory.create()

        staff_user = factories.UserFactory.create(is_staff=True)
        self.staff = factories.NominatingMemberProfileFactory.create(user=staff_user)
        self.user = self.staff.user
        self.user.user_permissions.add(
            Permission.objects.get(
                codename="edit_ballot", content_type__app_label="nominate"
            )
        )
        self.c1 = factories.CategoryFactory.create(
            election=self.election,
            fields=2,
            ballot_position=1,
        )

    def view_url(self):
        return reverse(
            "election:edit_nominations",
            kwargs={"election_id": self.election.slug, "member_id": self.member.id},
        )

    def test_get_renders_admin_template(self):
        self.client.force_login(self.user)
        response = self.client.get(self.view_url())

        assert response.status_code == 200
        self.assertTemplateUsed(response, "nominate/admin_nominate.html")


def field_data(category, field_index, *field_values):
    return {
        f"{category.id}-{field_index}-field_{i + 1}": v
        for i, v in enumerate(field_values)
    }
