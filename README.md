# Logical Unification

[![Build Status](https://travis-ci.org/pythological/unification.svg?branch=master)](https://travis-ci.org/pythological/unification) [![Coverage Status](https://coveralls.io/repos/github/pythological/unification/badge.svg?branch=master)](https://coveralls.io/github/pythological/unification?branch=master) [![PyPI](https://img.shields.io/pypi/v/logical-unification)](https://pypi.org/project/logical-unification/)

[Logical unification](https://en.wikipedia.org/wiki/Unification_(computer_science)) in Python, extensible via dispatch.

## Installation

Using `pip`:
```bash
pip install logical-unification
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

`unification`'s current design allows for unification and reification of nested structures that would otherwise break the Python stack recursion limit.  It uses a generator-based design to "stream" the unifications and reifications.

Below are some stack vs. stream benchmarks that demonstrate how well the stream-based approach scales against the stack-based approach in terms of unifying and reifying deeply nested lists containing integers.  These benchmarks were generated from the tests in `tests/test_benchmarks.py` using CPython 3.7.3.

<details><summary>Stack vs. stream benchmarks</summary>
<p>

```python
-------------------------------------------------------------------------------- benchmark 'reify_chain size=10': 2 tests -------------------------------------------------------------------------------
Name (time in us)                   Min                 Max               Mean            StdDev             Median               IQR                Outliers  OPS (Kops/s)            Rounds  Iterations
---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
test_reify_chain_stack[10]      41.0790 (1.0)      545.1940 (3.20)     52.9087 (1.07)     9.7964 (1.04)     50.8650 (1.08)     6.4301 (8.37)      11815;10849       18.9005 (0.93)     260164           1
test_reify_chain_stream[10]     42.4410 (1.03)     170.5540 (1.0)      49.3080 (1.0)      9.3993 (1.0)      47.2400 (1.0)      0.7680 (1.0)      14962;102731       20.2807 (1.0)      278113           1
---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

------------------------------------------ benchmark 'reify_chain size=1000': 1 tests -----------------------------------------
Name (time in ms)                          Min      Max     Mean  StdDev  Median     IQR  Outliers      OPS  Rounds  Iterations
-------------------------------------------------------------------------------------------------------------------------------
test_reify_chain_stream_large[1000]     7.7722  28.2579  10.0723  2.5087  9.4899  0.3106    70;155  99.2820    1528           1
-------------------------------------------------------------------------------------------------------------------------------

------------------------------------------------------------------------- benchmark 'reify_chain size=300': 2 tests --------------------------------------------------------------------------
Name (time in ms)                   Min                Max              Mean            StdDev            Median               IQR            Outliers       OPS            Rounds  Iterations
----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
test_reify_chain_stack[300]      1.5183 (1.0)      22.1821 (1.19)     1.9826 (1.0)      1.5511 (1.16)     1.7410 (1.0)      0.0801 (1.0)       144;684  504.3878 (1.0)        7201           1
test_reify_chain_stream[300]     1.7059 (1.12)     18.6020 (1.0)      2.1237 (1.07)     1.3389 (1.0)      1.9260 (1.11)     0.1020 (1.27)      118;585  470.8745 (0.93)       6416           1
----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

--------------------------------------------------------------------------------- benchmark 'reify_chain size=35': 2 tests --------------------------------------------------------------------------------
Name (time in us)                    Min                 Max                Mean             StdDev              Median                IQR             Outliers  OPS (Kops/s)            Rounds  Iterations
-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
test_reify_chain_stream[35]     129.2780 (1.0)      868.1510 (1.02)     190.0433 (1.11)     36.2784 (1.41)     179.5690 (1.08)     21.5360 (2.30)     1535;1455        5.2620 (0.90)      26072           1
test_reify_chain_stack[35]      150.7850 (1.17)     853.7920 (1.0)      170.5166 (1.0)      25.7944 (1.0)      165.8500 (1.0)       9.3530 (1.0)      3724;5480        5.8645 (1.0)       81286           1
-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

------------------------------------------- benchmark 'reify_chain size=5000': 1 tests ------------------------------------------
Name (time in ms)                           Min      Max     Mean  StdDev   Median     IQR  Outliers      OPS  Rounds  Iterations
---------------------------------------------------------------------------------------------------------------------------------
test_reify_chain_stream_large[5000]     46.9073  86.9737  52.9724  6.6919  49.6787  3.9609     68;68  18.8778     292           1
---------------------------------------------------------------------------------------------------------------------------------

------------------------------------------------------------------------------- benchmark 'unify_chain size=10': 2 tests -------------------------------------------------------------------------------
Name (time in us)                   Min                 Max                Mean             StdDev              Median               IQR            Outliers  OPS (Kops/s)            Rounds  Iterations
--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
test_unify_chain_stream[10]     77.6280 (1.0)      307.9130 (1.0)       86.7625 (1.0)      17.5355 (1.20)      82.7525 (1.0)      1.7290 (1.0)      809;1736       11.5257 (1.0)       15524           1
test_unify_chain_stack[10]      92.9890 (1.20)     309.8770 (1.01)     104.2017 (1.20)     14.6694 (1.0)      101.0160 (1.22)     4.2368 (2.45)    3657;6651        9.5968 (0.83)      73379           1
--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

------------------------------------------- benchmark 'unify_chain size=1000': 1 tests ------------------------------------------
Name (time in ms)                           Min      Max     Mean  StdDev   Median     IQR  Outliers      OPS  Rounds  Iterations
---------------------------------------------------------------------------------------------------------------------------------
test_unify_chain_stream_large[1000]     27.3518  65.5924  31.1374  4.2563  29.5148  3.5286     38;35  32.1158     496           1
---------------------------------------------------------------------------------------------------------------------------------

------------------------------------------------------------------------- benchmark 'unify_chain size=300': 2 tests --------------------------------------------------------------------------
Name (time in ms)                   Min                Max              Mean            StdDev            Median               IQR            Outliers       OPS            Rounds  Iterations
----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
test_unify_chain_stream[300]     3.6957 (1.0)      13.1876 (1.0)      4.4439 (1.0)      1.0719 (1.42)     4.2080 (1.0)      0.2410 (1.67)        51;95  225.0298 (1.0)        1114           1
test_unify_chain_stack[300]      4.2952 (1.16)     13.4294 (1.02)     4.7732 (1.07)     0.7555 (1.0)      4.6623 (1.11)     0.1446 (1.0)        36;136  209.5024 (0.93)       2911           1
----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

--------------------------------------------------------------------------------- benchmark 'unify_chain size=35': 2 tests ---------------------------------------------------------------------------------
Name (time in us)                    Min                   Max                Mean             StdDev              Median                IQR            Outliers  OPS (Kops/s)            Rounds  Iterations
------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
test_unify_chain_stream[35]     285.6880 (1.0)        934.9690 (1.0)      324.5402 (1.0)      40.8338 (1.0)      319.8520 (1.0)      20.4375 (1.0)      962;1159        3.0813 (1.0)       24331           1
test_unify_chain_stack[35]      345.2770 (1.21)     1,088.3650 (1.16)     407.9067 (1.26)     52.2263 (1.28)     396.6640 (1.24)     20.6560 (1.01)    2054;3027        2.4515 (0.80)      37594           1
------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

--------------------------------------------- benchmark 'unify_chain size=5000': 1 tests ---------------------------------------------
Name (time in ms)                            Min       Max      Mean   StdDev    Median      IQR  Outliers     OPS  Rounds  Iterations
--------------------------------------------------------------------------------------------------------------------------------------
test_unify_chain_stream_large[5000]     555.2733  754.9897  605.4949  50.6124  591.1251  61.4030       2;2  1.6515      26           1
--------------------------------------------------------------------------------------------------------------------------------------

Legend:
  Outliers: 1 Standard Deviation from Mean; 1.5 IQR (InterQuartile Range) from 1st Quartile and 3rd Quartile.
  OPS: Operations Per Second, computed as 1 / Mean
```

</p>
</details>

## About

This project is a fork of [`unification`](https://github.com/mrocklin/unification/).

## Development

Install the development dependencies:

```bash
$ pip install -r requirements.txt
```

Set up `pre-commit` hooks:

```bash
$ pre-commit install --install-hooks
```
