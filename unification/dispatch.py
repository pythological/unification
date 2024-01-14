from functools import partial

from multipledispatch import dispatch

namespace = {}

dispatch = partial(dispatch, namespace=namespace)
