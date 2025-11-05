"""
Cardio Unittests
================

@author A. Schaer
@copyright Magnes AG, (C) 2025
"""

import os

import matplotlib.pyplot as pltlib
import numpy as np
import pytest
from scipy import signal

from msgu.cardio import ecg


class CFG:
    FILE_DIR = os.path.dirname(__file__)
    RES_DIR = os.path.join(FILE_DIR, "res", "ecg")
    FS: float = 250.0


@pytest.fixture
def plottingf():
    if not os.path.exists(CFG.RES_DIR):
        os.makedirs(CFG.RES_DIR)

    yield

    pltlib.close("all")




def test_seeded_beat(plottingf):
    beat = ecg.Beat(CFG.FS, seed=0)

    fig, axs = pltlib.subplots()
    axs.plot(beat.time, beat.x, c="black")
    axs.set(xlabel="Time [s]", ylabel="Signal [mV]", xlim=(0, beat.time[-1]))
    fig.tight_layout()
    fig.savefig(os.path.join(CFG.RES_DIR, "single-beat"))


def test_generate_ecg_short():
    t, x = ecg.generate_ecg(CFG.FS)
    fig, axs = pltlib.subplots()
    axs.plot(t, x, c="black")
    axs.set(xlabel="Time [s]", ylabel="Signal [mV]", xlim=(0, t[-1]))
    fig.savefig(os.path.join(CFG.RES_DIR, "generated-short-ecg"))


def test_generate_ecg_100_beats():
    t, x = ecg.generate_ecg(CFG.FS, nbeats=100)
    print(f"ECG signal mean ± std [mV]: {np.mean(x):.2f} ± {np.std(x):.2f}", end="... ")
    f, X = signal.welch(x, fs=CFG.FS, nperseg=512)

    fig, axs = pltlib.subplots()
    axs.plot(t, x, c="black")
    axs.set(xlabel="Time [s]", ylabel="Signal [mV]", xlim=(0, t[-1]))
    fig.savefig(os.path.join(CFG.RES_DIR, "generated-100-beats-ecg"))
    axs.set(xlim=(0, 5))
    fig.savefig(os.path.join(CFG.RES_DIR, "generated-100-beats-ecg-first-five-seconds"))

    fig, axs = pltlib.subplots()
    axs.plot(f, 20 * np.log10(np.abs(X)), c="black")
    axs.set(xlabel="Frequency [s]", ylabel="PSD [dB/Hz]", xlim=(0, CFG.FS / 2))
    fig.savefig(os.path.join(CFG.RES_DIR, "generated-100-beats-ecg-psd"))
