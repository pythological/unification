import pytest

from types import MappingProxyType
from collections import OrderedDict

from unification import var
from unification.core import isground, reify, unground_lvars, unify


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

    # Make sure that no composite elements are constructed within the
    # groundedness checks.
    class CounterList(list):
        constructions = 0

        def __new__(cls, *args, **kwargs):
            cls.constructions += 1
            return super().__new__(cls, *args, **kwargs)

    test_l = CounterList([1, 2, CounterList([a_lv, CounterList([4])])])

    assert CounterList.constructions == 3

    assert not isground(test_l, {})
    assert CounterList.constructions == 3

    assert unground_lvars(test_l, {}) == {a_lv}


def test_recursion_limit():
    import sys
    import platform

    def gen_long_chain(last_elem=None, N=None):
        b_struct = None
        if N is None:
            N = sys.getrecursionlimit()
        for i in range(N - 1, 0, -1):
            b_struct = [i, last_elem if i == N - 1 else b_struct]
        return b_struct

    a_lv = var()

    b = gen_long_chain(a_lv, 10)
    res = reify(b, {a_lv: "a"})
    assert res == gen_long_chain("a", 10)

    r_limit = sys.getrecursionlimit()

    try:
        sys.setrecursionlimit(100)

        b = gen_long_chain(a_lv, 200)
        res = reify(b, {a_lv: "a"})
        exp_res = gen_long_chain("a", 200)

        if platform.python_implementation().lower() != "pypy":
            # CPython has stack limit issues when comparing nested lists, but
            # PyPy doesn't.
            with pytest.raises(RecursionError):
                assert res == exp_res

        sys.setrecursionlimit(300)

        assert res == exp_res

    finally:
        sys.setrecursionlimit(r_limit)
