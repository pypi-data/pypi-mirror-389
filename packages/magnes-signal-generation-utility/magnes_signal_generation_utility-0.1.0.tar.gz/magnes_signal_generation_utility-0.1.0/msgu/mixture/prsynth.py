"""
Pseudo-random Synthetic Signal Generator
========================================

@author A. Schaer, H. Maurenbrecher
@copyright Magnes AG, (C) 2025
"""

import dataclasses

import numpy as np
from scipy import signal

from msgu.cardio import ecg
from msgu.noise import noise
from msgu.periodic import tidal


@dataclasses.dataclass
class SynthMeta:
    """Synthetic data meta information

    Attributes
    ----------
    gamma : float
        Disturbance gain
    sigma : float
        Noise gain
    freqs : list[float]
        Peak frequencies of ground-truth
    fws : list[float]
        Gaussian frequency widths of ground-truth
    """

    gamma: float
    sigma: float
    freqs: list[float]
    fws: list[float]


@dataclasses.dataclass
class SynthData:
    """Generated synthetic dataset

    Attributes
    ----------
    t : np.ndarray
        Time array
    x : np.ndarray
        Underlying, ground-truth signal
    d : np.ndarray
        Disturbance signal
    n : np.ndarray
        Noise signal
    meta : SynthMeta
        Dataset meta information
    """

    t: np.ndarray[tuple[int], float]
    x: np.ndarray[tuple[int], float]
    d: np.ndarray[tuple[int], float]
    n: np.ndarray[tuple[int], float]
    meta: SynthMeta

    @property
    def z(self) -> np.ndarray[tuple[int], float]:
        """Measurement attribute

        Returns
        -------
        np.ndarray
            Composite measurement: x + gamma*d + sigma*n
        """
        return self.x + self.meta.gamma * self.d + self.meta.sigma * self.n

    @property
    def fs(self) -> float:
        """Sampling frequency

        Returns
        -------
        float
            Sampling frequency in Hertz
        """
        return 1 / (self.t[1] - self.t[0])

    def __len__(self) -> int:
        return len(self.t)


def generate_synthetic_wave_with_cardiac_artifacts(
    fs: float,
    freqs: list[float],
    widths: list[float],
    gamma: float = 1.0,
    sigma: float = 1.0,
    bwscaling: tidal.WAVE_SCALING = tidal.WAVE_SCALING.IDENTITY,
    seed: int = None,
    nbeats: int = 1000,
    max_hr_bpm: float = 180,
) -> SynthData:
    """Generate synthetic quasi-periodic signals corrupted by cardiac artifacts and pink noise

    Parameters
    ----------
    fs : float
        Sampling rate in Hertz
    freqs : list[float]
        Peak-frequencies
    widths : list[float]
        Frequency peaks widths
    gamma : float, optional
        Disturbance scale, default is 1.0
    sigma : float, optional
        Noise scale, default is 1.0
    bwscaling : tidal.WAVE_SCALING, optional
        Brain waves scaling strategy, default is IDENTITY
    seed : int, optional
        RNG seed for reproducibility
    nbeats : int, optional
        Number of heart-rate beats to generate, default is 1000
    max_hr_bpm : float, optional
        Maximum heart rate in beats-per-minute, default is 180

    Returns
    -------
    SynthData
        Synthetic dataset containing time, signals, and metadata
    """

    t, disturbance = ecg.generate_ecg(fs, nbeats=nbeats)

    ecg_peak_idx, _ = signal.find_peaks(
        disturbance,
        distance=round(60 / max_hr_bpm * fs),
        height=3 * np.std(disturbance),
    )
    disturbance /= np.mean(disturbance[ecg_peak_idx])

    ground_truth = tidal.generate_randomly_phased_waves_blurred_peaks(
        t, freqs, widths, scaling=bwscaling, seed=seed
    )

    ground_truth /= np.std(ground_truth)
    pn = noise.generate_pink_noise(len(t), noise.PINK_NOISE_ALGO.FFT)

    meta = SynthMeta(gamma, sigma, freqs, widths)
    data = SynthData(t, ground_truth, disturbance, pn, meta)

    return data
