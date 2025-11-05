"""
Test templates module
=====================

@author A. Schaer, H. Maurenbrecher
@copyright Magnes AG, (C) 2025
"""

import os

import matplotlib.pyplot as pltlib
import numpy as np
import pytest

from martrem.aux import templating


class CFG:
    FILE_DIR = os.path.dirname(__file__)
    DATA_DIR = os.path.join(FILE_DIR, "data")
    RES_DIR = os.path.join(FILE_DIR, "res", "templates")


@pytest.fixture
def plottingf():

    if not os.path.exists(CFG.RES_DIR):
        os.makedirs(CFG.RES_DIR)

    yield

    pltlib.close("all")


def test_mexican(plottingf):
    fs = 100.0
    t1 = 1.0
    n = round(t1 * fs) + 1
    t = np.linspace(0, t1, n)

    cr = templating.mexican(n, fs)

    assert len(cr) == n
    assert pytest.approx(cr[0]) == 0
    assert pytest.approx(cr[-1]) == 0
    assert pytest.approx(np.sum(cr**2) / fs) == 1.0

    fig, axs = pltlib.subplots()
    axs.plot(t, cr, lw=3, c="k")
    axs.set(xlabel="Time [s]", ylabel="Amplitude [a.u.]")
    fig.tight_layout()
    fig.savefig(os.path.join(CFG.RES_DIR, "sombrero"))


def test_uniform_wavelet():
    wavelet = np.array([0, 1.0, 0.5])
    er = np.array([0, 1.0, 0.0])

    cr = templating.uniform_wavelet(wavelet)

    assert np.allclose(cr, er)
