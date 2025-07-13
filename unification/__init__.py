from importlib.metadata import version

from .core import assoc, reify, unify
from .more import unifiable
from .variable import Var, isvar, var, variables, vars

__version__ = version("logical-unification")
