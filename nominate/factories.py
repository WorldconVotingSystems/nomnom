import factory

from . import models


class UserFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = models.UserModel

    username = factory.Faker("user_name")
    email = factory.Faker("email")
    password = factory.Faker("password")
    last_name = factory.Sequence(lambda n: f"factory_made_{n}")


class NominatingMemberProfileFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = models.NominatingMemberProfile

    user = factory.SubFactory(UserFactory)
    preferred_name = factory.Faker("name")
    member_number = factory.Sequence(lambda n: f"#faker-{n}")


class ElectionFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = models.Election

    name = factory.Faker("sentence", nb_words=4)
    slug = factory.Faker("slug")
    state = models.Election.STATE.PRE_NOMINATION


class BaseCategoryFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = models.Category

    election = factory.SubFactory(ElectionFactory)
    ballot_position = factory.Sequence(lambda n: n)


class SingleFieldCategoryFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = models.Category

    name = factory.Faker("sentence", nb_words=3)
    description = factory.Faker("sentence", nb_words=10)
    election = factory.SubFactory(ElectionFactory)
    ballot_position = factory.Sequence(lambda n: n)
    fields = 1
    field_1_description = factory.Faker("sentence", nb_words=4)


CategoryFactory = SingleFieldCategoryFactory


class TwoFieldCategoryFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = models.Category

    election = factory.SubFactory(ElectionFactory)
    ballot_position = factory.Sequence(lambda n: n)
    fields = 2
    field_1_description = factory.Faker("sentence", nb_words=4)
    field_2_description = factory.Faker("sentence", nb_words=4)
    field_2_required = True


class ThreeFieldCategoryFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = models.Category

    election = factory.SubFactory(ElectionFactory)
    ballot_position = factory.Sequence(lambda n: n)
    fields = 3
    field_1_description = factory.Faker("sentence", nb_words=4)
    field_2_description = factory.Faker("sentence", nb_words=4)
    field_2_required = True
    field_3_description = factory.Faker("sentence", nb_words=4)
    field_3_required = True


class NominationFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = models.Nomination

    category = factory.SubFactory(CategoryFactory)
    nominator = factory.SubFactory(NominatingMemberProfileFactory)
    field_1 = factory.Faker("sentence", nb_words=4)
    field_2 = factory.Faker("sentence", nb_words=4)
    field_3 = factory.Faker("sentence", nb_words=4)


class FinalistFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = models.Finalist

    category = factory.SubFactory(CategoryFactory)
    name = factory.Faker("sentence", nb_words=4)
    ballot_position = factory.Sequence(lambda n: n)


class RankFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = models.Rank

    membership = factory.SubFactory(NominatingMemberProfileFactory)
    finalist = factory.SubFactory(FinalistFactory)
    position = factory.Sequence(lambda n: n)
    voter_ip_address = factory.Faker("ipv4")
