import numpy as np
from functools import wraps


def count_calls(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        wrapper.calls += 1
        try:
            return func(*args, **kwargs)
        except TypeError:
            return func(*args[1:], **kwargs)

    wrapper.calls = 0
    wrapper.reset = lambda: setattr(wrapper, 'calls', 0)
    return wrapper


@count_calls
def sphere(x):
    """
    Функция Сферы (Функция Де Йонга F1)

    f(x) = Σ(xi²) для i=1 до n

    Область: xi ∈ [-5.12, 5.12]
    Глобальный минимум: f(x*) = 0 в точке x* = (0, 0, ..., 0)
    """
    return np.sum(x ** 2)


@count_calls
def rastrigin(x):
    """
    Функция Растригина

    f(x) = 10n + Σ[xi² - 10cos(2πxi)] для i=1 до n

    Область: xi ∈ [-5.12, 5.12]
    Глобальный минимум: f(x*) = 0 в точке x* = (0, 0, ..., 0)
    """
    n = len(x)
    return 10 * n + np.sum(x ** 2 - 10 * np.cos(2 * np.pi * x))


@count_calls
def ackley(x):
    """
    Функция Акли

    f(x) = -20·exp(-0.2·√(1/n·Σxi²)) - exp(1/n·Σcos(2πxi)) + 20 + e

    Область: xi ∈ [-32.768, 32.768]
    Глобальный минимум: f(x*) = 0 в точке x* = (0, 0, ..., 0)
    """
    n = len(x)
    sum1 = np.sum(x ** 2)
    sum2 = np.sum(np.cos(2 * np.pi * x))
    return -20 * np.exp(-0.2 * np.sqrt(sum1 / n)) - np.exp(sum2 / n) + 20 + np.e


@count_calls
def rosenbrock(x):
    """
    Функция Розенброка (Банановая функция)

    f(x) = Σ[100(xi+1 - xi²)² + (1 - xi)²] для i=1 до n-1

    Область: xi ∈ [-5, 10]
    Глобальный минимум: f(x*) = 0 в точке x* = (1, 1, ..., 1)
    """
    return np.sum(100 * (x[1:] - x[:-1] ** 2) ** 2 + (1 - x[:-1]) ** 2)


@count_calls
def griewank(x):
    """
    Функция Гриванка

    f(x) = 1 + (1/4000)·Σxi² - Π[cos(xi/√i)] для i=1 до n

    Область: xi ∈ [-600, 600]
    Глобальный минимум: f(x*) = 0 в точке x* = (0, 0, ..., 0)
    """
    sum_sq = np.sum(x ** 2)
    prod_cos = np.prod(np.cos(x / np.sqrt(np.arange(1, len(x) + 1))))
    return sum_sq / 4000 - prod_cos + 1


@count_calls
def schwefel(x):
    """
    Функция Швефеля (Schwefel 2.26)

    f(x) = 418.9829n - Σ[xi·sin(√|xi|)] для i=1 до n

    Область: xi ∈ [-500, 500]
    Глобальный минимум: f(x*) = 0 в точке x* = (420.9687, ..., 420.9687)
    """
    n = len(x)
    return 418.9829 * n - np.sum(x * np.sin(np.sqrt(np.abs(x))))


@count_calls
def levy(x):
    """
    Функция Леви (Levy N.13)

    Область: xi ∈ [-10, 10]
    Глобальный минимум: f(x*) = 0 в точке x* = (1, 1, ..., 1)
    """
    w = 1 + (x - 1) / 4
    term1 = np.sin(np.pi * w[0]) ** 2
    term3 = (w[-1] - 1) ** 2 * (1 + np.sin(2 * np.pi * w[-1]) ** 2)
    wi = w[:-1]
    sum_term = np.sum((wi - 1) ** 2 * (1 + 10 * np.sin(np.pi * wi + 1) ** 2))
    return term1 + sum_term + term3


@count_calls
def michalewicz(x, m=10):
    """
    Функция Михалевича

    f(x) = -Σ[sin(xi)·sin^(2m)(i·xi²/π)] для i=1 до n

    Область: xi ∈ [0, π]
    Параметр m определяет крутизну (обычно m=10)
    """
    i = np.arange(1, len(x) + 1)
    return -np.sum(np.sin(x) * np.sin(i * x ** 2 / np.pi) ** (2 * m))


@count_calls
def zakharov(x):
    """
    Функция Захарова

    f(x) = Σxi² + (Σ0.5i·xi)² + (Σ0.5i·xi)⁴ для i=1 до n

    Область: xi ∈ [-5, 10]
    Глобальный минимум: f(x*) = 0 в точке x* = (0, 0, ..., 0)
    """
    sum1 = np.sum(x ** 2)
    i = np.arange(1, len(x) + 1)
    sum2 = np.sum(0.5 * i * x)
    return sum1 + sum2 ** 2 + sum2 ** 4


@count_calls
def dixonprice(x):
    """
    Функция Диксона-Прайса

    f(x) = (x1 - 1)² + Σ[i·(2xi² - xi-1)²] для i=2 до n

    Область: xi ∈ [-10, 10]
    Глобальный минимум: f(x*) = 0
    """
    i = np.arange(2, len(x) + 1)
    term1 = (x[0] - 1) ** 2
    term2 = np.sum(i * (2 * x[1:] ** 2 - x[:-1]) ** 2)
    return term1 + term2


@count_calls
def st(x):
    return np.sum((x**4 - 16 * x**2 + 5 * x) / 2)

