from unittest.mock import Mock

import pytest
from django.contrib.auth.models import AnonymousUser
from django.test import RequestFactory, TestCase
from django.urls import reverse
from model_bakery import baker
from nominate.views import (
    ClosedElectionView,
    ElectionModeView,
    ElectionView,
    NominationView,
    VoteView,
    WelcomeView,
)

pytestmark = pytest.mark.usefixtures("db")


class TestWelcomeView(TestCase):
    def setup_method(self, test_method):
        self.election = baker.make("nominate.Election")
        self.member = baker.make("nominate.NominatingMemberProfile")
        self.user = self.member.user
        self.request_factory = RequestFactory()

    def test_get(self):
        request = self.request_factory.get("/")
        request.user = self.user
        response = WelcomeView.as_view()(request, election_id="dummy-election-id")
        assert response.status_code == 200


class TestElectionView(TestCase):
    def setup_method(self, test_method):
        self.request_factory = RequestFactory()
        self.member = baker.make("nominate.NominatingMemberProfile")
        self.user = self.member.user

    def test_get_queryset(self):
        request = self.request_factory.get("/")
        request.user = self.user
        response = ElectionView.as_view()(request)
        assert response.status_code == 200


class TestElectionModeView(TestCase):
    def setup_method(self, test_method):
        self.election = baker.make("nominate.Election")
        self.request_factory = RequestFactory()
        self.member = baker.make("nominate.NominatingMemberProfile")
        self.user = self.member.user

    def test_get_redirect_url_nominate(self):
        self.election.user_can_nominate = Mock(return_value=True)
        request = self.request_factory.get("/")
        request.user = self.user
        response = ElectionModeView.as_view()(request, election_id=self.election.slug)
        expected_url = reverse(
            "closed-election", kwargs={"election_id": self.election.slug}
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
            "closed-election", kwargs={"election_id": self.election.slug}
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
            "closed-election", kwargs={"election_id": self.election.slug}
        )
        assert response.status_code == 302
        assert response.url == expected_url


class TestClosedElectionView(TestCase):
    def setup_method(self, test_method):
        self.request_factory = RequestFactory()
        self.election = baker.make("nominate.Election")

    def test_get(self):
        request = self.request_factory.get("/")
        request.user = AnonymousUser()
        response = ClosedElectionView.as_view()(request, election_id=self.election.slug)
        assert response.status_code == 200
        assert response.template_name[0].endswith("_closed.html")


class TestNominationView(TestCase):
    def setup_method(self, test_method):
        self.request_factory = RequestFactory()

    def test_get_anonymous(self):
        request = self.request_factory.get("/")
        request.user = AnonymousUser()
        response = NominationView.as_view()(request, election_id="dummy-election-id")
        assert response.status_code == 302
        assert response.url == f"{reverse('login')}?next=/"


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
