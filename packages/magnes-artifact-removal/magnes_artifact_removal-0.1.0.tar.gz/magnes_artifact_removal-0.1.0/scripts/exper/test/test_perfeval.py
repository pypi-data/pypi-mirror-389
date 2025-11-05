"""
Test performance evaluation functions
=====================================

@author A. Schaer, H. Maurenbrecher
@copyright Magnes AG, (C) 2025
"""

import os

import matplotlib.pyplot as pltlib
import numpy as np
import pytest

from scripts.exper import perfeval


class CFG:
    FILE_DIR = os.path.dirname(__file__)
    DATA_DIR = os.path.join(FILE_DIR, "data")
    RES_DIR = os.path.join(FILE_DIR, "res", "perfeval")


@pytest.fixture
def plottingf():
    if not os.path.exists(CFG.RES_DIR):
        os.makedirs(CFG.RES_DIR)

    yield

    pltlib.close("all")


def test_construct_indicator_signal(plottingf):
    n = 1000
    width = 50
    k = np.arange(n)
    peaks = [width // 4] + [100 * ii for ii in range(1, 10)] + [n - width // 4]
    x = np.zeros(n)
    x[peaks] = 1.0

    cr = perfeval.construct_indicator_signal(x, np.std(x), width)
    assert len(cr) == n

    fig, axs = pltlib.subplots()
    axs.plot(k, x, c="red")
    axs.plot(k, cr, c="black", ls="--")
    axs.set(xlim=(0, n))
    fig.tight_layout()
    fig.savefig(os.path.join(CFG.RES_DIR, "indicator-signal"))


def test_count_events():
    n = 1000
    width = 50
    peaks = [width // 4] + [100 * ii for ii in range(1, 10)] + [n - width // 4]
    x = np.zeros(n)
    x[peaks] = 1.0

    cr = perfeval.count_events(x, np.std(x))
    assert cr == 11


def test_evaluate_classification():
    n = 1000
    w = 41
    true_peaks = [100 * ii for ii in range(1, 10)]
    truth = np.zeros(n)
    truth[true_peaks] = 1.0
    estimate_peaks = [10, 100 - w // 4, 200, 300 + w // 3, 400, 500, 700, 900 + w // 2]
    estimate = np.zeros(n)
    estimate[estimate_peaks] = 1.0
    nevents = len(true_peaks)
    expected_tpr = 4 / nevents
    expected_fpr = 4 / len(estimate_peaks)
    tpr, fpr = perfeval.evaluate_classification(truth, estimate, nevents, margin=w)
    assert pytest.approx(expected_tpr) == tpr
    assert pytest.approx(expected_fpr) == fpr
