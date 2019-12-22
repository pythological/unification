# Logical Unification

[![Build Status](https://travis-ci.org/pythological/unification.svg?branch=master)](https://travis-ci.org/pythological/unification) [![Coverage Status](https://coveralls.io/repos/github/pythological/unification/badge.svg?branch=master)](https://coveralls.io/github/pythological/unification?branch=master) [![PyPI](https://img.shields.io/pypi/v/logical-unification)](https://pypi.org/project/logical-unification/)

Logical [`unification`](https://en.wikipedia.org/wiki/Unification_(computer_science)) in Python, extensible via dispatch.

## Examples

`unification` has built-in support for most Python data types:

```python
>>> from unification import *
>>> unify(1, 1)
{}
>>> unify(1, 2)
False
>>> x = var('x')
>>> unify((1, x), (1, 2))
{~x: 2}
>>> unify((x, x), (1, 2))
False
```

Custom classes can be made "unifiable" with the `unifiable` decorator:

```python
@unifiable
class Account(object):
    def __init__(self, id, name, balance):
        self.id = id
        self.name = name
        self.balance = balance

>>> data = [Account(1, 'Alice', 100),
            Account(2, 'Bob', 0),
            Account(2, 'Charlie', 0),
            Account(2, 'Denis', 400),
            Account(2, 'Edith', 500)]
>>> id, name, balance = var('id'), var('name'), var('balance')
>>> [unify(Account(id, name, balance), acct) for acct in data]
[{~name: 'Alice', ~balance: 100, ~id: 1},
{~name: 'Bob', ~balance: 0, ~id: 2},
{~name: 'Charlie', ~balance: 0, ~id: 2},
{~name: 'Denis', ~balance: 400, ~id: 2},
{~name: 'Edith', ~balance: 500, ~id: 2}]
>>> [unify(Account(id, name, 0), acct) for acct in data]
[False,
{~name: 'Bob', ~id: 2},
{~name: 'Charlie', ~id: 2},
False,
False]
```

`unification` also supports function dispatch through pattern matching:

```python
>> from unification.match import *
>>> n = var('n')

@match(0)
def fib(n):
    return 0


@match(1)
def fib(n):
    return 1


@match(n)
def fib(n):
    return fib(n - 1) + fib(n - 2)

>>> map(fib, [0, 1, 2, 3, 4, 5, 6, 7, 8, 0])
[0, 1, 1, 2, 3, 5, 8, 13, 21, 34]
```

The pattern matching can be fairly complex:

```python
>> name, amount = var('name'), var('amount')

@match({'status': 200, 'data': {'name': name, 'credit': amount}})
def respond(name, amount):
    balance[name] +=  amount


@match({'status': 200, 'data': {'name': name, 'debit': amount}})
def respond(name, amount):
    balance[name] -= amount


@match({'status': 404})
def respond():
    print("Bad Request")

```

See the full example in the [examples directory](https://github.com/pythological/unification#examples).


## Performance and Reliability

Unification stresses extensibility over performance, preliminary benchmarks show that this is 2-5x slower than straight tuple-based unification.

`unification`'s approach is reliable; although one caveat is set unification, which is challenging to do in general.  It should work well in moderately complex cases, but it may break down under very complex ones.

## Installation

Using `pip`:
```bash
pip install python-unification
```

To install from source:
```bash
git clone git@github.com:pythological/unification.git
cd unification
pip install -r requirements.txt
```

Tests can be run with the provided `Makefile`:
```bash
make check
```

## About

This project is a fork of [`unification`](https://github.com/mrocklin/unification/).
