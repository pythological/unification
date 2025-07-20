import sys
from collections import OrderedDict
from types import MappingProxyType

from tests.utils import gen_long_chain
from unification import var
from unification.core import assoc, isground, reify, unground_lvars, unify
from unification.utils import find_deepest_element_in_nested_structure, freeze


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


def test_reify_handles_deep_nesting():
    """Test that reify() can handle deeply nested structures without hitting
    recursion limits."""
    a_lv = var()

    # Test with a structure deeper than typical recursion limits
    deep_structure, _ = gen_long_chain(a_lv, 500)

    # This should succeed regardless of recursion limit
    result = reify(deep_structure, {a_lv: "resolved"})

    # Verify the structure was processed (check a few levels)
    assert isinstance(result, list)
    assert result[0] == 1  # First element should be the counter

    # Navigate a few levels deep to verify structure
    current = result
    for i in range(5):  # Check first 5 levels
        assert isinstance(current, list)
        assert len(current) == 2
        if i < 4:  # Not the last iteration
            current = current[1]

    # The deepest element should be our resolved value
    assert find_deepest_element_in_nested_structure(result) == "resolved"


def test_reify_works_with_low_recursion_limit():
    """Test that reify() works even when Python's recursion limit is
    artificially low."""
    a_lv = var()
    original_limit = sys.getrecursionlimit()

    try:
        # Set a low recursion limit
        sys.setrecursionlimit(100)

        # Create a structure much deeper than the recursion limit
        deep_structure, _ = gen_long_chain(a_lv, 200)

        # This should still work because the library uses stream_eval
        result = reify(deep_structure, {a_lv: "success"})

        # Verify it worked
        assert isinstance(result, list)

        # Navigate to verify the deepest element
        assert find_deepest_element_in_nested_structure(result) == "success"

    finally:
        sys.setrecursionlimit(original_limit)


def test_unify_handles_deep_nesting():
    """Test that unify() can handle deeply nested structures without hitting
    recursion limits."""
    a_lv = var()

    # Create two deep structures - one with a variable, one with a value
    structure_with_var, _ = gen_long_chain(a_lv, 300)
    structure_with_value, _ = gen_long_chain("matched", 300)

    # This should succeed regardless of recursion limit
    result = unify(structure_with_var, structure_with_value, {})

    # Verify unification succeeded
    assert result is not False
    assert isinstance(result, dict)
    assert a_lv in result
    assert result[a_lv] == "matched"


def test_unify_works_with_low_recursion_limit():
    """Test that unify() works even when Python's recursion limit is
    artificially low."""
    a_lv = var()
    original_limit = sys.getrecursionlimit()

    try:
        # Set a low recursion limit
        sys.setrecursionlimit(100)

        # Create structures much deeper than the recursion limit
        structure_with_var, _ = gen_long_chain(a_lv, 150)
        structure_with_value, _ = gen_long_chain("unified", 150)

        # This should still work because the library uses stream_eval
        result = unify(structure_with_var, structure_with_value, {})

        # Verify unification succeeded
        assert result is not False
        assert isinstance(result, dict)
        assert a_lv in result
        assert result[a_lv] == "unified"

    finally:
        sys.setrecursionlimit(original_limit)


def test_reify_correctness_on_moderately_deep_structure():
    """Test that reify() produces correct results on a moderately deep
    structure we can verify."""
    a_lv = var()

    # Create a structure deep enough to be meaningful but shallow enough to verify
    deep_structure, lvars = gen_long_chain(a_lv, 20, use_lvars=True)

    # Create substitution mapping
    substitutions = {a_lv: "final_value"}
    substitutions.update({lvar: f"level_{level}" for lvar, level in lvars.items()})

    # Reify the structure
    result = reify(deep_structure, substitutions)

    # Verify the structure is correct by checking a few key positions
    assert isinstance(result, list)
    assert result[0] == "level_1"  # First element should be the substituted lvar

    # Navigate and verify a few levels
    current = result
    for expected_level in [1, 2, 3]:
        assert isinstance(current, list)
        assert len(current) == 2
        assert current[0] == f"level_{expected_level}"
        if expected_level < 3:  # Not the last iteration
            current = current[1]

    # The deepest element should be our final value
    assert find_deepest_element_in_nested_structure(result) == "final_value"


def test_mixed_deep_and_shallow_structures():
    """Test reify() with a mix of deep and shallow nested structures."""
    a_lv, b_lv = var(), var()

    # Create a complex structure with both deep and shallow parts
    deep_part, _ = gen_long_chain(a_lv, 100)
    shallow_part = [b_lv, "shallow"]

    complex_structure = {
        "deep": deep_part,
        "shallow": shallow_part,
        "mixed": [deep_part, shallow_part],
    }

    substitutions = {a_lv: "deep_value", b_lv: "shallow_value"}

    # This should handle the mixed complexity gracefully
    result = reify(complex_structure, substitutions)

    # Verify the structure
    assert isinstance(result, dict)
    assert "deep" in result
    assert "shallow" in result
    assert "mixed" in result

    # Check the shallow part
    assert result["shallow"] == ["shallow_value", "shallow"]

    # Check that deep part was processed (verify it's a list starting with 99)
    assert isinstance(result["deep"], list)
    assert result["deep"][0] == 1

    # Check mixed part
    assert isinstance(result["mixed"], list)
    assert len(result["mixed"]) == 2
    assert result["mixed"][1] == ["shallow_value", "shallow"]


def test_unify_freeze():
    # These will sometimes be in different orders after conversion to
    # `iter`/`list`/`tuple`!
    # u = frozenset({("name", a), ("debit", b)})
    # v = frozenset({("name", "Bob"), ("debit", 100)})

    a, b = var("name"), var("amount")
    u = freeze({"name": a, "debit": b})
    v = freeze({"name": "Bob", "debit": 100})

    assert unify(u, v, {}) == {a: "Bob", b: 100}
