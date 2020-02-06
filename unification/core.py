from toolz import assoc
from operator import length_hint
from functools import partial

from collections import OrderedDict, UserDict
from collections.abc import Iterator, Mapping, Set

from .utils import transitive_get as walk
from .variable import isvar
from .dispatch import dispatch


class UngroundLVarException(Exception):
    """An exception signaling that an unground variables was found."""


class ContractingAssociationMap(UserDict):
    """A map that contracts association chains.

    For instance, if we add the logic variable association a -> b to a
    `ContractingAssociationMap` containing a logic variable associationn like
    {c -> a, ...}, the result will be {c -> b, a -> b, ...}.
    """

    def __init__(self, *args, **kwargs):
        self.inverse = {}
        super().__init__(*args, **kwargs)
        # TODO
        # self.data = WeakKeyDictionary(self.data)

    def __setitem__(self, key, value):

        assert isvar(key)

        # Self-associations are a waste
        if key == value:
            return

        # Get the (one-step) walked value
        walk_value = self.data.get(value, value)

        # Get the keys that have this key as a value
        key_keys = self.inverse.setdefault(key, [])

        if walk_value == key:
            # The walked value equals the key, so we need to drop the `value`
            # association before we loop and reintroduce it
            del self[value]
            walk_value = value

        for key_key in tuple(key_keys):

            # old_val = self.data[key_key]

            # Remove the old mapping and its inverse
            del self[key_key]

            # Don't add self associations
            if (key_key == value) or (key_key == walk_value):
                continue

            # Remap those association keys to this lvar
            # TODO: Flatten-out this tail recursion?
            self[key_key] = walk_value

        if isvar(walk_value):
            # Add the new association's inverse
            self.inverse.setdefault(walk_value, []).append(key)

        super().__setitem__(key, walk_value)

    def __delitem__(self, key):

        val = self.data[key]

        if isvar(val):

            # Remove the inverse association
            self.inverse.setdefault(val, []).remove(key)

            if val in self.inverse and not self.inverse[val]:
                del self.inverse[val]

        super().__delitem__(key)


@dispatch(object, Mapping)
def _reify(o, s):
    return o


def _reify_Iterable(type_ctor, t, s):
    return type_ctor(tuple(reify(a, s) for a in t))


for seq, ctor in (
    (tuple, tuple),
    (list, list),
    (Iterator, iter),
    (set, set),
    (frozenset, frozenset),
):
    _reify.add((seq, Mapping), partial(_reify_Iterable, ctor))


def _reify_Mapping(ctor, d, s):
    return ctor((k, reify(v, s)) for k, v in d.items())


for seq in (dict, OrderedDict):
    _reify.add((seq, Mapping), partial(_reify_Mapping, seq))


@_reify.register(slice, Mapping)
def _reify_slice(o, s):
    return slice(*reify((o.start, o.stop, o.step), s))


@dispatch(object, Mapping)
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
        e = walk(e, s)
    return _reify(e, s)


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
    _reify_object = _reify.dispatch(object, Mapping)

    def _reify_var(u, s):
        nonlocal lvars

        if isvar(u):
            lvars.add(u)
        return u

    _reify.add((object, Mapping), _reify_var)
    try:
        reify(u, s)
    finally:
        _reify.add((object, Mapping), _reify_object)

    return lvars


def isground(u, s):
    """Determine whether or not `u` contains an unground logic variable under mappings `s`."""

    _reify_object = _reify.dispatch(object, Mapping)

    def _reify_var(u, s):
        if isvar(u):
            raise UngroundLVarException()
        return u

    _reify.add((object, Mapping), _reify_var)
    try:
        reify(u, s)
    except UngroundLVarException:
        return False
    finally:
        _reify.add((object, Mapping), _reify_object)

    return True
