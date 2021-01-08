import sys
from collections import OrderedDict
from types import MappingProxyType

import pytest

from tests.utils import gen_long_chain
from unification import var
from unification.core import assoc, isground, reify, unground_lvars, unify
from unification.utils import freeze


def test_assoc():
    d = {"a": 1, 2: 2}
    assert assoc(d, "c", 3) is not d
    assert assoc(d, "c", 3) == {"a": 1, 2: 2, "c": 3}
    assert assoc(d, 2, 3) == {"a": 1, 2: 3}
    assert assoc(d, "a", 0) == {"a": 0, 2: 2}
    assert d == {"a": 1, 2: 2}

    def assoc_OrderedDict(s, u, v):
        s[u] = v
        return s

    assoc.add((OrderedDict, object, object), assoc_OrderedDict)

    x = var()
    d2 = OrderedDict(d)
    assert assoc(d2, x, 3) is d2
    assert assoc(d2, x, 3) == {"a": 1, 2: 2, x: 3}
    assert assoc(d, x, 3) is not d


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
    assert reify((1, {2: x}), {x: slice(0, y), y: 3}) == (1, {2: slice(0, 3)})


def test_reify_slice():
    x = var()
    assert reify(slice(1, x, 3), {x: 10}) == slice(1, 10, 3)


def test_unify():
    x, y, z = var(), var(), var()
    assert unify(x, x, {}) == {}
    assert unify(1, 1, {}) == {}
    assert unify(1, 2, {}) is False
    assert unify(x, 2, {}) == {x: 2}
    assert unify(2, x, {}) == {x: 2}
    assert unify(2, x, MappingProxyType({})) == {x: 2}
    assert unify(x, y, {}) == {x: y}
    assert unify(y, x, {}) == {y: x}
    assert unify(y, x, {y: x}) == {y: x}
    assert unify(x, y, {y: x}) == {y: x}
    assert unify(y, x, {x: y}) == {x: y}
    assert unify(x, y, {x: y}) == {x: y}
    assert unify(y, x, {y: z}) == {y: z, z: x}
    assert unify(x, y, {y: z}) == {y: z, x: z}


def test_unify_slice():
    x, y = var(), var()
    assert unify(slice(1), slice(1), {}) == {}
    assert unify(slice(1, 2, 1), slice(2, 2, 1), {}) is False
    assert unify(slice(1, 2, 1), slice(x, 2, 1), {x: 2}) is False
    assert unify(slice(1, 2, 1), slice(1, 3, 1), {}) is False
    assert unify(slice(1, 4, 2), slice(1, 4, 1), {}) is False
    assert unify(slice(x), slice(x), {}) == {}
    assert unify(slice(1, 2, 3), x, {}) == {x: slice(1, 2, 3)}
    assert unify(slice(1, 2, None), slice(x, y), {}) == {x: 1, y: 2}


def test_unify_iter():
    x = var()
    assert unify([1], (1,)) is False
    assert unify((i for i in [1, 2]), [1, 2]) is False
    assert unify(iter([1, x]), iter([1, 2])) == {x: 2}


def test_unify_seq():
    x = var()
    assert unify([], [], {}) == {}
    assert unify([x], [x], {}) == {}
    assert unify((1, 2), (1, 2), {}) == {}
    assert unify([1, 2], [1, 2], {}) == {}
    assert unify((1, 2), (1, 2, 3), {}) is False
    assert unify((1, x), (1, 2), {}) == {x: 2}
    assert unify((1, x), (1, 2), {x: 3}) is False

    a, b, z = var(), var(), var()
    assert unify([a, b], x, {x: [z, 1]}) == {x: [z, 1], a: z, b: 1}


def test_unify_set():
    x, y = var(), var()
    assert unify(set(), set(), {}) == {}
    assert unify({x}, {x}, {}) == {}
    assert unify({1, 2}, {1, 2}, {}) == {}
    assert unify({1, x}, {1, 2}, {}) == {x: 2}
    assert unify({x, 2}, {1, 2}, {}) == {x: 1}
    assert unify({1, y, x}, {2, 1}, {x: 2}) is False


def test_unify_dict():
    x = var()
    assert unify({1: 2}, {1: 2}, {}) == {}
    assert unify({1: x}, {1: x}, {}) == {}
    assert unify({1: 2}, {1: 3}, {}) is False
    assert unify({2: 2}, {1: 2}, {}) is False
    assert unify({2: 2, 3: 3}, {1: 2}, {}) is False
    assert unify({1: x}, {1: 2}, {}) == {x: 2}


def test_unify_complex():
    x, y = var(), var()
    assert unify((1, {2: 3}), (1, {2: 3}), {}) == {}
    assert unify((1, {2: 3}), (1, {2: 4}), {}) is False
    assert unify((1, {2: x}), (1, {2: 4}), {}) == {x: 4}
    assert unify((1, {2: x}), (1, {2: slice(1, y)}), {y: 2}) == {x: slice(1, y), y: 2}
    assert unify({1: (2, 3)}, {1: (2, x)}, {}) == {x: 3}
    assert unify({1: [2, 3]}, {1: [2, x]}, {}) == {x: 3}


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


def test_reify_recursion_limit():
    import platform

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


def test_unify_recursion_limit():
    a_lv = var()

    b = gen_long_chain("a")
    b_var = gen_long_chain(a_lv)

    s = unify(b, b_var, {})

    assert s[a_lv] == "a"


def test_unify_freeze():

    # These will sometimes be in different orders after conversion to
    # `iter`/`list`/`tuple`!
    # u = frozenset({("name", a), ("debit", b)})
    # v = frozenset({("name", "Bob"), ("debit", 100)})

    a, b = var("name"), var("amount")
    u = freeze({"name": a, "debit": b})
    v = freeze({"name": "Bob", "debit": 100})

    assert unify(u, v, {}) == {a: "Bob", b: 100}
