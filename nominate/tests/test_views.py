from unittest.mock import Mock

import pytest
from django.contrib.auth.models import AnonymousUser, Permission
from django.test import RequestFactory, TestCase
from django.urls import reverse
from nominate import factories, models
from nominate.views import (
    ClosedElectionView,
    ElectionModeView,
    ElectionView,
    NominationView,
    VoteView,
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
        self.election = factories.ElectionFactory.create()

    def test_get(self):
        request = self.request_factory.get("/")
        request.user = AnonymousUser()
        response = ClosedElectionView.as_view()(request, election_id=self.election.slug)
        assert response.status_code == 200
        assert response.template_name[0].endswith("_closed.html")


class NominationViewSubmitMixin:
    def submit_nominations(self, data, extra=None):
        extra = extra or {}
        headers = {}
        url = reverse("election:nominate", kwargs={"election_id": self.election.slug})
        self.client.force_login(self.user)
        response = self.client.post(url, data=data, headers=headers, **extra)
        return response


class NominationHTMXSubmitMixin:
    def submit_nominations(self, data, extra=None):
        extra = extra or {}
        headers = {"HX-Request": "true"}
        url = reverse("election:nominate", kwargs={"election_id": self.election.slug})
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
        response = NominationView.as_view()(request, election_id="dummy-election-id")
        assert response.status_code == 302
        assert response.url == f"{reverse('login')}?next=/"

    def test_get_form(self):
        request = self.request_factory.get("/")
        request.user = self.user
        response = NominationView.as_view()(request, election_id=self.election.slug)
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
    success_status_code = 302


class TestNominationViewHTMX(NominationViewInvariants, NominationHTMXSubmitMixin):
    __test__ = True
    success_status_code = 200


def field_data(category, field_index, *field_values):
    return {
        f"{category.id}-{field_index}-field_{i + 1}": v
        for i, v in enumerate(field_values)
    }


class TestVoteView(TestCase):
    def setup_method(self, test_method):
        self.request_factory = RequestFactory()

    def test_get_anonymous(self):
        request = self.request_factory.get("/")
        request.user = AnonymousUser()
        response = VoteView.as_view()(request, election_id="dummy-election-id")
        # we are redirecting because the user isn't logged in
        assert response.status_code == 302
        assert response.url == f"{reverse('login')}?next=/"
