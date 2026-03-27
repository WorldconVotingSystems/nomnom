import pytest
from django.core.exceptions import ValidationError
from django.test.client import RequestFactory

from nomnom.canonicalize.admin import GroupNominationsForm
from nomnom.canonicalize.factories import WorkFactory
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


def test_form_filters_queryset_to_category(
    work_factory, nomination_factory, category_factory
):
    category = category_factory()
    work_factory(category=category)
    nomination_factory(category=category, field_1="Example")
    request = RequestFactory().get("/admin/canonicalize/canonicalizednomination/")

    form = GroupNominationsForm(
        modeladmin=None,
        action="group_works",
        request=request,
        queryset=Nomination.objects.all(),
    )

    assert all(w.category == category for w in form.fields["work"].queryset)


def test_form_sets_initial_if_matching_work_exists(
    work_factory, nomination_factory, category_factory
):
    category = category_factory()
    nomination = nomination_factory(category=category, field_1="Example")
    matching_work = work_factory(
        category=category, name=nomination.proposed_work_name()
    )
    matching_work.nominations.add(nomination)
    request = RequestFactory().get("/admin/canonicalize/canonicalizednomination/")
    queryset = Nomination.objects.all()

    form = GroupNominationsForm(
        modeladmin=None, action="group_works", request=request, queryset=queryset
    )

    assert form.fields["work"].initial == matching_work


def test_form_raises_error_for_multiple_elections(nomination_factory, category_factory):
    cat1 = category_factory()
    cat2 = category_factory()
    nomination_factory(category=cat1, field_1="One")
    nomination_factory(category=cat2, field_1="Two")
    request = RequestFactory().get("/admin/canonicalize/canonicalizednomination/")
    queryset = Nomination.objects.all()

    with pytest.raises(ValidationError, match="must come from exactly one election"):
        GroupNominationsForm(
            modeladmin=None, action="group_works", request=request, queryset=queryset
        )


def test_work_queryset_is_ordered_and_filtered(
    work_factory, nomination_factory, category_factory
):
    category = category_factory()
    nomination_factory(category=category, field_1="ABC")
    work_factory(name="Zebra", category=category)
    work_factory(name="Apple", category=category)
    request = RequestFactory().get("/admin/canonicalize/canonicalizednomination/")
    queryset = Nomination.objects.all()

    form = GroupNominationsForm(
        modeladmin=None, action="group_works", request=request, queryset=queryset
    )
    qs = list(form.fields["work"].queryset)

    assert qs == sorted(qs, key=lambda w: w.name)
    assert all(w.category == category for w in qs)


def test_work_field_label_from_instance(
    work_factory, nomination_factory, category_factory
):
    category = category_factory(name="Best Graphic Story")
    nomination_factory(category=category, field_1="Example")
    work = work_factory(name="Saga", category=category)
    request = RequestFactory().get("/admin/canonicalize/canonicalizednomination/")
    form = GroupNominationsForm(
        modeladmin=None,
        action="group_works",
        request=request,
        queryset=Nomination.objects.all(),
    )
    label_func = form.fields["work"].label_from_instance
    assert label_func(work) == f"{work.name} ({work.category})"


def test_form_raises_error_when_no_nominations_selected():
    empty_queryset = Nomination.objects.none()
    request = RequestFactory().get("/admin/canonicalize/canonicalizednomination/")
    with pytest.raises(ValidationError, match="at least one nomination"):
        GroupNominationsForm(
            modeladmin=None,
            action="group_works",
            request=request,
            queryset=empty_queryset,
        )


def test_closest_work_when_mode_matches_exactly(
    work_factory, nomination_factory, category_factory
):
    """When the most common proposed_work_name has an exact work name match,
    the form selects that work as initial (via the closest-alphabetical fallback)."""
    category = category_factory()
    # Three nominations with the same name, no work has them linked
    nomination_factory(category=category, field_1="Dune")
    nomination_factory(category=category, field_1="Dune")
    nomination_factory(category=category, field_1="Neuromancer")
    # Works exist but none has nominations linked (so exact-match via
    # find_match_based_on_identical_nomination won't fire)
    work_factory(name="Babel", category=category)
    target_work = work_factory(name="Dune", category=category)
    work_factory(name="Foundation", category=category)
    request = RequestFactory().get("/admin/canonicalize/canonicalizednomination/")

    form = GroupNominationsForm(
        modeladmin=None,
        action="group_works",
        request=request,
        queryset=Nomination.objects.all(),
    )

    assert form.fields["work"].initial == target_work


def test_closest_work_when_mode_is_close_alphabetically(
    work_factory, nomination_factory, category_factory
):
    """When the most common proposed_work_name doesn't exactly match any work,
    the form selects the alphabetically nearest work."""
    category = category_factory()
    # Most common name is "Dungeon" — no work with that exact name
    nomination_factory(category=category, field_1="Dungeon")
    nomination_factory(category=category, field_1="Dungeon")
    nomination_factory(category=category, field_1="Zebra")
    # Works: "Babel", "Dune", "Foundation" — "Dune" is the closest alphabetically
    # to "Dungeon" (it sorts before "Dungeon"; "Foundation" sorts after)
    work_factory(name="Babel", category=category)
    work_factory(name="Dune", category=category)
    expected_work = work_factory(name="Foundation", category=category)
    request = RequestFactory().get("/admin/canonicalize/canonicalizednomination/")

    form = GroupNominationsForm(
        modeladmin=None,
        action="group_works",
        request=request,
        queryset=Nomination.objects.all(),
    )

    # "Dungeon" sorts between "Dune" and "Foundation"; bisect picks the one after
    assert form.fields["work"].initial == expected_work


def test_closest_work_when_no_mode_uses_first_nomination(
    work_factory, nomination_factory, category_factory
):
    """When all proposed_work_names are different (no mode), the form uses the
    first nomination's name to find the closest work."""
    category = category_factory()
    # All different names — no mode. First nomination is "Babel" (ordered by field_1
    # via the queryset's default ordering)
    nomination_factory(category=category, field_1="Babel")
    nomination_factory(category=category, field_1="Dune")
    nomination_factory(category=category, field_1="Foundation")
    # Works that don't match any nomination exactly
    work_factory(name="Axiom", category=category)
    expected_work = work_factory(name="Babel-17", category=category)
    work_factory(name="Cryptonomicon", category=category)
    request = RequestFactory().get("/admin/canonicalize/canonicalizednomination/")

    form = GroupNominationsForm(
        modeladmin=None,
        action="group_works",
        request=request,
        queryset=Nomination.objects.all(),
    )

    # "Babel" is the first nomination's name; "Babel-17" is the closest work
    assert form.fields["work"].initial == expected_work
