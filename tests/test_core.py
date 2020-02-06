from types import MappingProxyType
from collections import OrderedDict

from unification import var
from unification.core import (
    reify,
    unify,
    unground_lvars,
    isground,
    ContractingAssociationMap,
)


def test_reify():
    x, y, z = var(), var(), var()
    s = {x: 1, y: 2, z: (x, y)}
    assert reify(x, s) == 1
    assert reify(10, s) == 10
    assert reify((1, y), s) == (1, 2)
    assert reify((1, (x, (y, 2))), s) == (1, (1, (2, 2)))
    assert reify(z, s) == (1, 2)
    assert reify(z, MappingProxyType(s)) == (1, 2)


def test_reify_Mapping():
    x, y = var(), var()
    s = {x: 2, y: 4}
    e = [(1, x), (3, {5: y})]
    expected_res = [(1, 2), (3, {5: 4})]
    assert reify(dict(e), s) == dict(expected_res)
    assert reify(OrderedDict(e), s) == OrderedDict(expected_res)


def test_reify_Set():
    x, y = var(), var()
    assert reify({1, 2, x, y}, {x: 3}) == {1, 2, 3, y}
    assert reify(frozenset({1, 2, x, y}), {x: 3}) == frozenset({1, 2, 3, y})


def test_reify_list():
    x, y = var(), var()
    s = {x: 2, y: 4}
    e = [1, [x, 3], y]
    assert reify(e, s) == [1, [2, 3], 4]


def test_reify_complex():
    x, y = var(), var()
    s = {x: 2, y: 4}
    e = {1: [x], 3: (y, 5)}

    assert reify(e, s) == {1: [2], 3: (4, 5)}


def test_unify_slice():
    x = var("x")
    y = var("y")

    assert unify(slice(1), slice(1), {}) == {}
    assert unify(slice(1, 2, 3), x, {}) == {x: slice(1, 2, 3)}
    assert unify(slice(1, 2, None), slice(x, y), {}) == {x: 1, y: 2}


def test_reify_slice():
    assert reify(slice(1, var(2), 3), {var(2): 10}) == slice(1, 10, 3)


def test_unify():
    assert unify(1, 1, {}) == {}
    assert unify(1, 2, {}) is False
    assert unify(var(1), 2, {}) == {var(1): 2}
    assert unify(2, var(1), {}) == {var(1): 2}
    assert unify(2, var(1), MappingProxyType({})) == {var(1): 2}


def test_iter():
    assert unify([1], (1,)) is False
    assert unify((i for i in [1, 2]), [1, 2]) is False


def test_unify_seq():
    assert unify((1, 2), (1, 2), {}) == {}
    assert unify([1, 2], [1, 2], {}) == {}
    assert unify((1, 2), (1, 2, 3), {}) is False
    assert unify((1, var(1)), (1, 2), {}) == {var(1): 2}
    assert unify((1, var(1)), (1, 2), {var(1): 3}) is False


def test_unify_set():
    x, y = var(), var()
    assert unify({1, 2}, {1, 2}, {}) == {}
    assert unify({1, x}, {1, 2}, {}) == {x: 2}
    assert unify({x, 2}, {1, 2}, {}) == {x: 1}
    assert unify({1, y, x}, {2, 1}, {x: 2}) is False


def test_unify_dict():
    assert unify({1: 2}, {1: 2}, {}) == {}
    assert unify({1: 2}, {1: 3}, {}) is False
    assert unify({2: 2}, {1: 2}, {}) is False
    assert unify({2: 2, 3: 3}, {1: 2}, {}) is False
    assert unify({1: var(5)}, {1: 2}, {}) == {var(5): 2}


def test_unify_complex():
    assert unify((1, {2: 3}), (1, {2: 3}), {}) == {}
    assert unify((1, {2: 3}), (1, {2: 4}), {}) is False
    assert unify((1, {2: var(5)}), (1, {2: 4}), {}) == {var(5): 4}

    assert unify({1: (2, 3)}, {1: (2, var(5))}, {}) == {var(5): 3}
    assert unify({1: [2, 3]}, {1: [2, var(5)]}, {}) == {var(5): 3}


def test_unground_lvars():
    a_lv, b_lv = var(), var()

    for ctor in (tuple, list, iter, set, frozenset):

        if ctor not in (set, frozenset):
            sub_ctor = list
        else:
            sub_ctor = tuple

        assert unground_lvars(ctor((1, 2)), {}) == set()
        assert unground_lvars(
            ctor((1, sub_ctor((a_lv, sub_ctor((b_lv, 2)), 3)))), {}
        ) == {a_lv, b_lv}
        assert unground_lvars(
            ctor((1, sub_ctor((a_lv, sub_ctor((b_lv, 2)), 3)))), {a_lv: 4}
        ) == {b_lv}
        assert (
            unground_lvars(
                ctor((1, sub_ctor((a_lv, sub_ctor((b_lv, 2)), 3)))), {a_lv: 4, b_lv: 5}
            )
            == set()
        )

        assert isground(ctor((1, 2)), {})
        assert isground(ctor((1, a_lv)), {a_lv: 2})
        assert isground(ctor((a_lv, sub_ctor((b_lv, 2)), 3)), {a_lv: b_lv, b_lv: 1})

        assert not isground(ctor((1, a_lv)), {a_lv: b_lv})
        assert not isground(ctor((1, var())), {})
        assert not isground(ctor((1, sub_ctor((a_lv, sub_ctor((b_lv, 2)), 3)))), {})
        assert not isground(
            ctor((a_lv, sub_ctor((b_lv, 2)), 3)), {a_lv: b_lv, b_lv: var("c")}
        )


def test_ContractingAssociationMap():

    a, b, c, d = var("a"), var("b"), var("c"), var("d")

    # Contractions should happen in the constructor
    m = ContractingAssociationMap({b: c, c: a, d: d})
    assert m == {b: a, c: a}

    # Order of entry shouldn't matter
    m = ContractingAssociationMap([(b, c), (c, a), (d, d)])
    assert m == {b: a, c: a}

    m = ContractingAssociationMap([(c, a), (b, c), (d, d)])
    assert m == {b: a, c: a}

    # Nor should the means of entry
    m = ContractingAssociationMap()
    m[a] = b
    m[b] = c

    assert m == {b: c, a: c}

    m = ContractingAssociationMap()
    m[b] = c
    m[a] = b

    assert m == {b: c, a: c}

    # Make sure we don't introduce cycles, and that we remove newly imposed
    # ones
    m[c] = a
    assert m == {b: a, c: a}

    m = ContractingAssociationMap([(b, c), (c, b), (d, d)])
    assert m == {c: b}

    m = ContractingAssociationMap([(c, b), (b, c), (d, d)])
    assert m == {b: c}

    # Simulate a long chain
    import timeit

    dict_time = timeit.timeit(
        stmt="""
    from unification import var, reify
    from unification.utils import transitive_get as walk

    m = {}
    first_lvar = var()
    lvar = first_lvar
    for i in range(1000):
        m[lvar] = var()
        lvar = m[lvar]
    m[lvar] = 1

    assert walk(first_lvar, m) == 1
    """,
        number=10,
    )

    cmap_time = timeit.timeit(
        stmt="""
    from unification import var, reify
    from unification.core import ContractingAssociationMap

    m = ContractingAssociationMap()
    first_lvar = var()
    lvar = first_lvar
    for i in range(1000):
        m[lvar] = var()
        lvar = m[lvar]
    m[lvar] = 1

    assert m[first_lvar] == 1
    """,
        number=10,
    )
