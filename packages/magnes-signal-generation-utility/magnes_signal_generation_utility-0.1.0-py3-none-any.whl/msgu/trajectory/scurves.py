"""
S-curves utility
================

@author A. Schaer, H. Maurenbrecher
@copyright Magnes AG, (C) 2025
"""

import numpy as np


def generate_s_curve3(n: int) -> np.ndarray:
    """Fit cubic s-curve on [0,1]x[0,1]

    Uses polynomial: x(t) = a t**3 + b t**2 + c t + d

    Boundary conditions with t0 = 0, t1 = 1, x0 = 0, x1 = 1:
        - x(t=t0) = x0 -> d = x0
        - dx(t=t0) = 0 -> c = 0
        - dx(t=t1) = 0 -> 3a t1**2 + 2b t1 = 0 --> b = -3/2 a t1
        - x(t=t1) = x1 -> a t1**3 - 3/2 a t1**3 + x0 = x1 --> a = -2 * (x1 - x0) / t1**3

    Parameters
    ----------
    n : int
        Desired number of output points

    Returns
    -------
    np.ndarray
        Cubic s-curve of n points
    """
    t = np.linspace(0, 1, n)
    a = -2.0
    b = 3.0
    c = 0.0
    d = 0.0
    return np.polyval([a, b, c, d], t)


def generate_s_curve5(n: int) -> np.ndarray:
    """Fit 5th Order S-Curve on [0,1]x[0,1]

    Uses polynomial: x(t) = a t**5 + b t**4 + c t**3 + d t**2 + e t + f

    Boundary conditions with t0 = 0, t1 = 1, x0 = 0, x1 = 1:
        - x(t=t0) = x0  -> f = x0
        - dx(t=t0) = 0  -> e = 0
        - ddx(t=t0) = 0 -> d = 0
        - x(t=t1) = x1  -> a + b + c + x0 = x1
        - dx(t=t1) = 0  -> 5a + 4b + 3c = 0
        - ddx(t=t1) = 0 -> 20a + 12b + 6c = 0

    Solution (via Wolframalpha):
        - a = 6 x1 - 6 x0
        - b = 15 (x0 - x1)
        - c = 10 (x1 - x0)

    Parameters
    ----------
    n : int
        Desired number of output points

    Returns
    -------
    np.ndarray
        Quintic S-curve of n points
    """
    t = np.linspace(0, 1, n)
    a = 6.0
    b = -15.0
    c = 10.0
    d = 0.0
    e = 0.0
    f = 0.0
    return np.polyval([a, b, c, d, e, f], t)
