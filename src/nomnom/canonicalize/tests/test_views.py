import random
from contextlib import contextmanager

import pytest
from django.core.exceptions import ValidationError
from django.db import connection
from django.http import Http404
from django.test.client import RequestFactory
from django.test.utils import CaptureQueriesContext

from nomnom.canonicalize import models, views
from nomnom.canonicalize.factories import WorkFactory
from nomnom.nominate.factories import NominationFactory


@contextmanager
def no_inserts():
    with CaptureQueriesContext(connection) as context:
        try:
            rv = yield
        finally:
            ...

    for query in context.captured_queries:
        sql = query["sql"]
        assert not (sql.startswith("INSERT INTO ") or sql.startswith("UPDATE ")), (
            "The DB was unexpectedly updated:\n" + sql
        )

    return rv


@pytest.fixture(name="log_queries")
def fixture_log_queries():
    with CaptureQueriesContext(connection) as context:
        try:
            yield context
        finally:
            ...

    for query in context.captured_queries:
        print(query["sql"])


@pytest.mark.django_db
class TestWorksWithNoWorkId:
    def test_group_works_with_no_previous_work_picks_first(
        self,
    ):
        nominations = NominationFactory.create_batch(3)
        post = RequestFactory().post(
            "/canonicalize/group_works",
            {"nominations": [n.pk for n in nominations]},
        )

        response = views.group_works(post)

        assert response.status_code == 200
        works = models.Work.objects.filter(name=nominations[0].proposed_work_name())
        assert works.count() == 1
        work = works.first()
        assert work.nominations.count() == 3
        assert set(work.nominations.all()) == set(nominations)

    def test_group_works_with_single_previous_work_picks_that(self, tp):
        nominations = NominationFactory.create_batch(3)
        work = WorkFactory.create()
        work.nominations.add(random.choice(nominations))

        post = RequestFactory().post(
            "/canonicalize/group_works", {"nominations": [n.pk for n in nominations]}
        )
        response = views.group_works(post)
        assert response.status_code == 200
        works = models.Work.objects.all()
        assert works.count() == 1
        stored_work = works.first()
        assert work == stored_work
        assert work.nominations.count() == 3
        assert set(work.nominations.all()) == set(nominations)

    def test_group_works_with_multiple_previous_works_fails(self, tp):
        nominations = NominationFactory.create_batch(3)
        work = WorkFactory.create()
        work.nominations.add(nominations[0])
        work = WorkFactory.create()
        work.nominations.add(nominations[1])

        post = RequestFactory().post(
            "/canonicalize/group_works",
            {"nominations": [n.pk for n in nominations]},
        )

        with no_inserts():
            with pytest.raises(ValidationError):
                views.group_works(post)

    def test_fails_when_nomination_id_does_not_exist(self, tp):
        nominations = NominationFactory.create_batch(3)

        post = RequestFactory().post(
            "/canonicalize/group_works",
            {"nominations": [n.pk for n in nominations] + [-1]},
        )
        with pytest.raises(Http404):
            with no_inserts():
                views.group_works(post)


@pytest.mark.django_db
class TestWorksWithWorkId:
    def test_group_works_sets_work(self, tp):
        nominations = NominationFactory.create_batch(3)
        work = WorkFactory.create()

        post = RequestFactory().post(
            "/canonicalize/group_works",
            {"nominations": [n.pk for n in nominations]},
        )
        response = views.group_works(post, work.pk)
        assert response.status_code == 200
        works = models.Work.objects.all()
        assert works.count() == 1
        assert work == works.first()

        assert work.nominations.count() == 3
        assert set(work.nominations.all()) == set(nominations)

    def test_group_works_overwrites_work(self, tp):
        nominations = NominationFactory.create_batch(3)
        nomination = random.choice(nominations)
        # add to an anonymous work
        WorkFactory.create().nominations.add(nomination)

        work = WorkFactory.create()

        post = RequestFactory().post(
            "/canonicalize/group_works",
            {"nominations": [n.pk for n in nominations]},
        )
        response = views.group_works(post, work.pk)
        assert response.status_code == 200
        works = models.Work.objects.all()
        assert works.count() == 2
        assert work in works

        work.refresh_from_db()
        assert work.nominations.count() == 3
        assert set(work.nominations.all()) == set(nominations)

    def test_fails_when_nomination_id_does_not_exist(self, tp):
        nominations = NominationFactory.create_batch(3)
        work = WorkFactory.create()

        post = RequestFactory().post(
            "/canonicalize/group_works",
            {"nominations": [n.pk for n in nominations] + [-1]},
        )
        with pytest.raises(Http404):
            with no_inserts():
                views.group_works(post, work.pk)

    def test_fails_when_work_does_not_exist(self, tp):
        nominations = NominationFactory.create_batch(3)
        post = RequestFactory().post(
            "/canonicalize/group_works",
            {"nominations": [n.pk for n in nominations]},
        )
        with pytest.raises(Http404):
            with no_inserts():
                views.group_works(post, -1)
