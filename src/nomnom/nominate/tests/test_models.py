import pytest
from django.contrib.auth.models import AnonymousUser, Permission
from nomnom.nominate.factories import (
    CategoryFactory,
    ElectionFactory,
    NominatingMemberProfileFactory,
)
from nomnom.nominate.models import Election, Nomination

pytestmark = pytest.mark.usefixtures("db")


@pytest.fixture(name="nominator")
def make_nominator():
    return NominatingMemberProfileFactory()


@pytest.fixture(name="category")
def make_category():
    return CategoryFactory(
        ballot_position=1,
        fields=1,
        field_1_description="Field 1",
    )


@pytest.fixture(name="election")
def make_election():
    return ElectionFactory()


def test_nomination_validation(category, nominator):
    Nomination(category=category, nominator=nominator).save()


@pytest.mark.django_db
class MemberMixin:
    def setup_method(self, test_method):
        test_name = test_method.__name__
        # use the name of the test to determine the type of user.
        if "anonymous_user" in test_name:
            self.nominator = None
            self.user = AnonymousUser()
            return

        self.nominator = nominator = NominatingMemberProfileFactory.create()
        self.user = user = nominator.user

        if "general_user" in test_name:
            perm = Permission.objects.get(codename="nominate")
            user.user_permissions.add(perm)
        elif "preview_user" in test_name:
            user.user_permissions.add(Permission.objects.get(codename="nominate"))
            user.user_permissions.add(
                Permission.objects.get(codename="preview_nominate")
            )


@pytest.mark.django_db
class TestPreNominationElection(MemberMixin):
    def setup_method(self, test_method):
        self.election = ElectionFactory.create(state=Election.STATE.PRE_NOMINATION)
        super().setup_method(test_method)

    def test_is_open(self):
        assert self.election.is_open is False

    def test_pretty_state_for_anonymous_user(self):
        assert self.election.pretty_state(self.user) == "Closed"

    def test_description_for_anonymous_user(self):
        assert self.election.describe_state(self.user) == "You must log in to nominate"

    def test_pretty_state_for_preview_user(self):
        assert self.election.pretty_state(self.user) == "Closed"

    def test_description_for_preview_user(self):
        assert self.election.describe_state(self.user) == "Nominations are not yet open"

    def test_pretty_state_for_general_user(self):
        assert self.election.pretty_state(self.user) == "Closed"

    def test_description_for_general_user(self):
        assert self.election.describe_state(self.user) == "Nominations are not yet open"


@pytest.mark.django_db
class TestPreviewingNominationElection(MemberMixin):
    def setup_method(self, test_method):
        self.election = ElectionFactory.create(state=Election.STATE.NOMINATION_PREVIEW)
        super().setup_method(test_method)

    def test_is_open(self):
        assert self.election.is_open is False

    def test_pretty_state_for_anonymous_user(self):
        assert self.election.pretty_state(self.user) == "Closed"

    def test_description_for_anonymous_user(self):
        assert self.election.describe_state(self.user) == "You must log in to nominate"

    def test_pretty_state_for_preview_user(self):
        assert self.election.pretty_state(self.user) == "Open"

    def test_description_for_preview_user(self):
        assert self.election.describe_state(self.user) == "Nominations are previewing"

    def test_pretty_state_for_general_user(self):
        assert self.election.pretty_state(self.user) == "Closed"

    def test_description_for_general_user(self):
        assert self.election.describe_state(self.user) == "Nominations are not yet open"


@pytest.mark.django_db
class TestNominatingElection(MemberMixin):
    def setup_method(self, test_method):
        self.election = ElectionFactory.create(state=Election.STATE.NOMINATIONS_OPEN)
        super().setup_method(test_method)

    def test_is_open(self):
        assert self.election.is_open is True

    def test_pretty_state_for_anonymous_user(self):
        assert self.election.pretty_state(self.user) == "Closed"

    def test_description_for_anonymous_user(self):
        assert self.election.describe_state(self.user) == "You must log in to nominate"

    def test_pretty_state_for_preview_user(self):
        assert self.election.pretty_state(self.user) == "Open"

    def test_description_for_preview_user(self):
        assert self.election.describe_state(self.user) == "Nominations are open"

    def test_pretty_state_for_general_user(self):
        assert self.election.pretty_state(self.user) == "Open"

    def test_description_for_general_user(self):
        assert self.election.describe_state(self.user) == "Nominations are open"
