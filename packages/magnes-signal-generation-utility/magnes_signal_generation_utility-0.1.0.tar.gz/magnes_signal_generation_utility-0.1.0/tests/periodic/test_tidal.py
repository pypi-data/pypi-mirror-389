"""
Sinusoidal signal generator testing
===================================

@author A. Schaer
@copyright Magnes AG, (C) 2025.
"""

import os

import matplotlib.pyplot as pltlib
import numpy as np
import pytest
from scipy import signal

from msgu.periodic import tidal


class CFG:
    FILE_DIR: str = os.path.dirname(__file__)
    RES_DIR: str = os.path.join(FILE_DIR, "res", "tidal")


@pytest.fixture
def plottingf():
    if not os.path.exists(CFG.RES_DIR):
        os.makedirs(CFG.RES_DIR)

    yield

    pltlib.close("all")


@pytest.mark.parametrize(
    "scaling", [s for s in tidal.WAVE_SCALING], ids=lambda x: x.name
)
def test_generate_randomly_phased_waves_single_freq(
    plottingf, scaling: tidal.WAVE_SCALING
):
    fs = 200
    t1 = 10
    n = round(fs * t1) + 1
    t = np.linspace(0, t1, n)
    freqs = [1.0, 14.5, 20.0, 65.0]
    x = tidal.generate_randomly_phased_waves_single_freq(
        t, freqs, scaling=scaling, seed=20250905
    )
    f, P = signal.welch(x, fs, nperseg=500)

    assert len(x) == n

    fig, axs = pltlib.subplots()
    axs.plot(t, x, c="black")
    axs.set(
        xlim=(0, t1),
        xlabel="Recording time [s]",
        ylabel="Amplitude [-]",
    )
    fig.tight_layout()
    fig.savefig(os.path.join(CFG.RES_DIR, f"random-waves-td-{scaling.name.lower()}"))

    fig, axs = pltlib.subplots()
    axs.plot(f, 10 * np.log10(P), c="black")
    for f0 in freqs:
        axs.axvline(f0, color="red")

    axs.set(xlabel="Frequency [Hz]", ylabel="PSD [dB/Hz]")
    fig.tight_layout()
    fig.savefig(os.path.join(CFG.RES_DIR, f"random-waves-psd-{scaling.name.lower()}"))


def test_generate_randomly_phased_waves_blurred_peaks(plottingf):
    t1 = 10
    fs = 250
    n = round(t1 * fs) + 1
    t = np.linspace(0, t1, n)
    f0 = 30
    bin_widths = [1, 5, 10]
    cr = []
    for w in bin_widths:
        cr.append(
            tidal.generate_randomly_phased_waves_blurred_peaks(
                t, [f0], [w], seed=20250911
            )
        )

    f = np.fft.rfftfreq(n) * fs
    CR = [np.fft.rfft(x, norm="ortho") for x in cr]

    fig, axs = pltlib.subplots()
    for x, w in zip(cr[::-1], bin_widths[::-1]):
        axs.plot(t, x, label=f"w = {w:.1f} Hz")

    axs.set(xlim=(t1 / 2, t1 / 2 + 2), xlabel="Time [s]", ylabel="Signal [-]")
    axs.legend(loc="upper left")
    fig.tight_layout()
    fig.savefig(os.path.join(CFG.RES_DIR, "random-blurred-waves-td"))

    fig, axs = pltlib.subplots(nrows=2, sharex=True)
    for x, w in zip(CR[::-1], bin_widths[::-1]):
        axs[0].plot(f, np.abs(x), label=f"w = {w:.1f} Hz")
        axs[1].plot(f, np.unwrap(np.angle(x)))

    for ax in axs:
        ax.axvline(f0, color="black", ls="--")

    axs[0].legend(loc="upper right")
    axs[0].set(ylabel="Amplitude [-]")
    axs[1].set(xlim=(0, fs / 2), xlabel="Frequency [Hz]", ylabel="Phase [rad]")
    fig.tight_layout()
    fig.savefig(os.path.join(CFG.RES_DIR, "random-blurred-waves-bin-width-fd"))
