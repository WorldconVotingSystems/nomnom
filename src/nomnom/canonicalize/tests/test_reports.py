import pytest
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission
from django.urls import reverse

from nomnom.canonicalize import models
from nomnom.canonicalize.admin import BallotReport
from nomnom.nominate import factories
from nomnom.nominate import models as nominate


@pytest.fixture(name="user")
def make_user(db):
    UserModel = get_user_model()
    user = UserModel.objects.create_user(
        username="testuser", password="password123", email="reports@example.com"
    )
    user.is_staff = True
    user.user_permissions.add(Permission.objects.get(codename="report"))
    user.user_permissions.add(Permission.objects.get(codename="view_raw_results"))
    user.save()
    return user


@pytest.fixture(name="nomination")
def make_nomination(db, user, category):
    nominator = nominate.NominatingMemberProfile.objects.create(
        user=user, preferred_name="Test User", member_number="123"
    )
    return factories.NominationFactory(nominator=nominator, category=category)


def test_report_is_empty_when_no_nominations(client, user, category):
    report = BallotReport(category)
    (header, *lines) = report.build_report()
    assert header.strip() == "nominator,work 1,work 2,work 3,work 4,work 5"
    assert lines == []


def test_report_is_empty_when_no_canonicalizations(client, user, category, nomination):
    report = BallotReport(category)
    (header, *lines) = report.build_report()
    assert header.strip() == "nominator,work 1,work 2,work 3,work 4,work 5"
    assert lines == []


def test_report_includes_canonicalized_nominations(client, user, category, nomination):
    # Canonicalize the nomination
    canonical_work = models.Work.objects.create(
        name="Canonical Work Name",
        category=nomination.category,
    )
    canonical_work.nominations.add(nomination)
    canonical_work.save()

    ic(models.CanonicalizedNomination.objects.all())

    report = BallotReport(category)
    (header, *lines) = report.build_report()
    assert header.strip() == "nominator,work 1,work 2,work 3,work 4,work 5"
    assert len(lines) == 1
    assert lines[0].startswith(
        f"{nomination.nominator.preferred_name},{canonical_work.name}"
    )


@pytest.fixture(name="canonicalized_ballot_report_url")
def make_canonicalized_ballot_report_url(category):
    return reverse("canonicalize:ballots", kwargs={"category_id": category.id})


def test_report_view_get_request_unauthenticated(
    client, canonicalized_ballot_report_url
):
    response = client.get(canonicalized_ballot_report_url)
    assert response.status_code == 302
    assert response.url.startswith("/admin/login/")  # Redirect to login


def test_report_view_get_request_without_permission_redirects_to_login(
    client, user, canonicalized_ballot_report_url
):
    client.force_login(user)
    user.user_permissions.clear()  # Remove all permissions
    response = client.get(canonicalized_ballot_report_url)
    assert response.status_code == 302
    assert response.url.startswith("/accounts/login/")  # Redirect to login


def test_report_view_get_request_with_permission(
    client, user, canonicalized_ballot_report_url
):
    client.force_login(user)
    response = client.get(canonicalized_ballot_report_url)
    assert response.status_code == 200  # OK
    assert "text/csv" in response["Content-Type"]
    assert "attachment" in response["Content-Disposition"]


def test_report_view_get_request_with_permission_contents(
    client, user, canonicalized_ballot_report_url, nomination
):
    # Canonicalize the nomination
    canonical_work = models.Work.objects.create(
        name="Canonical Work Name",
        category=nomination.category,
    )
    canonical_work.nominations.add(nomination)
    canonical_work.save()

    client.force_login(user)
    response = client.get(canonicalized_ballot_report_url)
    assert response.status_code == 200  # OK
    content = response.content.decode("utf-8")
    assert "nominator,work 1,work 2,work 3,work 4,work 5" in content
    assert f"{nomination.nominator.preferred_name},{canonical_work.name}" in content
