import csv
from io import StringIO
from urllib.parse import parse_qs, urlparse

import pytest
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission
from django.urls import reverse
from freezegun import freeze_time
from nomnom.nominate import factories, models, reports

pytestmark = pytest.mark.usefixtures("db")


@pytest.fixture(name="user")
def make_user(db):
    UserModel = get_user_model()
    user = UserModel.objects.create_user(username="testuser", password="password123")
    user.is_staff = True
    perm = Permission.objects.get(codename="report")
    user.user_permissions.add(perm)
    user.save()
    return user


@pytest.fixture(name="election")
def make_election(db):
    return models.Election.objects.create(slug="election_slug")


@pytest.fixture(name="nominations_report")
def make_nominations_report(election):
    return reports.NominationsReport(election=election)


def test_report_is_empty_when_election_is_empty(
    nominations_report: reports.NominationsReport,
):
    assert (
        nominations_report.get_report_content()
        == nominations_report.get_report_header()
    )


@freeze_time("2022-09-01")
def test_report_filename_contains_data(nominations_report: reports.NominationsReport):
    assert "2022-09-01" in nominations_report.get_filename()


def test_report_filename_includes_election_slug(
    election: models.Election, nominations_report: reports.NominationsReport
):
    assert election.slug in nominations_report.get_filename()


def test_report_filename_extension(nominations_report: reports.NominationsReport):
    assert nominations_report.get_filename().endswith(".csv")


def test_report_contains_nomination(
    nominations_report: reports.NominationsReport,
    nomination: models.Nomination,
):
    reader = csv.DictReader(nominations_report.get_report_content().splitlines())
    row = list(reader)[0]
    assert row["id"] == str(nomination.id)
    assert row["field_1"] == nomination.field_1


def test_report_doesnt_contain_nomination_from_other_election(
    nominations_report: reports.NominationsReport,
):
    factories.NominationFactory.create()

    assert (
        nominations_report.get_report_content()
        == nominations_report.get_report_header()
    )


@pytest.fixture(name="category")
def make_category(db, election):
    cat = models.Category.objects.create(
        election=election,
        name="testcategory",
        description="testcategory description",
        ballot_position=1,
        field_1_description="F1",
    )
    cat.save()
    return cat


@pytest.fixture(name="nomination")
def make_nomination(db, user, category):
    nominator = models.NominatingMemberProfile.objects.create(
        user=user, preferred_name="Test User", member_number="123"
    )
    return factories.NominationFactory(nominator=nominator, category=category)


@pytest.fixture(name="report_url")
def make_report_url():
    return reverse(
        "election:nomination-report", kwargs={"election_id": "election_slug"}
    )


def test_nomination_view_dispatch(client, report_url, user, nomination):
    client.force_login(user)
    response = client.get(report_url, HTTP_ACCEPT="text/csv")
    assert response.status_code == 200
    assert response["Content-Type"] == "text/csv"


def test_nomination_view_unknown_election_returns_404(client, user):
    client.force_login(user)
    url = reverse(
        "election:nomination-report", kwargs={"election_id": "does-not-exist"}
    )
    response = client.get(url, HTTP_ACCEPT="text/csv")
    assert response.status_code == 404


def test_nomination_report_query_set(nominations_report, nomination):
    queryset = list(nominations_report.query_set())
    assert queryset == [nomination]


def test_nomination_view_dispatch_unauthenticated(client, report_url):
    response = client.get(report_url, HTTP_ACCEPT="text/csv")
    assert response.status_code == 302
    parts = urlparse(response.url)
    query = parse_qs(parts.query)
    assert query["next"][0] == report_url


def test_nomination_view_get_unauthenticated(client, report_url):
    response = client.get(report_url, HTTP_ACCEPT="text/csv")
    assert response.status_code == 302
    parts = urlparse(response.url)
    query = parse_qs(parts.query)
    assert query["next"][0] == report_url


def test_nomination_view_get(client, report_url, user, nomination):
    client.force_login(user)
    response = client.get(report_url, HTTP_ACCEPT="text/csv")

    assert response.status_code == 200

    content = StringIO(response.content.decode())
    reader = csv.reader(content)

    header = next(reader)
    expected_header = [
        field.name for field in models.Nomination._meta.fields
    ] + reports.NominationsReport.extra_fields
    assert header == expected_header

    content = StringIO(response.content.decode())
    reader = csv.DictReader(content)

    data_row = next(reader)

    assert sorted(data_row.keys()) == sorted(header)

    with pytest.raises(StopIteration):  # No more data
        next(reader)
