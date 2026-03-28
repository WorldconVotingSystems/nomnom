import csv
import io
import random

import pytest
from django.contrib import admin
from django.core.exceptions import ValidationError
from django.test.client import RequestFactory
from django.urls import reverse
from waffle.testutils import override_switch

from nomnom.canonicalize import feature_switches
from nomnom.canonicalize.admin import (
    GroupNominationsForm,
    NominationGroupingView,
    build_eph_csv,
)
from nomnom.canonicalize.factories import WorkFactory
from nomnom.canonicalize.models import CanonicalizedNomination
from nomnom.nominate.factories import (
    CategoryFactory,
    NominatingMemberProfileFactory,
    NominationFactory,
)
from nomnom.nominate.models import Nomination

pytestmark = pytest.mark.usefixtures("db")


@pytest.fixture(name="work_factory")
def make_work():
    return WorkFactory


@pytest.fixture(name="nomination_factory")
def make_nomination():
    return NominationFactory


@pytest.fixture(name="category_factory")
def make_category():
    return CategoryFactory


@pytest.fixture(name="modeladmin")
def make_modeladmin():
    return NominationGroupingView(CanonicalizedNomination, admin.site)


def test_matching_works_only_includes_works_from_same_category(
    work_factory, nomination_factory, category_factory, modeladmin
):
    category = category_factory()
    other_category = category_factory()
    work_factory(name="Example", category=category)
    work_factory(name="Example", category=other_category)
    nomination_factory(category=category, field_1="Example")
    request = RequestFactory().get("/admin/canonicalize/canonicalizednomination/")

    form = GroupNominationsForm(
        modeladmin=modeladmin,
        action="group_works",
        request=request,
        queryset=Nomination.objects.all(),
    )

    assert all(w.category == category for w in form.matching_works)


def test_matching_works_finds_similar_work(
    work_factory, nomination_factory, category_factory, modeladmin
):
    category = category_factory()
    nomination = nomination_factory(category=category, field_1="Example")
    matching_work = work_factory(
        category=category, name=nomination.proposed_work_name()
    )
    request = RequestFactory().get("/admin/canonicalize/canonicalizednomination/")
    queryset = Nomination.objects.all()

    form = GroupNominationsForm(
        modeladmin=modeladmin, action="group_works", request=request, queryset=queryset
    )

    assert matching_work in form.matching_works


def test_form_raises_error_for_multiple_elections(
    nomination_factory, category_factory, modeladmin
):
    cat1 = category_factory()
    cat2 = category_factory()
    nomination_factory(category=cat1, field_1="One")
    nomination_factory(category=cat2, field_1="Two")
    request = RequestFactory().get("/admin/canonicalize/canonicalizednomination/")
    queryset = Nomination.objects.all()

    with pytest.raises(ValidationError, match="must come from exactly one election"):
        GroupNominationsForm(
            modeladmin=modeladmin,
            action="group_works",
            request=request,
            queryset=queryset,
        )


def test_matching_works_ordered_by_similarity(
    work_factory, nomination_factory, category_factory, modeladmin
):
    category = category_factory()
    nomination_factory(category=category, field_1="The Hobbit")
    fuzzy = work_factory(name="The Hobbits Journey", category=category)
    exact = work_factory(name="The Hobbit", category=category)
    request = RequestFactory().get("/admin/canonicalize/canonicalizednomination/")
    queryset = Nomination.objects.all()

    form = GroupNominationsForm(
        modeladmin=modeladmin, action="group_works", request=request, queryset=queryset
    )

    assert form.matching_works[0] == exact
    assert fuzzy in form.matching_works


def test_matching_works_have_similarity_pct(
    work_factory, nomination_factory, category_factory, modeladmin
):
    category = category_factory()
    nomination_factory(category=category, field_1="Example")
    work_factory(name="Example", category=category)
    request = RequestFactory().get("/admin/canonicalize/canonicalizednomination/")
    form = GroupNominationsForm(
        modeladmin=modeladmin,
        action="group_works",
        request=request,
        queryset=Nomination.objects.all(),
    )

    assert len(form.matching_works) > 0
    assert all(hasattr(w, "similarity_pct") for w in form.matching_works)


def test_form_raises_error_when_no_nominations_selected(modeladmin):
    empty_queryset = Nomination.objects.none()
    request = RequestFactory().get("/admin/canonicalize/canonicalizednomination/")
    with pytest.raises(ValidationError, match="at least one nomination"):
        GroupNominationsForm(
            modeladmin=modeladmin,
            action="group_works",
            request=request,
            queryset=empty_queryset,
        )


def test_matching_works_ranks_exact_name_match_highest(
    work_factory, nomination_factory, category_factory, modeladmin
):
    """When multiple nominations share a name that exactly matches a work,
    that work should rank highest in matching_works."""
    category = category_factory()
    nomination_factory(category=category, field_1="Dune")
    nomination_factory(category=category, field_1="Dune")
    nomination_factory(category=category, field_1="Neuromancer")
    work_factory(name="Babel", category=category)
    target_work = work_factory(name="Dune", category=category)
    work_factory(name="Foundation", category=category)
    request = RequestFactory().get("/admin/canonicalize/canonicalizednomination/")

    form = GroupNominationsForm(
        modeladmin=modeladmin,
        action="group_works",
        request=request,
        queryset=Nomination.objects.all(),
    )

    assert target_work in form.matching_works
    assert form.matching_works[0] == target_work


def test_matching_works_uses_average_similarity_across_nominations(
    work_factory, nomination_factory, category_factory, modeladmin
):
    """A work that matches most nominations should rank higher than one
    matching only a single nomination."""
    category = category_factory()
    nomination_factory(category=category, field_1="Dune")
    nomination_factory(category=category, field_1="Dune")
    nomination_factory(category=category, field_1="Dune")
    # "Dune" matches all 3, "Neuromancer" matches none
    dune_work = work_factory(name="Dune", category=category)
    work_factory(name="Neuromancer", category=category)
    request = RequestFactory().get("/admin/canonicalize/canonicalizednomination/")

    form = GroupNominationsForm(
        modeladmin=modeladmin,
        action="group_works",
        request=request,
        queryset=Nomination.objects.all(),
    )

    assert form.matching_works[0] == dune_work


@pytest.mark.django_db
class TestFinalistsCsv:
    """Test the EPH elimination CSV report includes Final Score and Number of Ballots columns."""

    @pytest.fixture(autouse=True)
    def enable_switch(self):
        with override_switch(feature_switches.SWITCH_FINALIST_CSV_TABLE, active=True):
            yield

    @pytest.fixture
    def staff_client(self, admin_client):
        return admin_client

    @pytest.fixture
    def eph_category(self, election):
        """A category with 8 works and enough ballots to drive EPH elimination."""
        category = CategoryFactory.create(
            election=election, fields=1, ballot_position=1
        )
        works = [WorkFactory(category=category, name=f"Work {i}") for i in range(8)]

        # Create 15 nominators, each nominating 5 random works.
        # The post_save signal auto-links nominations to works when field_1 matches.
        rng = random.Random(42)
        for _ in range(15):
            nominator = NominatingMemberProfileFactory()
            for work in rng.sample(works, 5):
                NominationFactory(
                    category=category,
                    nominator=nominator,
                    field_1=work.name,
                )

        return category

    def test_csv_has_final_score_and_ballot_columns(self, staff_client, eph_category):
        url = reverse("canonicalize:finalist_report", args=[eph_category.pk])
        response = staff_client.get(url)

        assert response.status_code == 200
        assert response["Content-Type"] == "text/csv"

        content = response.content.decode("utf-8")
        reader = csv.reader(io.StringIO(content))
        rows = list(reader)

        header = rows[0]
        assert header[0] == "Candidate"
        assert header[1] == "Final Score"
        assert header[2] == "Number of Ballots"
        assert header[-1] == "Finalists"

        # Every data row should have a non-empty Final Score and Number of Ballots
        for row in rows[1:]:
            assert row[0], "Candidate name should not be blank"
            assert row[1].isdigit(), f"Final Score should be numeric, got {row[1]!r}"
            assert row[2].isdigit(), (
                f"Number of Ballots should be numeric, got {row[2]!r}"
            )
            assert int(row[2]) > 0, "Every candidate must appear on at least one ballot"

    def test_csv_values_with_elimination_rounds(self):
        """Hand-verified EPH scenario with elimination rounds.

        4 works, finalist_count=2, so two rounds of elimination occur.

        Ballots:
          Ballot 1: {A, B, C}  — 3 works → 20 pts each
          Ballot 2: {A, B, C}  — 3 works → 20 pts each
          Ballot 3: {A, B, D}  — 3 works → 20 pts each
          Ballot 4: {A}        — 1 work  → 60 pts

        Round 1 (4 candidates):
          A=120 (4 ballots), B=60 (3), C=40 (2), D=20 (1)
          → D eliminated (fewest points & nominations)

        Round 2 (3 candidates, D removed; ballot 3 becomes {A,B}):
          A=130, B=70, C=40
          → C eliminated

        Finalists round (2 candidates, C removed; ballots 1-3 become {A,B}):
          A=150, B=90
        """
        ballots = [
            ["A", "B", "C"],
            ["A", "B", "C"],
            ["A", "B", "D"],
            ["A"],
        ]

        csv_content = build_eph_csv(ballots, finalist_count=2)
        reader = csv.reader(io.StringIO(csv_content))
        rows = list(reader)

        header = rows[0]
        assert header == [
            "Candidate",
            "Final Score",
            "Number of Ballots",
            "Round 1",
            "Round 2",
            "Finalists",
        ]

        data = {row[0]: row[1:] for row in rows[1:]}
        assert len(data) == 4

        # Finalists (survived to last round) listed first, then by elimination order.
        # [Final Score, Number of Ballots, Round 1, Round 2, Finalists]
        assert data["A"] == ["150", "4", "120", "130", "150"]
        assert data["B"] == ["90", "3", "60", "70", "90"]
        # C eliminated after round 2 — no Finalists column value
        assert data["C"] == ["40", "2", "40", "40"]
        # D eliminated after round 1 — no Round 2 or Finalists
        assert data["D"] == ["20", "1", "20"]
