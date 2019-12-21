from toolz import assoc
from operator import length_hint
from collections.abc import Iterator, Mapping

from .utils import transitive_get as walk
from .variable import isvar
from .dispatch import dispatch


@dispatch(Iterator, Mapping)
def _reify(t, s):
    return iter(reify(arg, s) for arg in t)


@dispatch(tuple, Mapping)
def _reify(t, s):
    return tuple(reify(iter(t), s))


@dispatch(list, Mapping)
def _reify(t, s):
    return list(reify(iter(t), s))


@dispatch(dict, Mapping)
def _reify(d, s):
    return dict((k, reify(v, s)) for k, v in d.items())


@dispatch(object, Mapping)
def _reify(o, s):
    return o  # catch all, just return the object


def reify(e, s):
    """Replace variables of an expression with their substitutions.

    >>> x, y = var(), var()
    >>> e = (1, x, (3, y))
    >>> s = {x: 2, y: 4}
    >>> reify(e, s)
    (1, 2, (3, 4))

    >>> e = {1: x, 3: (y, 5)}
    >>> reify(e, s)
    {1: 2, 3: (4, 5)}
    """
    if isvar(e):
        return reify(s[e], s) if e in s else e
    return _reify(e, s)


@dispatch(object, object, Mapping)
def _unify(u, v, s):
    return False  # catch all


def _unify_seq(u, v, s):
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
    _unify.add((seq, seq, Mapping), _unify_seq)


@dispatch((set, frozenset), (set, frozenset), Mapping)
def _unify(u, v, s):
    i = u & v
    u = u - i
    v = v - i
    return _unify(sorted(u), sorted(v), s)


@dispatch(dict, dict, Mapping)
def _unify(u, v, s):
    if len(u) != len(v):
        return False
    for key, uval in u.items():
        if key not in v:
            return False
        s = unify(uval, v[key], s)
        if s is False:
            return False
    return s


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


@dispatch(object, object)
def unify(u, v):
    return unify(u, v, {})
