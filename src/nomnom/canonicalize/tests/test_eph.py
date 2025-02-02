from nomnom.canonicalize.factories import WorkFactory
from nomnom.nominate.factories import NominationFactory


def test_eph_on_single_works(category):
    w1 = WorkFactory.create(category=category)
    w1.nominations.add(NominationFactory.create(category=category))
    w2 = WorkFactory.create()
    w2.nominations.add(NominationFactory.create(category=category))
    w3 = WorkFactory.create(category=category)
    w3.nominations.add(NominationFactory.create(category=category))
    w4 = WorkFactory.create()
    w4.nominations.add(NominationFactory.create(category=category))
    w5 = WorkFactory.create(category=category)
    w5.nominations.add(NominationFactory.create(category=category))

    assert False
