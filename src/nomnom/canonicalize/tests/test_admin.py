import pytest
from django.contrib import admin
from django.core.exceptions import ValidationError
from django.test.client import RequestFactory

from nomnom.canonicalize.admin import GroupNominationsForm, NominationGroupingView
from nomnom.canonicalize.factories import WorkFactory
from nomnom.canonicalize.models import CanonicalizedNomination
from nomnom.nominate.factories import CategoryFactory, NominationFactory
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
