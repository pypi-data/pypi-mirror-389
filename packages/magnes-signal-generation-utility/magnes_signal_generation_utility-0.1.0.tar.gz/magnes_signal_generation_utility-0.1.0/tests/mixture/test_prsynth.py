"""
Pseudo-random Synthesizer Testing
=================================

@author A. Schaer
@copyright Magnes AG, (C) 2025
"""

import os

import matplotlib.pyplot as pltlib
import numpy as np
import pytest

from msgu.mixture import prsynth


class CFG:
    FILE_DIR: str = os.path.dirname(__file__)
    RES_DIR: str = os.path.join(FILE_DIR, "res", "prsynth")


@pytest.fixture
def plottingf():
    if not os.path.exists(CFG.RES_DIR):
        os.makedirs(CFG.RES_DIR)

    yield

    pltlib.close("all")


def test_generate_synthetic_wave_with_cardiac_artifacts(plottingf):
    fs = 250.0
    freqs = [5.4, 13.7, 42.0]
    widths = [1, 5, 10]
    gamma = 5.0
    sigma = 0.1

    args = [fs, freqs, widths]
    kwargs = dict(gamma=gamma, sigma=sigma, seed=0, nbeats=5)

    cr = prsynth.generate_synthetic_wave_with_cardiac_artifacts(*args, **kwargs)
    assert pytest.approx(cr.meta.gamma) == gamma
    assert pytest.approx(cr.meta.sigma) == sigma
    assert np.allclose(cr.meta.freqs, freqs)
    assert np.allclose(cr.meta.fws, widths)

    fig, axs = pltlib.subplots()
    axs.plot(cr.t, cr.z, label="Measured", lw=1.5, c="black")
    axs.plot(cr.t, gamma * cr.d, label="Disturbance", lw=0.75, c="red")
    axs.plot(cr.t, cr.x, label="Signal", lw=0.75, c="deepskyblue", ls="--")
    axs.plot(cr.t, sigma * cr.n, label="Noise", lw=0.75, c="magenta", ls=":")
    axs.legend(loc="upper left", ncols=4)
    axs.set(xlabel="Time [s]", ylabel="Signals [a.u.]", xlim=(cr.t[0], cr.t[-1]))
    fig.tight_layout()
    fig.savefig(
        os.path.join(CFG.RES_DIR, "synthetic-wave-with-cardiac-artifacts"), dpi=300
    )
