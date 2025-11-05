"""
Test Noise Generation
=====================

@author A. Schaer
@copyright Magnes AG, (C) 2025
"""

import os
import time

import matplotlib.pyplot as pltlib
import numpy as np
import pytest

from msgu.noise import noise


class CFG:
    FILE_DIR: str = os.path.dirname(__file__)
    RES_DIR: str = os.path.join(FILE_DIR, "res", "noise")


@pytest.fixture
def plottingf():
    if not os.path.exists(CFG.RES_DIR):
        os.makedirs(CFG.RES_DIR)

    yield

    pltlib.close("all")


def test_generate_white_noise(plottingf):
    wn = noise.generate_white_noise(1024)

    assert len(wn) == 1024

    f = np.fft.rfftfreq(len(wn))
    WN = np.fft.rfft(wn, norm="ortho")
    fig, axs = pltlib.subplots()
    axs.plot(f, 20 * np.log10(np.abs(WN)), c="black")
    axs.axhline(0, c="cyan", ls="-")

    axs.set(
        xlabel="Normalized frequency",
        ylabel="|WN| [dB]",
        xlim=(0, 0.5),
        ylim=(-40, 10),
    )
    fig.tight_layout()
    fig.savefig(os.path.join(CFG.RES_DIR, "white-noise"))


@pytest.mark.parametrize("method", [m for m in noise.PINK_NOISE_ALGO])
def test_generate_pink_noise(plottingf, method: noise.PINK_NOISE_ALGO):
    n = 10_000
    tic = time.time()
    pn = noise.generate_pink_noise(n, algo=method)
    toc = time.time()
    print(
        f"Elapsed time for {method.name}: {toc-tic:.2e} seconds for n = {n}", end="..."
    )
    assert len(pn) == n

    f = np.fft.rfftfreq(len(pn))
    PN = np.fft.rfft(pn, norm="ortho")
    fig, axs = pltlib.subplots()
    axs.plot(f, 20 * np.log10(np.abs(PN)), c="black")
    axs.plot(
        f, 20 * np.log10(1 / (np.sqrt(f + np.spacing(1)))) - 10, c="magenta", ls="-"
    )

    axs.set(
        xlabel="Normalized frequency",
        ylabel="|PN| [dB]",
        xlim=(0, 0.5),
        ylim=(-40, 20),
    )
    fig.tight_layout()
    fig.savefig(os.path.join(CFG.RES_DIR, f"pink-noise-{method.name.lower()}"))
