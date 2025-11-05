from datetime import timedelta, datetime
from abc import ABC, abstractmethod
from typing import Dict, Any
import numpy

from dataclasses import dataclass
from .test_functions import (sphere, rastrigin, ackley,
                             rosenbrock, griewank, schwefel,
                             levy, michalewicz, zakharov,
                             dixonprice, st)


@dataclass
class Result:
    test_function: str
    success_percent: float
    calls: float
    input_args: Dict[str, Any]
    iterations: int
    avg_time: str
    avg_iterations: float


class BaseBenchMark(ABC):

    method_class: type = None
    start_method_name: str = None
    method_kwargs: dict = None
    test_function: callable = None
    test_function_name: str = None
    function_attr: str = None

    def __init__(self, method_class: type, start_method_name: str,
                 method_kwargs: dict, x_min: list, x_max: list,
                 n: int = 2, iterations: int = 100,
                 x_eps=0.001, function_attr: str = 'f', x_min_argument='x_min',
                 x_max_argument='x_max'):
        self.method_class = method_class
        self.start_method_name = start_method_name
        self.method_kwargs = method_kwargs
        self.function_attr = function_attr
        self.x_min = x_min
        self.x_max = x_max
        self.x_min_argument = x_min_argument
        self.x_max_argument = x_max_argument
        self.method = self.method_class(
            **self.method_kwargs,
            **{
                self.function_attr: self.test_function,
                self.x_min_argument: self.x_min,
                self.x_max_argument: self.x_max
            },
        )
        self.n = n
        self.iterations = iterations
        self.x_eps = x_eps

    def __call__(self) -> Result:
        for attr in {'calls', 'reset'}:
            if not hasattr(self.test_function, attr):
                raise AttributeError(f"Отсутствует обязательный атрибут у тестовой функции: {attr}")
        successes = 0
        calls_count = 0
        iterations_count = 0
        sum_timedelta = timedelta(0)
        for i in range(self.iterations):
            t = datetime.now()
            res_x, res_f, res_it = getattr(self.method, self.start_method_name)(self.canonical_x, self.x_eps)
            iterations_count += res_it
            sum_timedelta += datetime.now() - t
            if numpy.linalg.norm(res_x - self.canonical_x) < self.x_eps:
                successes += 1
            calls_count += self.test_function.calls
            self.test_function.reset()
            self.reset_method()
        result = Result(
            success_percent=100 * successes / self.iterations,
            calls=calls_count / self.iterations,
            input_args={
                **self.method_kwargs,
                **{
                    self.x_min_argument: self.x_min,
                    self.x_max_argument: self.x_max
                }
            },
            test_function=self.test_function_name,
            iterations=self.iterations,
            avg_time=str(sum_timedelta / self.iterations),
            avg_iterations=iterations_count / self.iterations
        )
        return result

    def reset_method(self):
        self.method = self.method_class(
            **self.method_kwargs,
            **{
                self.function_attr: self.test_function,
                self.x_min_argument: self.x_min,
                self.x_max_argument: self.x_max
            },
        )

    @property
    @abstractmethod
    def canonical_x(self) -> numpy.array:
        pass


class SphereBenchMark(BaseBenchMark):

    test_function = sphere
    test_function_name = 'Sphere'

    @property
    def canonical_x(self) -> numpy.array:
        return numpy.array(self.n * [0])


class RastriginBenchMark(BaseBenchMark):

    test_function = rastrigin
    test_function_name = 'Rastrigin'

    @property
    def canonical_x(self) -> numpy.array:
        return numpy.array(self.n * [0])


class AckleyBenchMark(BaseBenchMark):

    test_function = ackley
    test_function_name = 'Ackley'

    @property
    def canonical_x(self) -> numpy.array:
        return numpy.array(self.n * [0])


class RosenbrockBenchMark(BaseBenchMark):

    test_function = rosenbrock
    test_function_name = 'Rosenbrock'

    @property
    def canonical_x(self) -> numpy.array:
        return numpy.array(self.n * [1])


class GriewankBenchMark(BaseBenchMark):

    test_function = griewank
    test_function_name = 'Griewank'

    @property
    def canonical_x(self) -> numpy.array:
        return numpy.array(self.n * [0])


class SchwefelBenchMark(BaseBenchMark):

    test_function = schwefel
    test_function_name = 'Schwefel'

    @property
    def canonical_x(self) -> numpy.array:
        return numpy.array(self.n * [420.9687])


class LevyBenchMark(BaseBenchMark):

    test_function = levy
    test_function_name = 'Levy'

    @property
    def canonical_x(self) -> numpy.array:
        return numpy.array(self.n * [1])


# class MichalewiczBenchMark(BaseBenchMark):
#
#     test_function = michalewicz
#     test_function_name = 'Michalewicz'
#
#     @property
#     def canonical_x(self) -> numpy.array:
#         return numpy.array(self.n * [0])


class ZakharovBenchMark(BaseBenchMark):

    test_function = zakharov
    test_function_name = 'Zakharov'

    @property
    def canonical_x(self) -> numpy.array:
        return numpy.array(self.n * [0])


class DixonpriceBenchMark(BaseBenchMark):

    test_function = dixonprice
    test_function_name = 'Dixonprice'

    @property
    def canonical_x(self) -> numpy.array:
        return numpy.array([2 ** (-(2 ** i - 2) / 2 ** i) for i in range(1, self.n + 1)])


class StBenchMark(BaseBenchMark):
    test_function = st
    test_function_name = 'Styblinski–Tang'

    @property
    def canonical_x(self) -> numpy.array:
        return numpy.array(self.n * [-2.903534])
