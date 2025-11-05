"""
Example usage of the corrupted waves synthesizer
================================================

@author A. Schaer
@copyright Magnes AG, (C) 2025.
"""

import logging
import os

import matplotlib.pyplot as pltlib
import numpy as np
from scipy import signal

from msgu.mixture import prsynth


logger = logging.getLogger(__name__)


class CFG:
    FILE_DIR = os.path.dirname(__file__)
    RES_DIR = os.path.join(FILE_DIR, "res", "synth-waves")
    PLT_RC = {
        "font": {"size": 16},
        "savefig": {"format": "jpg", "dpi": 300},
        "axes": {"spines.right": False, "spines.top": False},
    }

    class DATA_GEN:
        PEAK_FREQS = [5, 20, 42]
        KWARGS = dict(
            fs=250,
            freqs=PEAK_FREQS,
            widths=[4 for _ in PEAK_FREQS],
            gamma=5.0,
            sigma=1.0,
            nbeats=100,
        )

    class VIZ:
        XSTYLE = dict(lw=0.75, c="deepskyblue", ls="--", label="Signal")
        ZSTYLE = dict(lw=0.75, c="black", label="Measurement")
        DSTYLE = dict(lw=1.5, c="red", label="Disturbance")
        NSTYLE = dict(lw=1.5, c="magenta", ls=":", label="Noise")


def setup():
    logging.basicConfig(level=logging.INFO)
    logger.info(__doc__)

    for kk, vv in CFG.PLT_RC.items():
        pltlib.rc(kk, **vv)

    if not os.path.exists(CFG.RES_DIR):
        os.makedirs(CFG.RES_DIR)


def power_to_db(lin: np.ndarray) -> np.ndarray:
    return 10 * np.log10(lin)


def generate_data() -> prsynth.SynthData:
    logger.info(f"Generating data with arguments: {CFG.DATA_GEN.KWARGS}")
    return prsynth.generate_synthetic_wave_with_cardiac_artifacts(**CFG.DATA_GEN.KWARGS)


def visualize_time_domain(data: prsynth.SynthData):
    logger.info("Visualizing data in time domain")
    zoom_span = 4.0
    zoom_t0 = 0.5 * (data.t[0] + data.t[-1])

    fig, axs = pltlib.subplots(figsize=(8, 5))
    axs.plot(data.t, data.z, **CFG.VIZ.ZSTYLE)
    axs.plot(data.t, data.x, **CFG.VIZ.XSTYLE)
    axs.plot(data.t, data.meta.gamma * data.d, **CFG.VIZ.DSTYLE)
    axs.plot(data.t, data.meta.sigma * data.n, **CFG.VIZ.NSTYLE)
    axs.set(xlim=(data.t[0], data.t[-1]), ylabel="Signal [a.u.]", xlabel="Time [s]")
    axs.legend(loc="lower left", ncols=2, bbox_to_anchor=(0.0, 1.0))
    fig.tight_layout()
    fig.savefig(os.path.join(CFG.RES_DIR, "synthetic-corrupted-wave"))
    axs.set(xlim=(zoom_t0, zoom_t0 + zoom_span))
    fig.savefig(os.path.join(CFG.RES_DIR, "synthetic-corrupted-wave-zoomed"))


def visualize_frequency_domain(data: prsynth.SynthData):
    logger.info("Visualizing data in frequency domain (Bode-magnitude)")

    NFFT = 256
    fx, Px = signal.welch(data.x, data.fs, nperseg=NFFT)
    fz, Pz = signal.welch(data.z, data.fs, nperseg=NFFT)
    fd, Pd = signal.welch(data.meta.gamma * data.d, data.fs, nperseg=NFFT)
    fn, Pn = signal.welch(data.meta.sigma * data.n, data.fs, nperseg=NFFT)

    fig, axs = pltlib.subplots(figsize=(8, 5))
    axs.plot(fx, power_to_db(Px), **CFG.VIZ.ZSTYLE)
    axs.plot(fz, power_to_db(Pz), **CFG.VIZ.XSTYLE)
    axs.plot(fd, power_to_db(Pd), **CFG.VIZ.DSTYLE)
    axs.plot(fn, power_to_db(Pn), **CFG.VIZ.NSTYLE)
    for f0, w in zip(data.meta.freqs, data.meta.fws):
        axs.axvline(f0, ls="-", c="grey", zorder=0)
        axs.axvspan(
            f0 - w / 2,
            f0 + w / 2,
            alpha=0.2,
            fc="grey",
        )

    axs.legend(loc="lower left", ncols=2, bbox_to_anchor=(0.0, 1.0))
    axs.set(
        xlim=(0, data.fs / 2),
        ylim=(-40, 0),
        xlabel="Frequency [Hz]",
        ylabel="PSD [dB/Hz]",
    )
    fig.tight_layout()
    fig.savefig(os.path.join(CFG.RES_DIR, "synthetic-corrupted-wave-psd"))


def main():
    data = generate_data()
    visualize_time_domain(data)
    visualize_frequency_domain(data)


if __name__ == "__main__":
    setup()
    main()
