import csv
from io import StringIO
from unittest import mock
from urllib.parse import parse_qs, urlparse

import pytest
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission
from django.contrib.messages.api import get_messages
from django.urls import reverse
from freezegun import freeze_time

from nomnom.nominate import factories, models, reports

pytestmark = pytest.mark.usefixtures("db")


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


@pytest.fixture(name="invalidated_nomination")
def make_nomination_with_invalidated(db, user, category):
    nominator = factories.NominatingMemberProfileFactory()
    nomination = factories.NominationFactory(nominator=nominator, category=category)
    nomination.save()
    models.NominationAdminData.objects.create(
        nomination=nomination,
        valid_nomination=False,
    ).save()
    return nomination


@pytest.fixture(name="nomination_report_url")
def make_nomination_report_url():
    return reverse(
        "election:nomination-report", kwargs={"election_id": "election_slug"}
    )


@pytest.fixture(name="invalid_nominations_report_url")
def make_invalid_nominations_report_url():
    return reverse(
        "election:invalidated-nomination-report",
        kwargs={"election_id": "election_slug"},
    )


def test_nomination_view_dispatch(client, nomination_report_url, user, nomination):
    client.force_login(user)
    response = client.get(nomination_report_url, HTTP_ACCEPT="text/csv")
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


def test_nomination_view_dispatch_unauthenticated(client, nomination_report_url):
    response = client.get(nomination_report_url, HTTP_ACCEPT="text/csv")
    assert response.status_code == 302
    parts = urlparse(response.url)
    query = parse_qs(parts.query)
    assert query["next"][0] == nomination_report_url


def test_nomination_view_get_unauthenticated(client, nomination_report_url):
    response = client.get(nomination_report_url, HTTP_ACCEPT="text/csv")
    assert response.status_code == 302
    parts = urlparse(response.url)
    query = parse_qs(parts.query)
    assert query["next"][0] == nomination_report_url


@pytest.mark.usefixtures("nomination")
@pytest.mark.parametrize("required_permission", ("report",))
def test_nomination_view_permission_required(
    client, nomination_report_url, user, required_permission
):
    client.force_login(user)
    user.user_permissions.remove(Permission.objects.get(codename=required_permission))

    response = client.get(nomination_report_url, HTTP_ACCEPT="text/csv")

    assert response.status_code == 302  # this view sends the user to a login


@pytest.mark.usefixtures("nomination")
@pytest.mark.parametrize("required_permission", ("report",))
def test_invalidated_nomination_view_permission_required(
    client, invalid_nominations_report_url, user, required_permission
):
    client.force_login(user)
    user.user_permissions.remove(Permission.objects.get(codename=required_permission))

    response = client.get(invalid_nominations_report_url, HTTP_ACCEPT="text/csv")

    assert response.status_code == 302  # this view sends the user to a login


@pytest.mark.usefixtures("invalidated_nomination")
def test_nomination_view_get(
    client,
    nomination_report_url,
    user,
    nomination,
):
    client.force_login(user)
    response = client.get(nomination_report_url, HTTP_ACCEPT="text/csv")

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

    assert data_row["field_1"] == nomination.field_1
    assert data_row["field_2"] == nomination.field_2
    assert data_row["field_3"] == nomination.field_3

    with pytest.raises(StopIteration):  # No more data
        next(reader)


@pytest.mark.usefixtures("nomination")
def test_invalidated_nomination_view_get(
    client, invalid_nominations_report_url, user, invalidated_nomination
):
    client.force_login(user)
    response = client.get(invalid_nominations_report_url, HTTP_ACCEPT="text/csv")

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

    assert data_row["field_1"] == invalidated_nomination.field_1
    assert data_row["field_2"] == invalidated_nomination.field_2
    assert data_row["field_3"] == invalidated_nomination.field_3

    with pytest.raises(StopIteration):  # No more data
        next(reader)


@pytest.fixture(name="valid_ranks_report_url")
def make_valid_ranks_report_url():
    return reverse("election:vote-report", kwargs={"election_id": "election_slug"})


def test_valid_ranks_report_disallows_get(client, valid_ranks_report_url, user):
    client.force_login(user)

    response = client.get(valid_ranks_report_url)

    assert response.status_code == 405


def test_valid_ranks_report_404_when_no_election(client, valid_ranks_report_url, user):
    client.force_login(user)

    response = client.post(valid_ranks_report_url)

    assert response.status_code == 404


@pytest.mark.parametrize("required_permission", ("view_raw_results", "report"))
def test_valid_ranks_report_permission_required(
    client, valid_ranks_report_url, user, required_permission
):
    client.force_login(user)
    user.user_permissions.remove(Permission.objects.get(codename=required_permission))

    response = client.post(valid_ranks_report_url)

    assert response.status_code == 403


@pytest.mark.usefixtures("election")
def test_valid_ranks_report_post_submits_request(client, valid_ranks_report_url, user):

    client.force_login(user)

    with mock.patch("nomnom.nominate.tasks.send_rank_report.delay") as delay:
        response = client.post(
            valid_ranks_report_url,
        )

    assert "text/html" in response["Content-Type"]

    # an email task should have been queued to send the report to the user
    delay.assert_called_once_with(
        election_id="election_slug",
        recipients=user.email,
        exclude_configured_recipients=True,
    )

    # a flash message should be in the response
    messages = [str(m) for m in get_messages(response.wsgi_request)]
    assert any("The full election report will be sent" for m in messages)
