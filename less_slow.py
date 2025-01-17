#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
less_slow.py
============

Micro-benchmarks to build a performance-first mindset in Python.

This project is a spiritual brother to `less_slow.cpp` for C++20,
and `less_slow.rs` for Rust. Unlike low-level systems languages,
Python is a high-level with significant runtime overheads, and
no obvious way to predict the performance of code.

Moreover, the performance of different language and library components
can vary significantly between consecutive Python versions. That's
true for both small numeric operations, and high-level abstractions,
like iterators, generators, and async code.
"""
import pytest
import numpy as np

# region: Numerics

# region: Accuracy vs Efficiency of Standard Libraries

# ? Numerical computing is a core subject in high-performance computing (HPC)
# ? research and graduate studies, yet its foundational concepts are more
# ? accessible than they seem. Let's start with one of the most basic
# ? operations — computing the __sine__ of a number.

import math


def f64_sine_math(x: float) -> float:
    return math.sin(x)


def f64_sine_numpy(x: float) -> float:
    return np.sin(x)


# ? NumPy is the de-facto standard for numerical computing in Python, and
# ? it's known for its speed and simplicity. However, it's not always the
# ? fastest option for simple operations like sine, cosine, or exponentials.
# ?
# ? NumPy lacks hot-path optimizations if the input is a single scalar value,
# ? and it's often slower than the standard math library for such cases:
# ?
# ?  - math.sin:  620us
# ?  - np.sin:    4200us
# ?
# ? NumPy, of course, becomes much faster when the input is a large array,
# ? as opposed to a single scalar value.
# ?
# ? When absolute bit-accuracy is not required, it's often possible to
# ? approximate mathematical functions using simpler, faster operations.
# ? For example, the Maclaurin series for sine:
# ?
# ?   sin(x) ≈ x - (x^3)/3! + (x^5)/5! - (x^7)/7! + ...
# ?
# ? is a simple polynomial approximation that converges quickly for small x.
# ? Both can be implemented in Python, NumPy, or Numba JIT, and benchmarked.


def f64_sine_math_maclaurin(x: float) -> float:
    return x - math.pow(x, 3) / 6.0 + math.pow(x, 5) / 120.0


def f64_sine_numpy_maclaurin(x: float) -> float:
    return x - np.pow(x, 3) / 6.0 + np.pow(x, 5) / 120.0


def f64_sine_maclaurin_powless(x: float) -> float:
    x2 = x * x
    x3 = x2 * x
    x5 = x3 * x2
    return x - (x3 / 6.0) + (x5 / 120.0)


# ? Let's define a couple of helper functions to run benchmarks on these functions,
# ? and compare their performance on 10k random floats in [0, 2π]. We can also
# ? use Numba JIT to compile these functions to machine code, and compare the
# ? performance of the JIT-compiled functions with the standard Python functions.

numba_installed = False
try:
    import numba

    numba_installed = True
except ImportError:
    pass  # skip if numba is not installed


def _f64_sine_run_benchmark_on_each(benchmark, sin_fn):
    """Applies `sin_fn` to 10k random floats in [0, 2π] individually."""
    inputs = np.random.rand(10_000)  # 10k random floats
    inputs = inputs.astype(np.float64) * 2 * np.pi  # [0, 2π]

    def call_sin_on_all():
        for x in inputs:
            sin_fn(x)

    result = benchmark(call_sin_on_all)
    return result


def _f64_sine_run_benchmark_on_all(benchmark, sin_fn):
    """Applies `sin_fn` to 10k random floats in [0, 2π] all at once."""
    inputs = np.random.rand(10_000)  # 10k random floats
    inputs = inputs.astype(np.float64) * 2 * np.pi  # [0, 2π]
    call_sin_on_all = lambda: sin_fn(inputs)  # noqa: E731
    result = benchmark(call_sin_on_all)
    return result


@pytest.mark.benchmark(group="sin")
def test_f64_sine_math(benchmark):
    _f64_sine_run_benchmark_on_each(benchmark, f64_sine_math)


@pytest.mark.benchmark(group="sin")
def test_f64_sine_numpy(benchmark):
    _f64_sine_run_benchmark_on_each(benchmark, f64_sine_numpy)


@pytest.mark.benchmark(group="sin")
def test_f64_sine_maclaurin_math(benchmark):
    _f64_sine_run_benchmark_on_each(benchmark, f64_sine_math_maclaurin)


@pytest.mark.benchmark(group="sin")
def test_f64_sine_maclaurin_numpy(benchmark):
    _f64_sine_run_benchmark_on_each(benchmark, f64_sine_numpy_maclaurin)


@pytest.mark.benchmark(group="sin")
def test_f64_sine_maclaurin_powless(benchmark):
    _f64_sine_run_benchmark_on_each(benchmark, f64_sine_maclaurin_powless)


@pytest.mark.skipif(not numba_installed, reason="Numba not installed")
@pytest.mark.benchmark(group="sin")
def test_f64_sine_jit(benchmark):
    sin_fn = numba.njit(f64_sine_math)
    sin_fn(0.0)  # trigger compilation
    _f64_sine_run_benchmark_on_each(benchmark, sin_fn)


@pytest.mark.skipif(not numba_installed, reason="Numba not installed")
@pytest.mark.benchmark(group="sin")
def test_f64_sine_maclaurin_jit(benchmark):
    sin_fn = numba.njit(f64_sine_math_maclaurin)
    sin_fn(0.0)  # trigger compilation
    _f64_sine_run_benchmark_on_each(benchmark, sin_fn)


@pytest.mark.skipif(not numba_installed, reason="Numba not installed")
@pytest.mark.benchmark(group="sin")
def test_f64_sine_maclaurin_powless_jit(benchmark):
    sin_fn = numba.njit(f64_sine_maclaurin_powless)
    sin_fn(0.0)  # trigger compilation
    _f64_sine_run_benchmark_on_each(benchmark, sin_fn)


@pytest.mark.benchmark(group="sin")
def test_f64_sines_numpy(benchmark):
    _f64_sine_run_benchmark_on_all(benchmark, f64_sine_numpy)


@pytest.mark.benchmark(group="sin")
def test_f64_sines_maclaurin_numpy(benchmark):
    _f64_sine_run_benchmark_on_all(benchmark, f64_sine_numpy_maclaurin)


@pytest.mark.benchmark(group="sin")
def test_f64_sines_maclaurin_powless(benchmark):
    _f64_sine_run_benchmark_on_all(benchmark, f64_sine_maclaurin_powless)


# ? The results are somewhat shocking!
# ?
# ? `f64_sine_maclaurin_powless` and `test_f64_sine_maclaurin_numpy` are
# ? both the fastest and one of the slowest implementations, depending on
# ? the input shape - scalar or array: 29us vs 2610us.
# ?
# ? This little benchmark is enough to understand, why Python is broadly
# ? considered a "glue" language for various native languages and pre-compiled
# ? libraries for batch/bulk processing.

# endregion: Accuracy vs Efficiency of Standard Libraries

# endregion: Numerics

# region: Pipelines and Abstractions

# ? Designing efficient micro-kernels is hard, but composing them into
# ? high-level pipelines without losing performance is just as difficult.
# ?
# ? Consider a hypothetical numeric processing pipeline:
# ?
# ?   1. Generate all integers in a given range (e.g., [1, 49]).
# ?   2. Filter out integers that are perfect squares.
# ?   3. Expand each remaining number into its prime factors.
# ?   4. Sum all prime factors from the filtered numbers.
# ?
# ? We'll explore four implementations of this pipeline:
# ?
# ?  - __Callback-based__ pipeline using lambdas,
# ?  - __Generators__, `yield`-ing values at each stage,
# ?  - __Range-based__ pipeline using a custom `PrimeFactors` iterator,
# ?  - __Polymorphic__ pipeline with a shared base class,
# ?  - __Async Generators__ with `async for` loops.

PIPE_START = 3
PIPE_END = 49


def is_power_of_two(x: int) -> bool:
    """Return True if x is a power of two, False otherwise."""
    return x > 0 and (x & (x - 1)) == 0


def is_power_of_three(x: int) -> bool:
    """Return True if x is a power of three, False otherwise."""
    MAX_POWER_OF_THREE = 12157665459056928801
    return x > 0 and (MAX_POWER_OF_THREE % x == 0)


# region: Callbacks

from typing import Callable, Tuple  # noqa: E402


def prime_factors_callback(number: int, callback: Callable[[int], None]) -> None:
    """Factorize `number` into primes, invoking `callback(factor)` for each factor."""
    factor = 2
    while number > 1:
        if number % factor == 0:
            callback(factor)
            number //= factor
        else:
            factor += 1 if factor == 2 else 2


def pipeline_callbacks() -> Tuple[int, int]:
    sum_factors = 0
    count = 0

    def record_factor(factor: int) -> None:
        nonlocal sum_factors, count
        sum_factors += factor
        count += 1

    for value in range(PIPE_START, PIPE_END + 1):
        if not is_power_of_two(value) and not is_power_of_three(value):
            prime_factors_callback(value, record_factor)

    return sum_factors, count


# endregion: Callbacks

# region: Generators
from typing import Generator  # noqa: E402
from itertools import chain  # noqa: E402
from functools import reduce  # noqa: E402


def prime_factors_generator(number: int) -> Generator[int, None, None]:
    """Yield prime factors of `number` one by one, lazily."""
    factor = 2
    while number > 1:
        if number % factor == 0:
            yield factor
            number //= factor
        else:
            factor += 1 if factor == 2 else 2


def pipeline_generators() -> Tuple[int, int]:

    values = range(PIPE_START, PIPE_END + 1)
    values = filter(lambda x: not is_power_of_two(x), values)
    values = filter(lambda x: not is_power_of_three(x), values)

    values_factors = map(prime_factors_generator, values)
    all_factors = chain.from_iterable(values_factors)

    # Use `reduce` to do a single-pass accumulation of (sum, count)
    sum_factors, count = reduce(
        lambda acc, factor: (acc[0] + factor, acc[1] + 1),
        all_factors,
        (0, 0),
    )
    return sum_factors, count


# endregion: Generators

# region: Iterators


class PrimeFactors:
    """An iterator to lazily compute the prime factors of a single number."""

    def __init__(self, number: int) -> None:
        self.number = number
        self.factor = 2

    def __iter__(self) -> "PrimeFactors":
        return self

    def __next__(self) -> int:
        while self.number > 1:
            if self.number % self.factor == 0:
                self.number //= self.factor
                return self.factor
            self.factor += 1 if self.factor == 2 else 2

        raise StopIteration


def pipeline_iterators() -> Tuple[int, int]:
    sum_factors = 0
    count = 0

    for value in range(PIPE_START, PIPE_END + 1):
        if not is_power_of_two(value) and not is_power_of_three(value):
            for factor in PrimeFactors(value):
                sum_factors += factor
                count += 1

    return sum_factors, count


# endregion: Iterators

# region: Polymorphic
from typing import List  # noqa: E402
from abc import ABC, abstractmethod  # noqa: E402


class PipelineStage(ABC):
    """Base pipeline stage, mimicking a C++-style virtual interface."""

    @abstractmethod
    def process(self, data: List[int]) -> None: ...


class ForRangeStage(PipelineStage):
    """Stage that appends [start..end] to `data`."""

    def __init__(self, start: int, end: int) -> None:
        self.start = start
        self.end = end

    def process(self, data: List[int]) -> None:
        data.clear()
        data.extend(range(self.start, self.end + 1))


class FilterStage(PipelineStage):
    """Stage that filters out values in-place using a predicate."""

    def __init__(self, predicate: Callable[[int], bool]) -> None:
        self.predicate = predicate

    def process(self, data: List[int]) -> None:
        data[:] = [x for x in data if not self.predicate(x)]


class PrimeFactorsStage(PipelineStage):
    """Stage that expands each value into prime factors, storing them back into data."""

    def process(self, data: List[int]) -> None:
        result = []
        for val in data:
            # Use the generator-based prime factors
            result.extend(PrimeFactors(val))
        data[:] = result


def pipeline_dynamic_dispatch() -> Tuple[int, int]:
    pipeline_stages = [
        ForRangeStage(PIPE_START, PIPE_END),
        FilterStage(is_power_of_two),
        FilterStage(is_power_of_three),
        PrimeFactorsStage(),
    ]

    data: List[int] = []
    for stage in pipeline_stages:
        stage.process(data)

    return sum(data), len(data)


# endregion: Polymorphic

# region: Async Generators

import asyncio  # noqa: E402
from typing import AsyncGenerator  # noqa: E402


async def for_range_async(start: int, end: int) -> AsyncGenerator[int, None]:
    """Async generator that yields [start..end]."""
    for value in range(start, end + 1):
        yield value


async def filter_async(generator, predicate: Callable[[int], bool]):
    """Async generator that yields values from `generator` that do NOT satisfy `predicate`."""
    async for value in generator:
        if not predicate(value):
            yield value


async def prime_factors_async(generator):
    """Async generator that yields all prime factors of the values coming from `generator`."""
    async for val in generator:
        for factor in prime_factors_generator(val):
            yield factor


async def pipeline_async() -> Tuple[int, int]:
    values = for_range_async(PIPE_START, PIPE_END)
    values = filter_async(values, is_power_of_two)
    values = filter_async(values, is_power_of_three)
    values = prime_factors_async(values)

    sum_factors = 0
    count = 0
    async for factor in values:
        sum_factors += factor
        count += 1

    return sum_factors, count


# endregion: Async Generators

PIPE_EXPECTED_SUM = 645  # sum of prime factors from the final data
PIPE_EXPECTED_COUNT = 84  # total prime factors from the final data


@pytest.mark.benchmark(group="pipelines")
def test_pipeline_callbacks(benchmark):
    result = benchmark(pipeline_callbacks)
    assert result == (PIPE_EXPECTED_SUM, PIPE_EXPECTED_COUNT)


@pytest.mark.benchmark(group="pipelines")
def test_pipeline_generators(benchmark):
    result = benchmark(pipeline_generators)
    assert result == (PIPE_EXPECTED_SUM, PIPE_EXPECTED_COUNT)


@pytest.mark.benchmark(group="pipelines")
def test_pipeline_iterators(benchmark):
    result = benchmark(pipeline_iterators)
    assert result == (PIPE_EXPECTED_SUM, PIPE_EXPECTED_COUNT)


@pytest.mark.benchmark(group="pipelines")
def test_pipeline_dynamic_dispatch(benchmark):
    """Benchmark the dynamic-dispatch (trait-object) pipeline."""
    result = benchmark(pipeline_dynamic_dispatch)
    assert result == (PIPE_EXPECTED_SUM, PIPE_EXPECTED_COUNT)


@pytest.mark.benchmark(group="pipelines")
def test_pipeline_async(benchmark):
    """Benchmark the async-generators pipeline."""
    run_async = lambda: asyncio.run(pipeline_async())  # noqa: E731
    result = benchmark(run_async)
    assert result == (PIPE_EXPECTED_SUM, PIPE_EXPECTED_COUNT)


# ? The results, as expected, are much slower than in similar pipelines
# ? written in C++ or Rust. However, the iterators, don't seem like a
# ? good design choice in Python!
# ?
# ?  - Callbacks: 16.8ms
# ?  - Generators: 23.3ms
# ?  - Iterators: 31.8ms
# ?  - Polymorphic: 33.2ms
# ?  - Async: 97.0ms
# ?
# ? For comparison, a fast C++/Rust implementation would take 200ns,
# ? or __84x__ faster than the fastest Python implementation here.

# endregion: Pipelines and Abstractions

# region: Structures, Tuples, ADTs, AOS, SOA

# region: Composite Structs

# ? Python has many ways of defining composite objects. The most common
# ? are tuples, dictionaries, named-tuples, dataclasses, and classes.
# ? Let's compare them by assembling a simple composite of numeric values.
# ?
# ? We prefer `float` and `bool` fields as the most predictable Python types,
# ? as the `int` integers in Python involve a lot of additional logic for
# ? arbitrary-precision arithmetic, which can affect the latencies.

from dataclasses import dataclass  # noqa: E402
from collections import namedtuple  # noqa: E402


@pytest.mark.benchmark(group="composite-structs")
def test_structs_dict(benchmark):
    def kernel():
        point = {"x": 1.0, "y": 2.0, "flag": True}
        return point["x"] + point["y"]

    result = benchmark(kernel)
    assert result == 3.0


class PointClass:
    def __init__(self, x: float, y: float, flag: bool) -> None:
        self.x = x
        self.y = y
        self.flag = flag


@pytest.mark.benchmark(group="composite-structs")
def test_structs_class(benchmark):
    def kernel():
        point = PointClass(1.0, 2.0, True)
        return point.x + point.y

    result = benchmark(kernel)
    assert result == 3.0


@dataclass
class PointDataclass:
    x: float
    y: float
    flag: bool


@pytest.mark.benchmark(group="composite-structs")
def test_structs_dataclass(benchmark):
    def kernel():
        point = PointDataclass(1.0, 2.0, True)
        return point.x + point.y

    result = benchmark(kernel)
    assert result == 3.0


PointNamedtuple = namedtuple("PointNamedtuple", ["x", "y", "flag"])


@pytest.mark.benchmark(group="composite-structs")
def test_structs_namedtuple(benchmark):
    def kernel():
        point = PointNamedtuple(1.0, 2.0, True)
        return point.x + point.y

    result = benchmark(kernel)
    assert result == 3.0


@pytest.mark.benchmark(group="composite-structs")
def test_structs_tuple_indexing(benchmark):
    def kernel():
        point = (1.0, 2.0, True)
        return point[0] + point[1]

    result = benchmark(kernel)
    assert result == 3.0


@pytest.mark.benchmark(group="composite-structs")
def test_structs_tuple_unpacking(benchmark):
    def kernel():
        x, y, _ = (1.0, 2.0, True)
        return x + y

    result = benchmark(kernel)
    assert result == 3.0


# ? Interestingly, the `namedtuple`, that is often believed to be a
# ? performance-oriented choice, is 50% slower than both `dataclass` and
# ? the custom class... which are in turn slower than a simple `dict`
# ? with the same string fields!
# ?
# ? - Tuple: 47ns (indexing) vs 43ns (unpacking)
# ? - Dict:  101ns
# ? - Dataclass: 122ns
# ? - Class: 125ns
# ? - Namedtuple: 183ns

# endregion: Composite Structs

# region: Heterogenous Collections

# ? Python is a dynamically typed language, and it allows mixing different
# ? types in a single collection. However, the performance of such collections
# ? can vary significantly, depending on the types and their distribution.


# endregion: Heterogenous Collections

# region: Tables and Arrays

import pandas as pd  # noqa: E402
import pyarrow as pa  # noqa: E402

# endregion: Tables and Arrays

# endregion: Structures, Tuples, ADTs, AOS, SOA

# region: Exceptions, Backups, Logging

# region: Errors

# ?  In the real world, control-flow gets messy, as different methods will
# ?  break in different places. Let's imagine a system, that:
# ?
# ?  - Reads an integer from a text file.
# ?  - Increments it.
# ?  - Saves it back to the text file.
# ?
# ?  As soon as we start dealing with "external devices", as opposed to the CPU itself,
# ?  failures become regular. The file may not exist, the integer may not be a number,
# ?  the file may be read-only, the disk may be full, the file may be locked, etc.

fail_period_read_integer = 6
fail_period_convert_to_integer = 11
fail_period_next_string = 17
fail_period_write_back = 23


def read_integer_from_file_or_raise(file: str, iteration: int) -> str:
    # Simulate a file-read failure
    if iteration % fail_period_read_integer == 0:
        raise RuntimeError(f"File read failed at iteration {iteration}")
    # Simulate a bad string that cannot be converted
    if iteration % fail_period_convert_to_integer == 0:
        return "abc"
    # Otherwise, pretend the file contains "1"
    return "1"


def string_to_integer_or_raise(value: str, iteration: int) -> int:
    try:
        return int(value)
    except ValueError:
        raise ValueError(f"Conversion failed at iteration {iteration}")


def integer_to_next_string_or_raise(value: int, iteration: int) -> str:
    if iteration % fail_period_next_string == 0:
        raise RuntimeError(f"Increment failed at iteration {iteration}")
    return str(value + 1)


def write_to_file_or_raise(file: str, value: str, iteration: int) -> None:
    if iteration % fail_period_write_back == 0:
        raise RuntimeError(f"File write failed at iteration {iteration}")
    # Otherwise, success (do nothing).


def increment_file_or_raise(file: str, iteration: int) -> None:
    read_value = read_integer_from_file_or_raise(file, iteration)
    int_value = string_to_integer_or_raise(read_value, iteration)
    next_value = integer_to_next_string_or_raise(int_value, iteration)
    write_to_file_or_raise(file, next_value, iteration)


@pytest.mark.benchmark(group="errors")
def test_errors_raise(benchmark):
    def runner():
        file_path = "test.txt"
        iteration = 0
        for _ in range(1_000):
            iteration += 1
            try:
                increment_file_or_raise(file_path, iteration)
            except Exception:
                pass

    benchmark(runner)


# ? Now let’s define a simple status-based approach, akin to `std::expected`
# ? or a custom status enum in C++. It's not a common pattern in Python.

from enum import Enum, auto  # noqa: E402


class Status(Enum):
    SUCCESS = auto()
    READ_FAILED = auto()
    CONVERT_FAILED = auto()
    INCREMENT_FAILED = auto()
    WRITE_FAILED = auto()


class Expected:
    """
    A simple 'expected' type in Python.
    - If success, `error` is None and `value` holds the data.
    - If error, `error` is a Status, and `value` may be None or partial data.
    """

    __slots__ = ("value", "error")

    def __init__(self, value=None, error: Status = None):
        self.value = value
        self.error = error

    def is_ok(self) -> bool:
        return self.error is None


def read_integer_from_file_expected(file: str, iteration: int) -> Expected:
    if iteration % fail_period_read_integer == 0:
        return Expected(error=Status.READ_FAILED)
    if iteration % fail_period_convert_to_integer == 0:
        # Return "abc" with success => which triggers the "convert failed" later
        return Expected(value="abc", error=None)
    # Otherwise, pretend the file contains "1"
    return Expected(value="1", error=None)


def string_to_integer_expected(value: str, iteration: int) -> Expected:
    if not value.isnumeric():
        return Expected(error=Status.CONVERT_FAILED)
    return Expected(value=int(value), error=None)


def integer_to_next_string_expected(value: int, iteration: int) -> Expected:
    if iteration % fail_period_next_string == 0:
        return Expected(error=Status.INCREMENT_FAILED)
    return Expected(value=str(value + 1), error=None)


def write_to_file_expected(file: str, value: str, iteration: int) -> Status:
    if iteration % fail_period_write_back == 0:
        return Status.WRITE_FAILED
    return Status.SUCCESS


def increment_file_expected(file: str, iteration: int) -> Status:
    res_read = read_integer_from_file_expected(file, iteration)
    if not res_read.is_ok():
        return res_read.error
    res_int = string_to_integer_expected(res_read.value, iteration)
    if not res_int.is_ok():
        return res_int.error
    res_incr = integer_to_next_string_expected(res_int.value, iteration)
    if not res_incr.is_ok():
        return res_incr.error

    return write_to_file_expected(file, res_incr.value, iteration)


@pytest.mark.benchmark(group="errors")
def test_errors_expected(benchmark):
    def runner():
        file_path = "test.txt"
        iteration = 0
        for _ in range(1_000):
            iteration += 1
            increment_file_expected(file_path, iteration)

    benchmark(runner)


# ? As we know, classes and `__slots__` may add a noticeable overhead.
# ? So let's explore the less common Go-style approach of returning tuples
# ? and unpacking them on the fly.

StatusCode = int
STATUS_SUCCESS = 0
STATUS_READ_FAILED = 1
STATUS_CONVERT_FAILED = 2
STATUS_INCREMENT_FAILED = 3
STATUS_WRITE_FAILED = 4


def read_integer_from_file_status(file: str, iteration: int) -> Tuple[str, StatusCode]:
    if iteration % fail_period_read_integer == 0:
        return None, STATUS_READ_FAILED
    if iteration % fail_period_convert_to_integer == 0:
        # Return "abc" with success => which triggers the "convert failed" later
        return "abc", STATUS_SUCCESS
    # Otherwise, pretend the file contains "1"
    return "1", STATUS_SUCCESS


def string_to_integer_status(value: str, iteration: int) -> Tuple[int, StatusCode]:
    if not value.isnumeric():
        return None, STATUS_CONVERT_FAILED
    return int(value), STATUS_SUCCESS


def integer_to_next_string_status(value: int, iteration: int) -> Tuple[str, StatusCode]:
    if iteration % fail_period_next_string == 0:
        return None, STATUS_INCREMENT_FAILED
    return str(value + 1), STATUS_SUCCESS


def write_to_file_status(file: str, value: str, iteration: int) -> Status:
    if iteration % fail_period_write_back == 0:
        return STATUS_WRITE_FAILED
    return STATUS_SUCCESS


def increment_file_status(file: str, iteration: int) -> Status:
    read_value, read_status = read_integer_from_file_status(file, iteration)
    if read_status != STATUS_SUCCESS:
        return read_status
    int_value, int_status = string_to_integer_status(read_value, iteration)
    if int_status != STATUS_SUCCESS:
        return int_status
    next_value, next_status = integer_to_next_string_status(int_value, iteration)
    if next_status != STATUS_SUCCESS:
        return next_status
    write_status = write_to_file_status(file, next_value, iteration)
    return write_status


@pytest.mark.benchmark(group="errors")
def test_errors_status(benchmark):
    def runner():
        file_path = "test.txt"
        iteration = 0
        for _ in range(1_000):
            iteration += 1
            increment_file_status(file_path, iteration)

    benchmark(runner)


# ? The results are quite interesting! Raising exceptions beats the more
# ? explicit `Expected` approach by 2x, but loses to tuple-based status
# ? codes by 50%.
# ?
# ? - Raise: 329us
# ? - Expected: 660us
# ? - Status: 236us
# ?
# ? That difference could grow further we get a `noexcept`-like mechanism
# ? to annotate functions that never raise exceptions, and need no stack
# ? tracing logic: https://github.com/python/typing/issues/604
# ?
# ? Stick to `tuple`-s with unpacking for the best performance!

# endregion: Errors

# regions: Logs

# endregion: Logs

# endregion: Exceptions, Backups, Logging

# region: Dynamic Code

# region: Reflection, Inspection

import inspect  # noqa: E402

# endregion: Reflection, Inspection

# region: Evaluating Strings

# endregion: Evaluating Strings

# endregion: Dynamic Code

# region: External Systems, IO, Networking


# endregion: External Systems, IO, Networking
