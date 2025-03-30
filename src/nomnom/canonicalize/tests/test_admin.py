import pytest
from django.core.exceptions import ValidationError

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

    form = GroupNominationsForm()
    form.__post_init__(modeladmin=None, request=None, queryset=Nomination.objects.all())

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

    form = GroupNominationsForm()
    form.__post_init__(modeladmin=None, request=None, queryset=Nomination.objects.all())

    assert form.fields["work"].initial == matching_work


def test_form_raises_error_for_multiple_elections(nomination_factory, category_factory):
    cat1 = category_factory()
    cat2 = category_factory()
    nomination_factory(category=cat1, field_1="One")
    nomination_factory(category=cat2, field_1="Two")

    form = GroupNominationsForm()
    with pytest.raises(ValidationError, match="must come from exactly one election"):
        form.__post_init__(
            modeladmin=None, request=None, queryset=Nomination.objects.all()
        )


def test_work_queryset_is_ordered_and_filtered(
    work_factory, nomination_factory, category_factory
):
    category = category_factory()
    nomination_factory(category=category, field_1="ABC")
    work_factory(name="Zebra", category=category)
    work_factory(name="Apple", category=category)

    form = GroupNominationsForm()
    form.__post_init__(modeladmin=None, request=None, queryset=Nomination.objects.all())
    qs = list(form.fields["work"].queryset)

    assert qs == sorted(qs, key=lambda w: w.name)
    assert all(w.category == category for w in qs)


def test_work_field_label_from_instance(work_factory, category_factory):
    category = category_factory(name="Best Graphic Story")
    work = work_factory(name="Saga", category=category)
    form = GroupNominationsForm()
    label_func = form.fields["work"].label_from_instance
    assert label_func(work) == f"{work.name} ({work.category})"


def test_form_raises_error_when_no_nominations_selected():
    form = GroupNominationsForm()

    empty_queryset = Nomination.objects.none()

    with pytest.raises(ValidationError, match="at least one nomination"):
        form.__post_init__(modeladmin=None, request=None, queryset=empty_queryset)
