"""
Gaussians Module unittesting
============================

@author A. Schaer
@copyright Magnes AG, (C) 2025.
"""

import os

import matplotlib.pyplot as pltlib
import numpy as np
import pytest

from msgu.gauss import gaussians


class CFG:
    FILE_DIR: str = os.path.dirname(__file__)
    RES_DIR: str = os.path.join(FILE_DIR, "res")


@pytest.fixture
def plottingf():
    if not os.path.exists(CFG.RES_DIR):
        os.makedirs(CFG.RES_DIR)

    yield

    pltlib.close("all")


def test_gaussian(plottingf):
    t = np.linspace(-5, 5, 100)
    x = gaussians.gaussian(t)
    assert len(t) == len(x)

    fig, axs = pltlib.subplots()
    axs.plot(t, x)
    axs.set(xlim=(t[0], t[-1]))
    fig.tight_layout()
    fig.savefig(os.path.join(CFG.RES_DIR, "gaussian"))


def test_dgauss(plottingf):
    t = np.linspace(-5, 5, 100)
    x = gaussians.dgauss(t)
    assert len(t) == len(x)

    fig, axs = pltlib.subplots()
    axs.plot(t, x)
    axs.set(xlim=(t[0], t[-1]))
    fig.tight_layout()
    fig.savefig(os.path.join(CFG.RES_DIR, "gaussian-first-derivative"))


def test_d2gauss(plottingf):
    t = np.linspace(-5, 5, 100)
    x = gaussians.d2gauss(t)
    assert len(t) == len(x)

    fig, axs = pltlib.subplots()
    axs.plot(t, x)
    axs.set(xlim=(t[0], t[-1]))
    fig.tight_layout()
    fig.savefig(os.path.join(CFG.RES_DIR, "gaussian-second-derivative"))
