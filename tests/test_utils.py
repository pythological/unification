from unification.utils import freeze, transitive_get
from unification.variable import var


def test_transitive_get():
    x, y = var(), var()
    assert transitive_get(x, {x: y, y: 1}) == 1
    assert transitive_get({1: 2}, {x: y, y: 1}) == {1: 2}
    # Cycles are not handled
    # assert transitive_get(x, {x: x}) == x
    # assert transitive_get(x, {x: y, y: x}) == x


def test_freeze():
    assert freeze({1: [2, 3]}) == ((1, (2, 3)),)
    assert freeze(set([1])) == (1,)
    assert freeze(([1],)) == ((1,),)
