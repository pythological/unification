from toolz import assoc
from operator import length_hint
from functools import partial
from collections import OrderedDict, deque
from collections.abc import Generator, Iterator, Mapping, Set

from .utils import transitive_get as walk
from .variable import isvar, Var
from .dispatch import dispatch


# An object used to tell the reifier that the next yield constructs the reified
# object from its constituent refications (if any).
construction_sentinel = object()


class UngroundLVarException(Exception):
    """An exception signaling that an unground variable was found."""


@dispatch(object, Mapping)
def _reify(o, s):
    yield o


@_reify.register(Var, Mapping)
def _reify_Var(o, s):
    o_w = walk(o, s)

    if o_w is o:
        yield o_w
    else:
        yield _reify(o_w, s)


def _reify_Iterable_ctor(ctor, t, s):
    """Create a generator that yields _reify generators.

    The yielded generators need to be evaluated by the caller and the fully
    reified results "sent" back to this generator so that it can finish
    constructing reified iterable.

    This approach allows us "collapse" nested `_reify` calls by pushing nested
    calls up the stack.
    """
    res = []

    if isinstance(t, Mapping):
        t = t.items()

    for y in t:
        r = _reify(y, s)
        if isinstance(r, Generator):
            r = yield r
        res.append(r)

    yield construction_sentinel

    yield ctor(res)


for seq, ctor in (
    (tuple, tuple),
    (list, list),
    (Iterator, iter),
    (set, set),
    (frozenset, frozenset),
):
    _reify.add((seq, Mapping), partial(_reify_Iterable_ctor, ctor))


for seq in (dict, OrderedDict):
    _reify.add((seq, Mapping), partial(_reify_Iterable_ctor, seq))


@_reify.register(slice, Mapping)
def _reify_slice(o, s):
    start = yield _reify(o.start, s)
    stop = yield _reify(o.stop, s)
    step = yield _reify(o.step, s)

    yield construction_sentinel

    yield slice(start, stop, step)


def _reify_eval(e, s, reify_filter=None):
    """Evaluate a stream of reification results.

    This implementation consists of a deque that simulates an evaluation stack
    of `_reify`-produced generators.  We're able to overcome `RecursionError`s
    this way.
    """

    b = _reify(e, s)

    if not isinstance(b, Generator):
        return b

    d = deque()
    r_args = None
    d.append(b)

    while d:
        z = d[-1]
        try:
            r = z.send(r_args)

            if reify_filter:
                _ = reify_filter(z, r)

            if isinstance(r, Generator):
                d.append(r)
                r_args = None
            else:
                r_args = r

        except StopIteration:
            _ = d.pop()

    return r


@dispatch(object, Mapping)
def reify(e, s, reify_filter=None):
    """Replace logic variables in a term, `e`, with their substitutions in `s`.

    >>> x, y = var(), var()
    >>> e = (1, x, (3, y))
    >>> s = {x: 2, y: 4}
    >>> reify(e, s)
    (1, 2, (3, 4))

    >>> e = {1: x, 3: (y, 5)}
    >>> reify(e, s)
    {1: 2, 3: (4, 5)}
    """
    return _reify_eval(e, s)


@dispatch(object, object, Mapping)
def _unify(u, v, s):
    return False


def _unify_Sequence(u, v, s):
    len_u = length_hint(u, -1)
    len_v = length_hint(v, -1)

    if len_u != len_v:
        return False

    for uu, vv in zip(u, v):
        s = unify(uu, vv, s)
        if s is False:
            return False
    return s


for seq in (tuple, list, Iterator):
    _unify.add((seq, seq, Mapping), _unify_Sequence)


@_unify.register(Set, Set, Mapping)
def _unify_Set(u, v, s):
    i = u & v
    u = u - i
    v = v - i
    return _unify(iter(u), iter(v), s)


@_unify.register(Mapping, Mapping, Mapping)
def _unify_Mapping(u, v, s):
    if len(u) != len(v):
        return False
    for key, uval in u.items():
        if key not in v:
            return False
        s = unify(uval, v[key], s)
        if s is False:
            return False
    return s


@_unify.register(slice, slice, dict)
def _unify_slice(u, v, s):
    return unify((u.start, u.stop, u.step), (v.start, v.stop, v.step), s)


@dispatch(object, object, Mapping)
def unify(u, v, s):
    """Find substitution so that u == v while satisfying s.

    >>> x = var('x')
    >>> unify((1, x), (1, 2), {})
    {~x: 2}
    """
    u = walk(u, s)
    v = walk(v, s)
    if u == v:
        return s
    if isvar(u):
        return assoc(s, u, v)
    if isvar(v):
        return assoc(s, v, u)
    return _unify(u, v, s)


@unify.register(object, object)
def unify_NoMap(u, v):
    return unify(u, v, {})


def unground_lvars(u, s):
    """Return the unground logic variables from a term and state."""

    lvars = set()

    def lvar_filter(z, r):
        nonlocal lvars

        if isvar(r):
            lvars.add(r)

        if r is construction_sentinel:
            z.close()

            # Remove this generator from the stack.
            raise StopIteration()

    _reify_eval(u, s, lvar_filter)

    return lvars


def isground(u, s):
    """Determine whether or not `u` contains an unground logic variable under mappings `s`."""

    def lvar_filter(z, r):

        if isvar(r):
            raise UngroundLVarException()
        elif r is construction_sentinel:
            z.close()

            # Remove this generator from the stack.
            raise StopIteration()

    try:
        _reify_eval(u, s, lvar_filter)
    except UngroundLVarException:
        return False

    return True
