"""
S-curves utility testing
========================

@author A. Schaer
@copyright Magnes AG, (C) 2025
"""

import os

import matplotlib.pyplot as pltlib
import numpy as np
import pytest

from msgu.trajectory import scurves


class CFG:
    FILE_DIR: str = os.path.dirname(__file__)
    RES_DIR: str = os.path.join(FILE_DIR, "res", "scurves")


@pytest.fixture
def plottingf():
    if not os.path.exists(CFG.RES_DIR):
        os.makedirs(CFG.RES_DIR)

    yield

    pltlib.close("all")


def test_generate_s_curve3(plottingf):
    n = 1000
    t = np.linspace(0, 1, n)
    x = scurves.generate_s_curve3(n)

    assert pytest.approx(x[0]) == 0
    assert pytest.approx(x[-1]) == 1

    fig, axs = pltlib.subplots()
    axs.plot(t, x, c="black")
    fig.tight_layout()
    fig.savefig(os.path.join(CFG.RES_DIR, "scurve-poly3"))


def test_generate_s_curve5(plottingf):
    n = 1000
    t = np.linspace(0, 1, n)
    x = scurves.generate_s_curve5(n)

    assert pytest.approx(x[0]) == 0
    assert pytest.approx(x[-1]) == 1

    fig, axs = pltlib.subplots()
    axs.plot(t, x, c="black")
    fig.tight_layout()
    fig.savefig(os.path.join(CFG.RES_DIR, "scurve-poly5"))
