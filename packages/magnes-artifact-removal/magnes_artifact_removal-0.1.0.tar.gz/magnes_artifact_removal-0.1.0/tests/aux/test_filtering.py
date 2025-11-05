"""
Test Filtering Auxiliary Tool
=============================

@author A. Schaer, H. Maurenbrecher
@copyright Magnes AG, (C) 2025
"""

import os

import matplotlib.pyplot as pltlib
import numpy as np
import pytest

from msgu.noise import noise

from martrem.aux import filtering


class CFG:
    FILE_DIR = os.path.dirname(__file__)
    DATA_DIR = os.path.join(FILE_DIR, "data")
    RES_DIR = os.path.join(FILE_DIR, "res", "filtering")
    PLTLIB_RC: dict = {"savefig": {"dpi": 300, "format": "jpg"}}


@pytest.fixture
def plottingf():
    for kk, vv in CFG.PLTLIB_RC.items():
        pltlib.rc(kk, **vv)

    if not os.path.exists(CFG.RES_DIR):
        os.makedirs(CFG.RES_DIR)

    yield

    pltlib.close("all")


class TestFiltersOnWhiteNoise:
    t1 = 100
    fs = 100.0
    n = round(t1 * fs) + 1
    t = np.linspace(0, t1, n)
    wn = noise.generate_white_noise(n)

    def freqresp_plot(self, x, xf, fcs=None):
        X = np.abs(np.fft.rfft(x, norm="ortho")) ** 2
        XF = np.abs(np.fft.rfft(xf, norm="ortho")) ** 2
        f = np.fft.rfftfreq(self.n, d=1.0 / self.fs)
        todB = lambda x: 10 * np.log10(x)

        fig, axs = pltlib.subplots()
        axs.plot(f, todB(X), label="Unfiltered", c="k")
        axs.plot(f, todB(XF), label="Filtered", c="deepskyblue", ls=":")
        axs.plot(f, todB(filtering.maf(XF, 10)), lw=2, c="orange")
        axs.axhline(-3, color="red", ls="--")
        axs.legend(loc="lower left")
        if fcs:
            for fc in fcs:
                axs.axvline(fc, color="r", linestyle="--")

        axs.set(
            xlabel="Frequency [Hz]",
            ylabel="PSD [dB/Hz]",
            xlim=(0, self.fs / 2),
            ylim=(-40, 10),
        )
        fig.tight_layout()

        return fig

    def test_lowpass(self, plottingf):
        fc = 30.0
        xf = filtering.lowpass(self.wn, self.fs, fc)
        fig = self.freqresp_plot(self.wn, xf, [fc])
        fig.savefig(os.path.join(CFG.RES_DIR, "lowpass-white-noise"))

    def test_highpass(self, plottingf):
        fc = 10.0
        xf = filtering.highpass(self.wn, self.fs, fc)
        fig = self.freqresp_plot(self.wn, xf, [fc])
        fig.savefig(os.path.join(CFG.RES_DIR, "highpass-white-noise"))

    def test_bandpass(self, plottingf):
        fc = [15, 20]
        xf = filtering.bandpass(self.wn, self.fs, fc)
        fig = self.freqresp_plot(self.wn, xf, fc)
        fig.savefig(os.path.join(CFG.RES_DIR, "bandpass-white-noise"))

    def test_notch(self, plottingf):
        fc = 25.0
        xf = filtering.notch(self.wn, self.fs, fc)
        fig = self.freqresp_plot(self.wn, xf, [fc])
        fig.savefig(os.path.join(CFG.RES_DIR, "notch-white-noise"))

    def test_maf(self, plottingf):
        n = 20
        xf = filtering.maf(self.wn, n)
        fig = self.freqresp_plot(self.wn, xf)
        fig.savefig(os.path.join(CFG.RES_DIR, "maf-white-noise"))
