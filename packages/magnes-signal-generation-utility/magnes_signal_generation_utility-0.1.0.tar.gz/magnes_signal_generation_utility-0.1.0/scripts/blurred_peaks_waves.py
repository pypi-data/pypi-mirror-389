"""
Example usage of the blurred-peak waves generation
==================================================

@author A. Schaer
@copyright Magnes AG, (C) 2025.
"""

import logging
import os

import matplotlib.pyplot as pltlib
import numpy as np
from scipy import signal

from msgu.periodic import tidal


logger = logging.getLogger(__name__)


class CFG:
    FILE_DIR = os.path.dirname(__file__)
    RES_DIR = os.path.join(FILE_DIR, "res", "blurred-peaks")
    PLT_RC = {
        "font": {"size": 16},
        "savefig": {"format": "jpg", "dpi": 300},
        "axes": {"spines.right": False, "spines.top": False},
    }


def setup():
    logging.basicConfig(level=logging.INFO)
    logger.info(__doc__)

    for kk, vv in CFG.PLT_RC.items():
        pltlib.rc(kk, **vv)

    if not os.path.exists(CFG.RES_DIR):
        os.makedirs(CFG.RES_DIR)


def visualize_synthetic_signals():
    peak_freqs = [5, 20, 42]
    widths = [10 for _ in peak_freqs]
    fs = 1000
    t1 = 100.0
    n = round(fs * t1) + 1
    t = np.linspace(0, t1, n)
    datasets: list[np.ndarray] = [
        tidal.generate_randomly_phased_waves_blurred_peaks(
            t, [f], [w], scaling=tidal.WAVE_SCALING.IDENTITY, seed=0
        )
        for f, w in zip(peak_freqs, widths)
    ]

    linestyles = ["-", "--", "-."]
    yticks = []
    fig, axs = pltlib.subplots()
    for ii, data in enumerate(datasets):
        x = data / np.std(data)
        offset = 5 * (ii - len(peak_freqs) / 2)
        axs.plot(t, x + offset, c="black", ls="-", clip_on=True)
        yticks.append(offset)

    yticklabels = [rf"$f_0 = {f}\rm\,Hz$" for f in peak_freqs]
    axs.set(xlim=(0, 1), yticks=yticks, yticklabels=yticklabels, xlabel="Time [s]")
    fig.tight_layout()
    fig.savefig(os.path.join(CFG.RES_DIR, "pseudo-random-oscillations"))

    fig, axs = pltlib.subplots(figsize=(8, 5))
    for ii, data in enumerate(datasets):
        f, X = signal.welch(data, fs, nperseg=int(2**11))
        X /= np.max(np.abs(X))

        axs.plot(
            f,
            10 * np.log10(np.abs(X)),
            c="black",
            ls=linestyles[ii],
            label=yticklabels[ii],
            zorder=10,
        )
        axs.axvline(peak_freqs[ii], c="gray", ls=linestyles[ii], zorder=5)

    axs.set(ylim=(-40, 5), xlim=(0, 100), xlabel="Frequency [Hz]", ylabel="PSD [dB/Hz]")
    fig.tight_layout()
    fig.savefig(os.path.join(CFG.RES_DIR, "pseudo-random-oscillations-psd"))


def main():
    logger.info("Generating and visualizing synthetic signals.")
    visualize_synthetic_signals()


if __name__ == "__main__":
    setup()
    main()
