from .core import unify, reify
from .more import unifiable
from .variable import var, isvar, vars, variables, Var

from ._version import get_versions

__version__ = get_versions()["version"]
del get_versions
