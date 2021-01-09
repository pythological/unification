import ast
from collections.abc import Mapping

from unification import var
from unification.core import _reify, _unify, reify, stream_eval, unify
from unification.more import _reify_object, _unify_object, unifiable


class Foo(object):
    def __init__(self, a, b):
        self.a = a
        self.b = b

    def __eq__(self, other):
        return type(self) == type(other) and (self.a, self.b) == (other.a, other.b)


class Bar(object):
    def __init__(self, c):
        self.c = c

    def __eq__(self, other):
        return type(self) == type(other) and self.c == other.c


def test_unify_object():
    x = var()
    assert stream_eval(_unify_object(Foo(1, 2), Foo(1, 2), {})) == {}
    assert stream_eval(_unify_object(Foo(1, 2), Foo(1, 3), {})) is False
    assert stream_eval(_unify_object(Foo(1, 2), Foo(1, x), {})) == {x: 2}


def test_unify_nonstandard_object():
    _unify.add((ast.AST, ast.AST, Mapping), _unify_object)
    x = var()
    assert unify(ast.Num(n=1), ast.Num(n=1), {}) == {}
    assert unify(ast.Num(n=1), ast.Num(n=2), {}) is False
    assert unify(ast.Num(n=1), ast.Num(n=x), {}) == {x: 1}


def test_reify_object():
    x = var()
    obj = stream_eval(_reify_object(Foo(1, x), {x: 4}))
    assert obj.a == 1
    assert obj.b == 4

    f = Foo(1, 2)
    assert stream_eval(_reify_object(f, {})) is f


def test_reify_nonstandard_object():
    _reify.add((ast.AST, Mapping), _reify_object)
    x = var()
    assert reify(ast.Num(n=1), {}).n == 1
    assert reify(ast.Num(n=x), {}).n == x
    assert reify(ast.Num(n=x), {x: 2}).n == 2


def test_reify_slots():
    class SlotsObject(object):
        __slots__ = ["myattr"]

        def __init__(self, myattr):
            self.myattr = myattr

        def __eq__(self, other):
            return type(self) == type(other) and self.myattr == other.myattr

    x = var()
    s = {x: 1}
    e = SlotsObject(x)
    assert stream_eval(_reify_object(e, s)) == SlotsObject(1)
    assert stream_eval(_reify_object(SlotsObject(1), s)) == SlotsObject(1)


def test_objects_full():
    _unify.add((Foo, Foo, Mapping), _unify_object)
    _unify.add((Bar, Bar, Mapping), _unify_object)
    _reify.add((Foo, Mapping), _reify_object)
    _reify.add((Bar, Mapping), _reify_object)

    x, y = var(), var()
    assert unify(Foo(1, 2), Bar(1), {}) is False
    assert unify(Foo(1, Bar(2)), Foo(1, Bar(x)), {}) == {x: 2}
    assert reify(Foo(x, Bar(Foo(y, 3))), {x: 1, y: 2}) == Foo(1, Bar(Foo(2, 3)))

    class SubFoo(Foo):
        pass

    assert unify(Foo(1, 2), SubFoo(1, 2), {}) is False


@unifiable
class A(object):
    def __init__(self, a, b):
        self.a = a
        self.b = b

    def __eq__(self, other):
        return type(self) == type(other) and self.__dict__ == other.__dict__


def test_unifiable_dict():
    x = var()
    f = A(1, 2)
    g = A(1, x)
    assert unify(f, g, {}) == {x: 2}
    assert reify(g, {x: 2}) == f


@unifiable
class Aslot(object):
    __slots__ = ("a", "b")

    def __init__(self, a, b):
        self.a = a
        self.b = b

    def __eq__(self, other):
        return type(self) == type(other) and all(
            a == b for a, b in zip(self.__slots__, other.__slots__)
        )


def test_unifiable_slots():
    x = var()
    f = Aslot(1, 2)
    g = Aslot(1, x)
    assert unify(f, g, {}) == {x: 2}
    assert reify(g, {x: 2}) == f
