"""
Test cleaning module
====================

@author A. Schaer, H. Maurenbrecher
@copyright Magnes AG, (C) 2025
"""

import os

import matplotlib.pyplot as pltlib
import numpy as np
import pytest


from msgu.mixture import prsynth
from martrem.aux import templating
from martrem import cleaning


class CFG:
    FILE_DIR = os.path.dirname(__file__)
    DATA_DIR = os.path.join(FILE_DIR, "data")
    RES_DIR = os.path.join(FILE_DIR, "res", "cleaning")
    PLTLIB_RC: dict = {"savefig": {"dpi": 300, "format": "jpg"}, "lines": {"lw": 0.75}}


@pytest.fixture
def plottingf():
    for kk, vv in CFG.PLTLIB_RC.items():
        pltlib.rc(kk, **vv)

    if not os.path.exists(CFG.RES_DIR):
        os.makedirs(CFG.RES_DIR)

    yield

    pltlib.close("all")


def plot_cleaining_results(
    data: prsynth.SynthData, corrected: np.ndarray, artifact: np.ndarray, basename: str
):
    fig, axs = pltlib.subplots(nrows=2, sharex=True, sharey=True, figsize=(8, 5))
    axs[0].plot(data.t, data.z, c="gray", label="$z[k]$", lw=2)
    axs[0].plot(data.t, corrected, c="deepskyblue", label=r"$\hat{x}[k]$")
    axs[0].plot(data.t, data.x, c="black", label="$x[k]$", ls="--")
    axs[0].set(ylabel="Signals [a.u.]")
    axs[0].legend(ncol=3, loc="upper right")

    axs[1].plot(data.t, data.meta.gamma * data.d, c="red", label="$d[k]$")
    axs[1].plot(data.t, artifact, c="black", label=r"$\hat{d}[k]$", ls="-.")
    axs[1].set(
        xlim=(data.t[0], data.t[-1]), xlabel="Time [s]", ylabel="Disturbance [a.u.]"
    )
    axs[1].legend(ncol=2, loc="upper right")
    fig.tight_layout()
    fig.savefig(os.path.join(CFG.RES_DIR, basename))
    axs[1].set(xlim=(0, 4))
    fig.savefig(os.path.join(CFG.RES_DIR, f"{basename}-zoom"))


def test_clean_with_shape_template(plottingf):
    fs = 250.0
    T_psi = 0.1
    n_psi = round(T_psi * fs) + 1
    psi = templating.mexican(n_psi, fs=fs)
    min_peak_distance = round(60 / 180 * fs)
    data = prsynth.generate_synthetic_wave_with_cardiac_artifacts(
        fs, [12.0], [2.0], gamma=5.0, sigma=1.0, seed=0, nbeats=100, max_hr_bpm=150
    )
    ccorrected, cartifact = cleaning.clean_with_shape_template(
        data.z, data.fs, psi, 0.1, min_peak_distance
    )
    assert len(ccorrected) == len(data)
    assert len(cartifact) == len(data)
    plot_cleaining_results(data, ccorrected, cartifact, "template-removal")


def test_clean_with_shape_template_multipass(plottingf):
    fs = 250.0
    psi_durations = [0.07, 0.08, 0.09, 0.1, 0.11, 0.12]
    psis = []
    for T_psi in psi_durations:
        n_psi = round(T_psi * fs) + 1
        psis.append(templating.mexican(n_psi, fs=fs))

    min_peak_distance = round(60 / 180 * fs)
    data = prsynth.generate_synthetic_wave_with_cardiac_artifacts(
        fs, [12.0], [2.0], gamma=5.0, sigma=1.0, seed=0, nbeats=100, max_hr_bpm=150
    )
    ccorrected, cartifact = cleaning.clean_with_shape_template_multipass(
        data.z, data.fs, psis, 0.1, min_peak_distance
    )
    assert len(ccorrected) == len(data)
    assert len(cartifact) == len(data)
    plot_cleaining_results(data, ccorrected, cartifact, "multipass-template-removal")


def test_clean_with_adaptive_shape_correlation(plottingf):
    fs = 250.0
    T_psi = 0.1
    n_psi = round(T_psi * fs) + 1
    psi = templating.mexican(n_psi, fs=fs)
    n_tau = 2 * n_psi
    min_peak_distance = round(60 / 180 * fs)
    data = prsynth.generate_synthetic_wave_with_cardiac_artifacts(
        fs, [12.0], [2.0], gamma=5.0, sigma=1.0, seed=0, nbeats=100, max_hr_bpm=150
    )
    ccorrected, cartifact = cleaning.clean_with_adaptive_shape_correlation(
        data.z, data.fs, psi, n_tau, 0.1, min_peak_distance
    )
    assert len(ccorrected) == len(data)
    assert len(cartifact) == len(data)
    plot_cleaining_results(
        data, ccorrected, cartifact, "adaptive-shape-correlation-cleaning"
    )
