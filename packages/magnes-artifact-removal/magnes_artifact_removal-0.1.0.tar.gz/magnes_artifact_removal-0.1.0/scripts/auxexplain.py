"""
Auxiliary Explanations Script
=============================

This script generates the components for the auxiliary
images needed to illustrate the inner workings of the
algorithms.

@author A. Schaer, H. Maurenbrecher
@copyright Magnes AG, (C) 2025.
"""

import os
import logging

import matplotlib.pyplot as pltlib
import numpy as np

from msgu.mixture import prsynth
from msgu.cardio import ecg

from martrem import cleaning
from martrem.aux import templating


class CFG:
    LOG_LEVEL: int = logging.INFO
    FILE_DIR: str = os.path.dirname(__file__)
    RES_DIR: str = os.path.join(FILE_DIR, "res", "auxexplain")

    class SIM:
        FS: float = 1000.0
        N_BEATS: int = 50
        SIGMA: float = 0.1
        GAMMA: float = 8.0
        FREQS: list[float] = [13.0, 25.0]
        WIDTHS: list[float] = [2.0, 4.2]
        ST_DURATION: float = 0.08
        N_ST: int = round(ST_DURATION * FS) + 1
        N_TAU: int = 2 * N_ST
        F_CO_HP: float = 0.1
        MIN_PEAK_DIST: int = round(60 / 180 * FS)

        assert len(FREQS) == len(WIDTHS)

    class VIZ:
        T1: float = 3
        CM = pltlib.cm.YlGnBu_r
        ST_T0: float = T1 / 5
        T_SCALE_BAR_OFFSET: float = T1 - 1.1
        PLT_RC: dict = {
            "font": {"size": 16},
            "savefig": {"format": "svg", "dpi": 300},
            "axes": {"spines.right": False, "spines.top": False},
            "lines": {"linewidth": 0.75},
            "legend": {"frameon": False},
        }
        WIDE_FIG_SIZE: tuple = (10, 5)
        NARROW_FIG_SIZE: tuple = (5, 5)
        PALETTE = CM(np.linspace(0, 0.8, 5))
        ST_C = PALETTE[-1]


logger = logging.getLogger(__name__)


def setup():
    logging.basicConfig(level=CFG.LOG_LEVEL)
    logger.info(__doc__)

    if not os.path.exists(CFG.RES_DIR):
        os.makedirs(CFG.RES_DIR)

    for kk, vv in CFG.VIZ.PLT_RC.items():
        pltlib.rc(kk, **vv)


def add_time_scalebar_to_axs(axs: pltlib.Axes, y: float = -1):
    axs.plot(
        [CFG.VIZ.T_SCALE_BAR_OFFSET, CFG.VIZ.T_SCALE_BAR_OFFSET + 1],
        [y, y],
        c="black",
        lw=1,
    )


def main():
    data = prsynth.generate_synthetic_wave_with_cardiac_artifacts(
        CFG.SIM.FS,
        CFG.SIM.FREQS,
        CFG.SIM.WIDTHS,
        CFG.SIM.GAMMA,
        CFG.SIM.SIGMA,
        nbeats=CFG.SIM.N_BEATS,
    )
    search_template = templating.mexican(CFG.SIM.N_ST, fs=data.fs)
    t_search_template = np.linspace(0, CFG.SIM.ST_DURATION, len(search_template))
    midres = dict()

    xhat, dhat = cleaning.clean_with_adaptive_shape_correlation(
        data.z,
        data.fs,
        search_template,
        CFG.SIM.N_TAU,
        CFG.SIM.F_CO_HP,
        CFG.SIM.MIN_PEAK_DIST,
        midres=midres,
    )

    xcorr = midres["xcorr"]
    xcp_idx = midres["xcorr-peaks"]
    template_windows = midres["template-windows"]
    tau = midres["tau"]

    beat = ecg.Beat(CFG.SIM.FS, seed=0)

    fig, axs = pltlib.subplots(figsize=CFG.VIZ.WIDE_FIG_SIZE)
    axs.plot(
        t_search_template + CFG.VIZ.ST_T0,
        search_template,
        c=CFG.VIZ.ST_C,
        lw=1.5,
        alpha=1.0,
        ls="-",
        label=r"$\psi$",
    )
    axs.plot(data.t, data.z, c=CFG.VIZ.PALETTE[0], label="$z$")
    add_time_scalebar_to_axs(axs, -CFG.SIM.GAMMA)
    axs.legend(loc="upper right", ncols=2)
    axs.set(xlim=(0, CFG.VIZ.T1), xticks=[], yticks=[], ylabel="Signal [a.u.]")
    axs.spines.bottom.set_visible(False)
    fig.tight_layout()
    fig.savefig(os.path.join(CFG.RES_DIR, "measurement-and-search-template"))

    fig, axs = pltlib.subplots(figsize=CFG.VIZ.WIDE_FIG_SIZE)
    axs.plot(data.t, xcorr, c="black", label=r"$r_{z\psi}$")
    axs.plot(data.t[xcp_idx], xcorr[xcp_idx], marker="^", color="red", ls="")
    for pidx in xcp_idx:
        if data.t[pidx] > CFG.VIZ.T1:
            break

        try:
            axs.axvspan(
                data.t[pidx - CFG.SIM.N_TAU // 2],
                data.t[pidx + CFG.SIM.N_TAU // 2 + 1],
                facecolor="gray",
                alpha=0.2,
            )
        except IndexError:
            # It can be that the last vspan exceeds the end of time
            pass

    axs.spines.bottom.set_visible(False)
    axs.set(xlim=(0, CFG.VIZ.T1), xticks=[], yticks=[], ylabel=r"$r_{z\psi}$")
    fig.tight_layout()
    fig.savefig(os.path.join(CFG.RES_DIR, "xcorr"))

    fig, axs = pltlib.subplots(figsize=CFG.VIZ.WIDE_FIG_SIZE)
    axs.plot(data.t, data.z, c=CFG.VIZ.PALETTE[0], label=r"$r_{z\psi}$")
    for pidx in xcp_idx:
        if data.t[pidx] > CFG.VIZ.T1:
            break
        try:
            axs.axvspan(
                data.t[pidx - CFG.SIM.N_TAU // 2],
                data.t[pidx + CFG.SIM.N_TAU // 2 + 1],
                facecolor="gray",
                alpha=0.2,
            )
        except IndexError:
            # It can be that the last vspan exceeds the end of time
            pass

    axs.spines.bottom.set_visible(False)
    axs.set(xlim=(0, CFG.VIZ.T1), xticks=[], yticks=[], ylabel=r"$z$")
    # axs.legend(loc="upper right")
    fig.tight_layout()
    fig.savefig(os.path.join(CFG.RES_DIR, "z-windows"))

    fig, axs = pltlib.subplots(figsize=CFG.VIZ.NARROW_FIG_SIZE)
    t = np.linspace(0, 1, CFG.SIM.N_TAU)
    for tau_data in template_windows:
        axs.plot(t, tau_data, c=CFG.VIZ.PALETTE[0], alpha=0.5)

    axs.plot(t, tau, c=CFG.VIZ.PALETTE[2], lw=2)
    axs.spines.bottom.set_visible(False)
    axs.set(xlim=(0, 1), xticks=[], yticks=[], ylabel=r"$\tau$")
    fig.tight_layout()
    fig.savefig(os.path.join(CFG.RES_DIR, "tau-averaging"))

    fig, axs = pltlib.subplots(figsize=CFG.VIZ.WIDE_FIG_SIZE)
    axs.plot(data.t, dhat, c=CFG.VIZ.PALETTE[3], lw=1.5, label=r"$\hat{d}$")
    axs.plot(data.t, data.meta.gamma * data.d, c="black", ls="--", label=r"$d$")
    axs.legend(loc="upper right", ncols=2)
    axs.spines.bottom.set_visible(False)
    axs.set(
        xlim=(0, CFG.VIZ.T1),
        xticks=[],
        yticks=[],
        ylabel="Signal [a.u.]",
    )
    fig.tight_layout()
    fig.savefig(os.path.join(CFG.RES_DIR, "artifact-estimation"))

    fig, axs = pltlib.subplots(figsize=CFG.VIZ.WIDE_FIG_SIZE)
    axs.plot(data.t, xhat, c=CFG.VIZ.PALETTE[4], lw=1.5, label=r"$\hat{x}$")
    axs.plot(data.t, data.x, c="black", ls="--", label=r"$x$")
    axs.legend(loc="upper right", ncols=2)
    axs.spines.bottom.set_visible(False)
    axs.set(xlim=(0, CFG.VIZ.T1), xticks=[], yticks=[], ylabel=r"Signal [a.u.]")
    fig.tight_layout()
    fig.savefig(os.path.join(CFG.RES_DIR, "signal-estimation"))

    fig, axs = pltlib.subplots()
    peak_time_beat = beat.time[np.argmax(beat.x)]
    peak_time_template = t_search_template[np.argmax(search_template)]
    axs.plot(
        beat.time - peak_time_beat, beat.x / max(beat.x), c=CFG.VIZ.PALETTE[0], lw=1
    )

    axs.plot(
        t_search_template - peak_time_template,
        search_template / max(search_template),
        c=CFG.VIZ.PALETTE[-1],
        lw=1,
    )
    axs.spines.bottom.set_visible(False)
    axs.set(
        xlim=(-peak_time_beat, beat.time[-1] - peak_time_beat),
        xticks=[],
        yticks=[],
        ylabel=r"Signal [a.u.]",
    )
    fig.tight_layout()
    fig.savefig(os.path.join(CFG.RES_DIR, "qrs-sombrero"))

    pltlib.close("all")


if __name__ == "__main__":
    setup()
    main()
