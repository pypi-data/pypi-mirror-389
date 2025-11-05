"""
Visualizing Gaussian bell and its derivatives
=============================================

@author A. Schaer
@copyright Magnes AG, (C) 2025
"""

import logging
import os

import matplotlib.pyplot as pltlib
import numpy as np

from msgu.gauss import gaussians


logger = logging.getLogger(__name__)


class CFG:
    FILE_DIR = os.path.dirname(__file__)
    RES_DIR = os.path.join(FILE_DIR, "res", "gauss")
    PLT_RC = {
        "font": {"size": 16},
        "savefig": {"format": "svg", "dpi": 300},
        "axes": {"spines.right": False, "spines.top": False},
        "lines": {"linewidth": 3},
    }


def setup():
    logging.basicConfig(level=logging.INFO)
    logger.info(__doc__)

    for kk, vv in CFG.PLT_RC.items():
        pltlib.rc(kk, **vv)

    if not os.path.exists(CFG.RES_DIR):
        os.makedirs(CFG.RES_DIR)


def visualize_gaussian():
    logger.info("Plotting Gaussian and its derivatives")
    sigma = 1.0
    s = 6.0
    x = np.linspace(-s * sigma, s * sigma, 10_000, dtype=float)

    g = gaussians.gaussian(x, sigma=sigma)
    dga = gaussians.dgauss(x, sigma=sigma)
    ddga = gaussians.d2gauss(x, sigma=sigma)

    th = np.sqrt(np.log(4)) * sigma

    fig, ax = pltlib.subplots()
    ax.plot(x, g, c="black", label="$g(t)$", ls="--")
    ax.plot(x, dga, c="black", label=r"$\dot{g}(t)$", ls=":")
    ax.plot(x, ddga, c="black", label=r"$\ddot{g}(t)$", ls="-")
    for ii in range(1, 4):
        ax.axvspan(-ii * sigma, ii * sigma, alpha=0.15, color="orange", ec=None)

    vlinekwargs = dict(ls="-", color="deepskyblue", lw=0.75)
    ax.axvline(-th, **vlinekwargs)
    ax.axvline(th, **vlinekwargs)

    ax.set(xlim=(x[0], x[-1]), xlabel="Time [-]", ylabel="Amplitude [-]")
    ax.legend(loc="upper right")
    ax.grid(False)
    fig.tight_layout()
    fig.savefig(os.path.join(CFG.RES_DIR, "gaussians"))


def visualize_mexican_hat():
    fsh = 10000
    fs = 250
    t1 = 0.1
    nh = round(fsh * t1) + 1
    n = round(fs * t1) + 1
    th = np.linspace(0, t1, nh) - 0.5 * t1
    t = np.linspace(0, t1, n) - 0.5 * t1
    sigma = t1 / 6
    psih = -gaussians.d2gauss(th, sigma=sigma)
    psih -= psih[0]
    psi = -gaussians.d2gauss(t, sigma=sigma)
    psi -= psi[0]

    peak_amp = np.max(psih)
    psi /= peak_amp
    psih /= peak_amp
    styleh = dict(c="red")
    style = dict(c="black", marker="o", ls="", mfc=[1, 1, 1, 0], mec="black", ms=10)

    fig, axs = pltlib.subplots()
    axs.plot(th, psih, **styleh)
    axs.plot(t, psi, **style, clip_on=False)
    axs.set(
        xlim=(-t1 / 2, t1 / 2),
        xticks=[-t1 / 2, 0, t1 / 2],
        xticklabels=["-T/2", "0", "T/2"],
        xlabel="Time [-]",
        ylabel=r"$\psi(t)$ [-]",
    )
    fig.tight_layout()
    fig.savefig(os.path.join(CFG.RES_DIR, "search-template-td"))

    fa = np.linspace(0, fs / 2, 1000)
    a = 1 / (2 * sigma**2)
    omega = 2 * np.pi * fa
    omega2 = np.square(omega)
    PSIA = omega2 * np.exp(-omega2 / (4 * a))
    PSIA /= np.max(PSIA)
    peak_f = 6 * np.sqrt(2) / t1 / (2 * np.pi)

    fig, axs = pltlib.subplots()
    axs.plot(fa, PSIA, **styleh)
    axs.axvline(peak_f, ls="--", color="black")
    axs.set(xlim=(0, fs / 2), xlabel="Frequency [Hz]", ylabel="|S(f)| [-]")
    fig.tight_layout()
    fig.savefig(os.path.join(CFG.RES_DIR, "search-template-fd"))


def main():
    visualize_gaussian()
    visualize_mexican_hat()
    pltlib.close("all")


if __name__ == "__main__":
    setup()
    main()
