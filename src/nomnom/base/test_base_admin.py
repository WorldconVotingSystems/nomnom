from unittest.mock import Mock

import pytest
from django.db import connection, models
from django.test.utils import isolate_apps

from nomnom.base.admin import PrefillSingleton


@pytest.fixture
def make_queryset():
    def _make(count=1, first_value=None):
        qs = Mock()
        qs.count.return_value = count
        qs.first.return_value = first_value
        return qs

    return _make


@pytest.fixture(name="admin")
def admin_with_tables(db):
    """Fixture that creates real DB tables for the fake models, for tests that exercise infer_queryset."""
    with isolate_apps("nomnom.base"):

        class FakeRelation(models.Model):
            class Meta:
                app_label = "nomnom_base"

        class FakeModel(models.Model):
            field_name = models.ForeignKey(on_delete=models.CASCADE, to=FakeRelation)

            class Meta:
                app_label = "nomnom_base"

        class FakeModelAdmin:
            model = FakeModel

            def get_changeform_initial_data(self, request):
                return {}

        class TestAdmin(PrefillSingleton, FakeModelAdmin):
            model = FakeModel

        with connection.schema_editor() as schema_editor:
            schema_editor.create_model(FakeRelation)
            schema_editor.create_model(FakeModel)

        try:
            yield TestAdmin(), FakeRelation
        finally:
            with connection.schema_editor() as schema_editor:
                schema_editor.delete_model(FakeModel)
                schema_editor.delete_model(FakeRelation)


def test_get_changeform_initial_data_with_3tuple(admin, make_queryset):
    admin_instance, _ = admin
    queryset = make_queryset(count=1, first_value="the one and only")

    admin_instance.get_singleton_initial_fields = lambda request: [
        ("field_name", queryset, queryset),
    ]

    initial_data = admin_instance.get_changeform_initial_data(request=None)

    assert initial_data["field_name"] == "the one and only"


def test_get_changeform_initial_data_with_2tuple(admin, make_queryset):
    queryset = make_queryset(count=1, first_value="the one and only")
    admin_instance, _ = admin

    admin_instance.get_singleton_initial_fields = lambda request: [
        ("field_name", queryset),
    ]

    initial_data = admin_instance.get_changeform_initial_data(request=None)

    assert initial_data["field_name"] == "the one and only"


def test_get_changeform_initial_data_with_name(admin):
    admin_instance, FakeRelation = admin
    FakeRelation.objects.create()

    admin_instance.get_singleton_initial_fields = lambda request: [
        "field_name",
    ]

    initial_data = admin_instance.get_changeform_initial_data(request=None)

    assert initial_data["field_name"] == FakeRelation.objects.first()
