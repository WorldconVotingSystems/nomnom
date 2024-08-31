import itertools
from collections.abc import Iterable
from unittest.mock import Mock

import pytest
from django.contrib.auth.models import AnonymousUser, Permission
from django.core import mail
from django.test import RequestFactory, TestCase
from django.urls import reverse

from nomnom.nominate import factories, models
from nomnom.nominate.views import (
    ElectionModeView,
    ElectionView,
    NominationView,
)

pytestmark = pytest.mark.usefixtures("db")


class TestElectionView(TestCase):
    def setup_method(self, test_method):
        self.request_factory = RequestFactory()
        self.member = factories.NominatingMemberProfileFactory.create()
        self.user = self.member.user

    def test_get_queryset(self):
        request = self.request_factory.get("/")
        request.user = self.user
        response = ElectionView.as_view()(request)
        assert response.status_code == 200


class TestElectionModeView(TestCase):
    def setup_method(self, test_method):
        self.election = factories.ElectionFactory.create()
        self.request_factory = RequestFactory()
        self.member = factories.NominatingMemberProfileFactory.create()
        self.user = self.member.user

    def test_get_redirect_url_nominate(self):
        self.election.user_can_nominate = Mock(return_value=True)
        request = self.request_factory.get("/")
        request.user = self.user
        response = ElectionModeView.as_view()(request, election_id=self.election.slug)
        expected_url = reverse(
            "election:closed", kwargs={"election_id": self.election.slug}
        )
        assert response.status_code == 302
        assert response.url == expected_url

    def test_get_redirect_url_vote(self):
        self.election.user_can_nominate = Mock(return_value=False)
        self.election.user_can_vote = Mock(return_value=True)
        request = self.request_factory.get("/")
        request.user = self.user
        response = ElectionModeView.as_view()(request, election_id=self.election.slug)
        expected_url = reverse(
            "election:closed", kwargs={"election_id": self.election.slug}
        )
        assert response.status_code == 302
        assert response.url == expected_url

    def test_get_redirect_url_closed(self):
        self.election.user_can_nominate = Mock(return_value=False)
        self.election.user_can_vote = Mock(return_value=False)
        request = self.request_factory.get("/")
        request.user = self.user
        response = ElectionModeView.as_view()(request, election_id=self.election.slug)
        expected_url = reverse(
            "election:closed", kwargs={"election_id": self.election.slug}
        )
        assert response.status_code == 302
        assert response.url == expected_url


class TestClosedElectionView(TestCase):
    def setup_method(self, test_method):
        self.request_factory = RequestFactory()
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
        self.request_factory = RequestFactory()
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
        self.c2 = factories.CategoryFactory.create(
            election=self.election,
            fields=2,
            ballot_position=2,
        )

    def test_get_anonymous(self):
        request = self.request_factory.get("/")
        request.user = AnonymousUser()
        response = self.view_class.as_view()(request, election_id="dummy-election-id")
        assert response.status_code == 302
        assert response.url == f"{reverse('login')}?next=/"

    def test_get_form(self):
        request = self.request_factory.get("/")
        request.user = self.user
        response = self.view_class.as_view()(request, election_id=self.election.slug)
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
            nominator=self.user.convention_profile,
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

        assert self.user.convention_profile.nomination_set.count() == 3
        assert self.user.convention_profile.nomination_set.first().field_1 == "title 1"
        assert self.user.convention_profile.nomination_set.last().field_1 == "title 3"


class TestNominationViewFull(NominationViewInvariants, NominationViewSubmitMixin):
    __test__ = True
    view_class = NominationView
    success_status_code = 302

    def view_url(self):
        return reverse("election:nominate", kwargs={"election_id": self.election.slug})


class TestNominationViewHTMX(NominationViewInvariants, NominationHTMXSubmitMixin):
    __test__ = True
    view_class = NominationView
    success_status_code = 200

    def view_url(self):
        return reverse("election:nominate", kwargs={"election_id": self.election.slug})


class TestAdminNominationView(TestCase):
    def setup_method(self, test_method):
        self.election = factories.ElectionFactory(state="nominating")
        self.request_factory = RequestFactory()
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


def field_data(category, field_index, *field_values):
    return {
        f"{category.id}-{field_index}-field_{i + 1}": v
        for i, v in enumerate(field_values)
    }
