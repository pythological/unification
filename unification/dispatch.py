from functools import partial as _partial

from multipledispatch import dispatch

namespace = {}

_partial = _partial(dispatch, namespace=namespace)
