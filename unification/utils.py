import sys
from collections import deque
from collections.abc import Mapping, Sequence, Set
from contextlib import suppress

__PY37 = sys.version_info >= (3, 7)


def transitive_get(key, d):
    """Get a value for a dict key in a transitive fashion.

    >>> d = {1: 2, 2: 3, 3: 4}
    >>> d.get(1)
    2
    >>> transitive_get(1, d)
    4
    """
    with suppress(TypeError):
        while key in d:
            key = d[key]
    return key


def _toposort(edges):
    """Topologically sort a dictionary.

    Algorithm by Kahn [1] - O(nodes + vertices).

    inputs:
        edges - a dict of the form {a: {b, c}} where b and c depend on a
    outputs:
        L - an ordered list of nodes that satisfy the dependencies of edges

    >>> _toposort({1: (2, 3), 2: (3, )})
    [1, 2, 3]

    Closely follows the wikipedia page [2]

    [1] Kahn, Arthur B. (1962), "Topological sorting of large networks",
    Communications of the ACM
    [2] http://en.wikipedia.org/wiki/Toposort#Algorithms
    """
    incoming_edges = {k: set(val) for k, val in reverse_dict(edges).items()}

    S = deque(v for v in edges if v not in incoming_edges)
    L = []

    while S:
        n = S.popleft()
        for m in edges.get(n, ()):
            edges_m = incoming_edges[m]
            edges_m.remove(n)
            if not edges_m:
                S.append(m)
        L.append(n)
    
    if any(incoming_edges.get(v) for v in edges):
        raise ValueError("Input has cycles")
    
    return L


def reverse_dict(d):
    """Reverses the direction of a dependency dict.

    >>> d = {'a': (1, 2), 'b': (2, 3), 'c':()}
    >>> reverse_dict(d)  # doctest: +SKIP
    {1: ('a',), 2: ('a', 'b'), 3: ('b',)}

    :note: dict order are not deterministic. As we iterate on the
        input dict, it make the output of this function depend on the
        dict order. So this function output order should be considered
        as undeterministic.

    """
    result = {}
    for key in d:
        for val in d[key]:
            result[val] = result.get(val, ()) + (key,)
    return result


def freeze(d):
    """Freeze container to hashable a form.

    >>> freeze(1)
    1

    >>> freeze([1, 2])
    (1, 2)

    >>> freeze({1: 2}) # doctest: +SKIP
    ((1, 2),)
    """
    if isinstance(d, Mapping):
        if __PY37:
            items = d.items()
        else:
            items = sorted(d.items(), key=lambda x: hash(x[0]))
        return tuple(map(freeze, items))
    if isinstance(d, Set):
        return tuple(map(freeze, sorted(d, key=hash)))
    if isinstance(d, Sequence):
        return tuple(map(freeze, d))
    return d
