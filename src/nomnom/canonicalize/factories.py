import factory

from . import models
from nomnom.nominate.factories import CategoryFactory


class WorkFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = models.Work

    name = factory.Faker("sentence", nb_words=3)
    category = factory.SubFactory(CategoryFactory)
    notes = factory.Faker("sentence", nb_words=10)
