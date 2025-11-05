"""
Noise Generation Utility
========================

@author A. Schaer, H. Maurenbrecher
@copyright Magnes AG, (C) 2025
"""

import enum

import numpy as np


class CFG:
    THEORY_FILTER_KERNEL_SIZE: int = 64
    WIKI_FILTER_KERNEL_SIZE: int = 64
    VOSS_MCCARTNEY_N_GENERATORS: int = 16


class PINK_NOISE_ALGO(enum.Enum):
    FILTER_THEORY = enum.auto()
    FILTER_WIKI = enum.auto()
    FFT = enum.auto()
    VOSS_MCCARTNEY = enum.auto()


def generate_white_noise(n: int) -> np.ndarray:
    """Generate zero-mean, unit-variance white noise

    Parameters
    ----------
    n : int
        Number of samples to generate

    Returns
    -------
    np.ndarray
        White noise signal as numpy array
    """
    wn = np.random.randn(n)
    return (wn - np.mean(wn)) / np.std(wn)


def generate_pink_noise(
    n: int, algo: PINK_NOISE_ALGO = PINK_NOISE_ALGO.FILTER_THEORY
) -> np.ndarray:
    """Generate pink noise (1/f noise)

    Note
    ----
    It is 1/f in terms of _power_, hence 1/sqrt(f) in terms of amplitude.

    Parameters
    ----------
    n : int
        Number of samples to generate
    algo : PINK_NOISE_ALGO, optional
        Algorithm to use for generation, default is FILTER_THEORY

    Returns
    -------
    np.ndarray
        Pink noise signal as numpy array
    """
    wn = generate_white_noise(n)

    match algo:
        case PINK_NOISE_ALGO.FILTER_THEORY:
            if n < CFG.THEORY_FILTER_KERNEL_SIZE:
                raise ValueError(
                    f"Number of pink-noise samples with {algo} need to be at least {CFG.THEORY_FILTER_KERNEL_SIZE}"
                )

            t = np.arange(1, CFG.THEORY_FILTER_KERNEL_SIZE + 1, dtype=float)
            kernel = 1 / np.sqrt(t)
            pink_noise = np.convolve(wn, kernel, mode="same")

        case PINK_NOISE_ALGO.FILTER_WIKI:
            if n < CFG.WIKI_FILTER_KERNEL_SIZE:
                raise ValueError(
                    f"Number of pink-noise samples with {algo} need to be at least {CFG.WIKI_FILTER_KERNEL_SIZE}"
                )

            kernel = np.zeros(CFG.WIKI_FILTER_KERNEL_SIZE, dtype=float)
            sqrt_N = np.sqrt(CFG.WIKI_FILTER_KERNEL_SIZE)
            for nn in range(CFG.WIKI_FILTER_KERNEL_SIZE):
                kernel[nn] = 1 + np.cos(np.pi * nn) / sqrt_N
                for kk in range(1, CFG.WIKI_FILTER_KERNEL_SIZE // 2):
                    kernel[nn] += (
                        2
                        * np.cos(2 * np.pi * kk * nn / CFG.WIKI_FILTER_KERNEL_SIZE)
                        / np.sqrt(kk)
                    )

            kernel /= CFG.WIKI_FILTER_KERNEL_SIZE
            pink_noise = np.convolve(wn, kernel, mode="same")

        case PINK_NOISE_ALGO.FFT:
            f = np.fft.rfftfreq(n)
            f[0] = f[0] + np.spacing(1)
            WN = np.fft.rfft(wn, norm="ortho")
            WN /= np.sqrt(f)
            pink_noise = np.fft.irfft(WN, norm="ortho", n=n)

        case PINK_NOISE_ALGO.VOSS_MCCARTNEY:
            generators = np.zeros(CFG.VOSS_MCCARTNEY_N_GENERATORS)
            pink_noise = np.zeros(n)

            for i in range(n):
                for j in range(CFG.VOSS_MCCARTNEY_N_GENERATORS):
                    if i % (2**j) == 0:
                        generators[j] = np.random.randn()

                pink_noise[i] = np.sum(generators)

        case _:
            raise ValueError(
                f"Invalid pink noise generation algorithm {algo} provided. "
                f"Must be one of {PINK_NOISE_ALGO.__members__}"
            )

    return (pink_noise - np.mean(pink_noise)) / np.std(pink_noise)
