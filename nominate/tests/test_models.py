from nominate.models import Entry
import pytest


@pytest.mark.django_db
def test_entry_validation():
    Entry.objects.create()
