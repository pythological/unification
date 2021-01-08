import pytest

from tests.utils import gen_long_chain
from unification import assoc, isvar, reify, unify, var
from unification.utils import transitive_get as walk

nesting_sizes = [10, 35, 300]


def unify_stack(u, v, s):

    u = walk(u, s)
    v = walk(v, s)

    if u == v:
        return s
    if isvar(u):
        return assoc(s, u, v)
    if isvar(v):
        return assoc(s, v, u)

    if isinstance(u, (tuple, list)) and type(u) == type(v):
        for i_u, i_v in zip(u, v):
            s = unify_stack(i_u, i_v, s)
            if s is False:
                return s

        return s

    return False


def reify_stack(u, s):

    u_ = walk(u, s)

    if u_ is not u:
        return reify_stack(u_, s)

    if isinstance(u_, (tuple, list)):
        return type(u_)(reify_stack(i_u, s) for i_u in u_)

    return u_


@pytest.mark.benchmark(group="unify_chain")
@pytest.mark.parametrize("size", nesting_sizes)
def test_unify_chain_stream(size, benchmark):
    a_lv = var()
    form = gen_long_chain(a_lv, size)
    term = gen_long_chain("a", size)

    res = benchmark(unify, form, term, {})
    assert res[a_lv] == "a"


@pytest.mark.benchmark(group="unify_chain")
@pytest.mark.parametrize("size", nesting_sizes)
def test_unify_chain_stack(size, benchmark):
    a_lv = var()
    form = gen_long_chain(a_lv, size)
    term = gen_long_chain("a", size)

    res = benchmark(unify_stack, form, term, {})
    assert res[a_lv] == "a"


@pytest.mark.benchmark(group="reify_chain")
@pytest.mark.parametrize("size", nesting_sizes)
def test_reify_chain_stream(size, benchmark):
    a_lv = var()
    form = gen_long_chain(a_lv, size)
    term = gen_long_chain("a", size)

    res = benchmark(reify, form, {a_lv: "a"})
    assert res == term


@pytest.mark.benchmark(group="reify_chain")
@pytest.mark.parametrize("size", nesting_sizes)
def test_reify_chain_stack(size, benchmark):
    a_lv = var()
    form = gen_long_chain(a_lv, size)
    term = gen_long_chain("a", size)

    res = benchmark(reify_stack, form, {a_lv: "a"})
    assert res == term
