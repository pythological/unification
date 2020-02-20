import sys


def gen_long_chain(last_elem=None, N=None):
    b_struct = None
    if N is None:
        N = sys.getrecursionlimit()
    for i in range(N - 1, 0, -1):
        b_struct = [i, last_elem if i == N - 1 else b_struct]
    return b_struct
