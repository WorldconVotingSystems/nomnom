from nominate.models import Nomination
import pytest


@pytest.mark.django_db
def test_nomination_validation():
    Nomination.objects.create()
