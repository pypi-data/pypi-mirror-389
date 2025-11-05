"""
Gaussians and derivatives
=========================

@author A. Schaer, H. Maurenbrecher
@copyright Magnes AG, (C) 2025.
"""

import numpy as np


def gaussian(x: np.ndarray, mu: float = 0.0, sigma: float = 1.0) -> np.ndarray:
    """Return gaussian function evaluated on provided input.

    Parameters
    ----------
    x : np.ndarray
        The input array
    mu : float, optional
        The center of the Gaussian, default is 0.0
    sigma : float, optional
        The standard deviation of the Gaussian, default is 1.0

    Returns
    -------
    np.ndarray
        Non-normalized Gaussian bell centered at mu and with stddev sigma
    """
    a = 0.5 / sigma**2
    return np.exp(-((x - mu) ** 2) * a)


def dgauss(x: np.ndarray, mu: float = 0.0, sigma: float = 1.0) -> np.ndarray:
    """First gaussian derivative

    Parameters
    ----------
    x : np.ndarray
        The input array
    mu : float, optional
        The center of the Gaussian, default is 0.0
    sigma : float, optional
        The standard deviation of the Gaussian, default is 1.0

    Returns
    -------
    np.ndarray
        Non-normalized first derivative of the Gaussian bell centered at mu and with stddev sigma
    """
    return (mu - x) * gaussian(x, mu, sigma) / sigma**2


def d2gauss(x: np.ndarray, mu: float = 0.0, sigma: float = 1.0) -> np.ndarray:
    """Second gaussian derivative

    Parameters
    ----------
    x : np.ndarray
        The input array
    mu : float, optional
        The center of the Gaussian, default is 0.0
    sigma : float, optional
        The standard deviation of the Gaussian, default is 1.0

    Returns
    -------
    np.ndarray
        Non-normalized second derivative of the Gaussian bell centered at mu and with stddev sigma
    """

    a = 0.5 / sigma**2
    return gaussian(x, mu, sigma) * (2 * a * (x - mu) ** 2 - 1) * 2 * a
