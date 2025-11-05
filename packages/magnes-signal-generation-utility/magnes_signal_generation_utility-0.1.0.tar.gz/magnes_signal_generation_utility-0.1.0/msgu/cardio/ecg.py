"""
ECG-like signal generation
==========================

@author A. Schaer, H. Maurenbrecher
@copyright Magnes AG, (C) 2025
"""

import dataclasses
import random

import numpy as np
from scipy import signal


class CFG:
    NOISE_LEVEL = 0.01

    class ECG_LIMITS_S:
        ## https://en.wikipedia.org/wiki/Electrocardiography#Amplitudes_and_intervals
        ## https://en.wikipedia.org/wiki/QRS_complex
        MIN_HR = 45.0
        MAX_HR = 150.0
        P = (0.01, 0.08)
        PR = (0.12, 0.2)
        QRS = (0.075, 0.105)
        Q = (0.02, 0.04)
        VAT = (0.02, 0.05)
        ST = PR
        T = (0.02, 0.16)
        RR = (60.0 / MAX_HR, 60.0 / MIN_HR)

    class ECG_MAX_AMPLITUDES_MW:
        P = 0.25
        R = 4.0
        Q = R / 4
        S = R / 5
        T = 2 * P


@dataclasses.dataclass
class Beat:
    fs: float
    seed: int = None

    def __post_init__(self):
        if isinstance(self.seed, (int, float, str, bytes, bytearray)):
            random.seed(self.seed)

        self._x = None

        def random_duration(limits: tuple):
            return random.randint(
                round(limits[0] * self.fs),
                round(limits[1] * self.fs),
            )

        self.p = (
            random_duration(CFG.ECG_LIMITS_S.P),
            random.uniform(0, CFG.ECG_MAX_AMPLITUDES_MW.P),
        )
        self.pq = random_duration(CFG.ECG_LIMITS_S.PR) - self.p[0]
        vat = random_duration(CFG.ECG_LIMITS_S.VAT)
        qrs = random_duration(CFG.ECG_LIMITS_S.QRS)
        self.q = max(random_duration(CFG.ECG_LIMITS_S.Q), 3), -1 * random.uniform(
            0.5 * CFG.ECG_MAX_AMPLITUDES_MW.Q, CFG.ECG_MAX_AMPLITUDES_MW.Q
        )
        self.r = max(2 * (vat - self.q[0]), 3), random.uniform(
            0.5 * CFG.ECG_MAX_AMPLITUDES_MW.R, CFG.ECG_MAX_AMPLITUDES_MW.R
        )
        self.s = max(qrs - self.q[0] - self.r[0], 3), -1 * random.uniform(
            0.5 * CFG.ECG_MAX_AMPLITUDES_MW.S, CFG.ECG_MAX_AMPLITUDES_MW.S
        )
        self.st = random_duration(CFG.ECG_LIMITS_S.ST)
        self.t = random_duration(CFG.ECG_LIMITS_S.T), random.uniform(
            0, CFG.ECG_MAX_AMPLITUDES_MW.T
        )

        self.n = (
            self.p[0]
            + self.pq
            + self.q[0]
            + self.r[0]
            + self.s[0]
            + self.st
            + self.t[0]
            + 1
        )

        if self._x is None:
            _x = np.zeros(self.n)
            i0 = 0
            _x[: self.p[0]] = self.p[1] * signal.windows.hann(self.p[0])
            i0 += self.p[0] + self.pq
            _x[i0 : i0 + self.q[0]] = self.q[1] * signal.windows.triang(self.q[0])
            i0 += self.q[0]
            _x[i0 : i0 + self.r[0]] = self.r[1] * signal.windows.triang(self.r[0])
            i0 += self.r[0]
            _x[i0 : i0 + self.s[0]] = self.s[1] * signal.windows.triang(self.s[0])
            i0 += self.s[0] + self.st
            _x[i0 : i0 + self.t[0]] = self.t[1] * signal.windows.hann(self.t[0])
            self._x = _x

    @property
    def duration(self) -> float:
        """Beat duration in seconds

        Returns
        -------
        float
            Duration of the beat signal in seconds
        """
        return (self.n - 1) / self.fs

    @property
    def time(self) -> np.ndarray:
        """Time array for the beat signal

        Returns
        -------
        np.ndarray
            Time array corresponding to the beat signal
        """
        return np.linspace(0, self.duration, self.n)

    @property
    def x(self) -> np.ndarray:
        """Beat signal array (copy)

        Returns
        -------
        np.ndarray
            Copy of the beat signal array
        """
        return self._x.copy()

    @property
    def r_peak_index(self) -> int:
        """Index of the R-peak in the beat signal

        Returns
        -------
        int
            Array index of the R-peak
        """
        return self.p[0] + self.pq + self.q[0] + self.r[0] // 2


def generate_ecg(
    fs: float, nbeats: int = 5, sigma: float = CFG.NOISE_LEVEL
) -> tuple[np.ndarray, np.ndarray]:
    """Generate timeseries at given sampling frequency and number of heart-beats

    Parameters
    ----------
    fs : float
        Sampling frequency in Hertz
    nbeats : int, optional
        Number of beats to be included in timeseries, defaults to 5
    sigma : float, optional
        Noise level to be added to signal

    Returns
    -------
    t : np.ndarray
        Time array
    x : np.ndarray
        ECG signal array
    """
    beats: list[Beat] = []
    MAX_ATTEMPTS = 5 * nbeats
    attempts = 0
    while len(beats) < nbeats and attempts <= MAX_ATTEMPTS:
        attempts += 1
        try:
            beat = Beat(fs)
            beats.append(beat)
        except Exception:
            pass

    if len(beats) == 0:
        raise RuntimeError("Failed to generate any beats at all")

    rrs = [
        random.randint(
            round(CFG.ECG_LIMITS_S.RR[0] * fs), round(CFG.ECG_LIMITS_S.RR[1] * fs)
        )
        for _ in range(nbeats - 1)
    ]
    res = beats[0].x
    for beat, rr in zip(beats[1:], rrs):
        arrays = [res]
        if rr - beat.r_peak_index > 0:
            arrays.append(np.zeros(rr - beat.r_peak_index))

        arrays.append(beat.x)
        res = np.concat(arrays)

    return np.linspace(0, (len(res) - 1) / fs, len(res)), res + sigma * np.random.randn(
        len(res)
    )
