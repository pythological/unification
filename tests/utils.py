import sys

from unification.variable import var


def gen_long_chain(last_elem=None, N=None, use_lvars=False):
    """Generate a nested list of length `N` with the last element set to `last_elm`.

    Parameters
    ----------
    last_elem: object
        The element to be placed in the inner-most nested list.
    N: int
        The number of nested lists.
    use_lvars: bool
        Whether or not to add `var`s to the first elements of each nested list
        or simply integers.  If ``True``, each `var` is passed the nesting
        level integer (i.e. ``var(i)``).

    Returns
    -------
    list, dict
        The generated nested list and a ``dict`` containing the generated
        `var`s and their nesting level integers, if any.

    """
    b_struct = None
    if N is None:
        N = sys.getrecursionlimit()
    lvars = {}
    for i in range(N - 1, 0, -1):
        i_el = var(i) if use_lvars else i
        if use_lvars:
            lvars[i_el] = i
        b_struct = [i_el, last_elem if i == N - 1 else b_struct]
    return b_struct, lvars
