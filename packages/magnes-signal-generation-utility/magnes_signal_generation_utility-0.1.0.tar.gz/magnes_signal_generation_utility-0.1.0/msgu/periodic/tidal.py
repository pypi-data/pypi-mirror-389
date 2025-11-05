"""
Sinusoidal periodic signals
===========================

@author A. Schaer, H. Maurenbrecher
@copyright Magnes AG, (C) 2025.
"""

import enum

import numpy as np

from msgu.noise import noise
from msgu.gauss import gaussians


class WAVE_SCALING(enum.Enum):
    IDENTITY = enum.auto()
    INV = enum.auto()
    INV_SQRT = enum.auto()
    TWO_INV_SQRT = enum.auto()

    def __call__(self, x: float) -> float:
        match self:
            case WAVE_SCALING.IDENTITY:
                return 1.0
            case WAVE_SCALING.INV:
                return 1.0 / x
            case WAVE_SCALING.INV_SQRT:
                return 1.0 / np.sqrt(x)
            case WAVE_SCALING.TWO_INV_SQRT:
                return np.sqrt(2 / x)
            case _:
                raise ValueError(f"Invalid wave scaling {self}")



def generate_randomly_phased_waves_single_freq(
    t: np.ndarray,
    freqs: list[float],
    scaling: WAVE_SCALING = WAVE_SCALING.INV,
    seed: int = None,
) -> np.ndarray:
    """Returns a signal that is a superposition of randomly phased sine-waves.

    The amplitude of each wave is scaled according to the provided scaling strategy.
    This is the sharp-peaks implemenation.

    Parameters
    ----------
    t : np.ndarray
        Time array
    freqs : list[float]
        List of peak-frequencies
    scaling : WAVE_SCALING, optional
        Addends scaling strategy, default is INV
    seed : int, optional
        RNG seed for reproducibility

    Returns
    -------
    np.ndarray
        Superposition of sine-waves
    """
    x = np.zeros_like(t)
    if seed:
        np.random.seed(seed)

    for f in freqs:
        if f <= 0:
            continue

        x += np.sin(2 * np.pi * f * t + 2 * np.pi * np.random.rand()) * scaling(f)

    return x / len(freqs)


def generate_randomly_phased_waves_blurred_peaks(
    t: np.ndarray,
    freqs: list[float],
    widths: list[float],
    scaling: WAVE_SCALING = WAVE_SCALING.INV,
    seed: int = None,
) -> np.ndarray:
    """Returns a signal that is a superposition of randomly phased sine-waves with blurred frequencies

    Parameters
    ----------
    t : np.ndarray
        Time array
    freqs : list[float]
        List of peak-frequencies
    widths : list[float]
        Frequency peaks widths
    scaling : WAVE_SCALING, optional
        Addends scaling strategy, default is INV
    seed : int, optional
        RNG seed for reproducibility

    Returns
    -------
    np.ndarray
        Superposition of sine-waves
    """
    th = np.sqrt(np.log(4))
    x = np.zeros_like(t)
    fs = 1 / (t[1] - t[0])
    if seed:
        np.random.seed(seed)

    f = np.fft.rfftfreq(len(t)) * fs
    for f0, w in zip(freqs, widths):
        if f0 <= 0 or w <= 0:
            raise ValueError(f"Invalid frequency {f0} or width {w} passed")

        y = noise.generate_white_noise(len(t))
        yf = np.fft.rfft(y, norm="ortho")
        # NOTE If we want the width to correspond to -3dB (i.e. power halving),
        # we need to scale the squared fft or scale by the square-root of the window
        W = np.sqrt(gaussians.gaussian(f, f0, w * th))
        yf *= W
        x += np.fft.irfft(yf, n=len(x), norm="ortho") * scaling(f0)

    return x.copy()