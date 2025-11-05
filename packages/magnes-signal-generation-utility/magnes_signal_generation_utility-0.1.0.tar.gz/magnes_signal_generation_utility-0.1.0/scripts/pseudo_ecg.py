"""
Generate and visualize a pseudo ECG signal
==========================================

@author A. Schaer
@copyright Magnes AG, (C) 2025
"""

"""
Example usage of the blurred-peak waves generation
==================================================

@author A. Schaer
@copyright Magnes AG, (C) 2025.
"""

import logging
import os
import random

import matplotlib.pyplot as pltlib
import numpy as np
from scipy import signal

from msgu.cardio import ecg


logger = logging.getLogger(__name__)


class CFG:
    FILE_DIR = os.path.dirname(__file__)
    RES_DIR = os.path.join(FILE_DIR, "res", "cardio")
    PLT_RC = {
        "font": {"size": 16},
        "savefig": {"format": "svg", "dpi": 300},
        "axes": {"spines.right": False, "spines.top": False},
    }


def setup():
    logging.basicConfig(level=logging.INFO)
    logger.info(__doc__)

    for kk, vv in CFG.PLT_RC.items():
        pltlib.rc(kk, **vv)

    if not os.path.exists(CFG.RES_DIR):
        os.makedirs(CFG.RES_DIR)


def main():
    fs = 1000.0
    random.seed(0)
    beats: list[ecg.Beat] = []
    nbeats = 10
    attempts = 0
    MAX_ATTEMPTS = 10 * nbeats
    while len(beats) < nbeats and attempts <= MAX_ATTEMPTS:
        attempts += 1
        try:
            beats.append(ecg.Beat(fs))
        except Exception:
            pass

    nbeats = len(beats)
    b0 = beats[0]

    t = 1e3 * b0.time
    fig, axs = pltlib.subplots()
    axs.plot(t, b0.x, c="black", lw=3)
    axs.set(
        xlabel="Time [ms]",
        ylabel="Amplitude [mV]",
        xlim=(t[0], t[-1]),
        ylim=(-1, 5),
    )
    fig.tight_layout()
    fig.savefig(os.path.join(CFG.RES_DIR, "beat"))

    t1h = 0.3
    t0t = t1h + 0.1
    t1t = 0.1
    th = np.linspace(0, t1h, round(fs * t1h) + 1)
    tt = t0t + np.linspace(0, t1t, round(fs * t1t) + 1)
    ah = 2
    at = 5
    hw = signal.windows.hann(len(th)) * ah
    tw = signal.windows.triang(len(tt)) * at
    colors = pltlib.cm.YlGnBu_r(np.linspace(0, 0.7, 2))

    fig, axs = pltlib.subplots()
    axs.plot(th, hw, c=colors[0], lw=3)
    axs.plot(th, -0.2 * np.ones_like(th), c="black", lw=1, ls="--")
    axs.plot(tt, tw, c=colors[1], lw=3)
    axs.plot(tt, -0.2 * np.ones_like(tt), c="black", lw=1, ls="--")
    axs.plot(np.mean(th) * np.ones(2), [0, ah], c="black", lw=1)
    axs.plot(np.mean(tt) * np.ones(2), [0, at], c="black", lw=1)

    axs.set(
        xlabel="Time [a.u.]",
        ylabel="Amplitude [a.u.]",
        xticks=[],
        yticks=[],
    )
    fig.tight_layout()
    fig.savefig(os.path.join(CFG.RES_DIR, "beat-waves"))

    colors = pltlib.cm.YlGnBu_r(np.linspace(0, 0.7, nbeats))
    fig, axs = pltlib.subplots()
    for bi, b in enumerate(beats):
        t = np.linspace(0, 1, b.n)
        axs.plot(t, b.x - (bi - nbeats / 2), c=colors[bi], lw=3)

    ref_bar_amplitude = 5
    axs.plot(
        [1.08, 1.08], [-0.5 * ref_bar_amplitude, 0.5 * ref_bar_amplitude], c="black"
    )
    axs.text(
        1.02,
        0.0,
        f"{ref_bar_amplitude} mV",
        ha="center",
        va="top",
        rotation=90,
        rotation_mode="anchor",
    )
    axs.set(
        xlabel="Normalized time [-]", ylabel="Amplitude [mV]", xlim=(0, 1.1), yticks=[]
    )
    fig.tight_layout()
    fig.savefig(os.path.join(CFG.RES_DIR, "beats"))

    t, x = ecg.generate_ecg(fs, sigma=0)
    fig, axs = pltlib.subplots()
    axs.plot(t, x, c="black", lw=3)
    axs.set(xlim=(0, t[-1]), xlabel="Time [s]", ylabel="Amplitude [mV]")
    fig.tight_layout()
    fig.savefig(os.path.join(CFG.RES_DIR, "ecg"))
    pltlib.close("all")


if __name__ == "__main__":
    setup()
    main()
