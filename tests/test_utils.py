from unification.utils import freeze


def test_freeze():
    assert freeze({1: [2, 3]}) == frozenset([(1, (2, 3))])
    assert freeze(set([1])) == frozenset([1])
    assert freeze(([1],)) == ((1,),)
