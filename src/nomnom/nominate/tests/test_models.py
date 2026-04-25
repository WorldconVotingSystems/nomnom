import pytest
from django.contrib.auth.models import AnonymousUser, Group, Permission
from django_svcs.apps import svcs_from

from nomnom.convention import ConventionConfiguration
from nomnom.nominate.factories import (
    CategoryFactory,
    ElectionFactory,
    NominatingMemberProfileFactory,
    NominationFactory,
)
from nomnom.nominate.models import Election, Nomination

pytestmark = pytest.mark.usefixtures("db")


@pytest.fixture(name="nominating_group")
def make_nominating_group(db):
    convention_configuration = svcs_from().get(ConventionConfiguration)
    return Group.objects.get_or_create(name=convention_configuration.nominating_group)[
        0
    ]


@pytest.fixture(name="voting_group")
def make_voting_group(db):
    convention_configuration = svcs_from().get(ConventionConfiguration)
    return Group.objects.get_or_create(name=convention_configuration.voting_group)[0]


@pytest.fixture(name="nominator")
def make_nominator(nominating_group):
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
        assert self.election.pretty_state(self.user) == "Not yet open"

    def test_description_for_anonymous_user(self):
        assert self.election.describe_state(self.user) == "You must log in to nominate"

    def test_pretty_state_for_preview_user(self):
        assert self.election.pretty_state(self.user) == "Not yet open"

    def test_description_for_preview_user(self):
        assert self.election.describe_state(self.user) == "Nominations are not yet open"

    def test_pretty_state_for_general_user(self):
        assert self.election.pretty_state(self.user) == "Not yet open"

    def test_description_for_general_user(self):
        assert self.election.describe_state(self.user) == "Nominations are not yet open"


@pytest.mark.django_db
class TestPreviewingNominationElection(MemberMixin):
    def setup_method(self, test_method):
        self.election = ElectionFactory.create(state=Election.STATE.NOMINATION_PREVIEW)
        super().setup_method(test_method)

    def test_is_open(self):
        assert self.election.is_open, (
            f"Election in state {self.election.state} should be open"
        )

    def test_pretty_state_for_anonymous_user(self):
        assert self.election.pretty_state(self.user) == "Nomination Preview"

    def test_description_for_anonymous_user(self):
        assert self.election.describe_state(self.user) == "You must log in to nominate"

    def test_pretty_state_for_preview_user(self):
        assert self.election.pretty_state(self.user) == "Open"

    def test_description_for_preview_user(self):
        assert self.election.describe_state(self.user) == "Nominations are previewing"

    def test_pretty_state_for_general_user(self):
        assert self.election.pretty_state(self.user) == "Nomination Preview"

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


@pytest.fixture(name="set_of_nominations")
def make_set_of_nominations(election, nominator):
    c1 = CategoryFactory.create(
        election=election,
        fields=2,
        ballot_position=1,
    )
    other_member = NominatingMemberProfileFactory.create()
    NominationFactory.create_batch(
        2,
        category=c1,
        nominator=other_member,
    )
    NominationFactory.create_batch(
        2,
        category=c1,
        nominator=nominator,
    )


class TestFieldsForCanonicalization:
    """Test Nomination.fields_for_canonicalization with various flag permutations."""

    @pytest.mark.parametrize(
        "fields, f2_canon, f3_canon, expected_fields",
        [
            # 1-field category: only field_1, flags irrelevant
            (1, False, False, ["A"]),
            (1, True, False, ["A"]),
            (1, True, True, ["A"]),
            # 2-field category
            (2, False, False, ["A"]),
            (2, True, False, ["A", "B"]),
            # 3-field category
            (3, False, False, ["A"]),
            (3, True, False, ["A", "B"]),
            (3, False, True, ["A", "C"]),
            (3, True, True, ["A", "B", "C"]),
        ],
        ids=[
            "1field-none",
            "1field-f2on",
            "1field-both",
            "2field-none",
            "2field-f2on",
            "3field-none",
            "3field-f2on",
            "3field-f3on",
            "3field-both",
        ],
    )
    def test_fields_for_canonicalization(
        self, db, fields, f2_canon, f3_canon, expected_fields
    ):
        cat = CategoryFactory.create(
            fields=fields,
            field_2_used_for_canonicalization=f2_canon,
            field_3_used_for_canonicalization=f3_canon,
        )
        nom = NominationFactory.create(
            category=cat, field_1="A", field_2="B", field_3="C"
        )
        assert nom.fields_for_canonicalization == expected_fields

    @pytest.mark.parametrize(
        "fields, f2_canon, f3_canon, expected_name",
        [
            (1, False, False, "Title"),
            (2, False, False, "Title"),
            (2, True, False, "Title Author"),
            (3, False, False, "Title"),
            (3, True, False, "Title Author"),
            (3, False, True, "Title Publisher"),
            (3, True, True, "Title Author Publisher"),
        ],
        ids=[
            "1field",
            "2field-f2off",
            "2field-f2on",
            "3field-none",
            "3field-f2on",
            "3field-f3on",
            "3field-both",
        ],
    )
    def test_proposed_work_name(self, db, fields, f2_canon, f3_canon, expected_name):
        cat = CategoryFactory.create(
            fields=fields,
            field_2_used_for_canonicalization=f2_canon,
            field_3_used_for_canonicalization=f3_canon,
        )
        nom = NominationFactory.create(
            category=cat, field_1="Title", field_2="Author", field_3="Publisher"
        )
        assert nom.proposed_work_name() == expected_name

    @pytest.mark.parametrize(
        "fields, f2_canon, f3_canon, expected_display",
        [
            (1, False, False, "Title"),
            (2, True, False, "Title | Author"),
            (3, True, True, "Title | Author | Publisher"),
            (3, False, True, "Title | Publisher"),
        ],
    )
    def test_canonicalization_display_name(
        self, db, fields, f2_canon, f3_canon, expected_display
    ):
        cat = CategoryFactory.create(
            fields=fields,
            field_2_used_for_canonicalization=f2_canon,
            field_3_used_for_canonicalization=f3_canon,
        )
        nom = NominationFactory.create(
            category=cat, field_1="Title", field_2="Author", field_3="Publisher"
        )
        assert nom.canonicalization_display_name() == expected_display


@pytest.mark.django_db
@pytest.mark.usefixtures("set_of_nominations")
def test_removing_nomination_permissions_via_user_invalidates_nominations(
    nominator, nominating_group
):
    nominator.user.groups.remove(nominating_group)
    nominator.save()

    # check our results
    assert Nomination.valid.filter(nominator=nominator).count() == 0
    assert Nomination.valid.count() == 2


@pytest.mark.django_db
@pytest.mark.usefixtures("set_of_nominations")
def test_removing_nomination_permissions_via_group_invalidates_nominations(
    nominator, nominating_group: Group
):
    nominating_group.user_set.remove(nominator.user)
    nominator.save()

    assert Nomination.valid.filter(nominator=nominator).count() == 0
    assert Nomination.valid.count() == 2
