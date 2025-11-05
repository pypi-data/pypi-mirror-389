"""
Single configuration run
========================

Results are computed for a fixed configuration settings. Several
runs are combined to obtain results independent from random effects.

@author A. Schaer, H. Maurenbrecher
@copyright Magnes AG, (C) 2025
"""

import dataclasses
import logging
import os

import matplotlib.pyplot as pltlib
import numpy as np
from scipy import signal

from msgu.mixture import prsynth

from martrem import cleaning
from martrem.aux import templating
from martrem.aux import scaling
from martrem.autoenc import autoencoder as ae

from scripts.exper import perfeval


class CFG:
    LOG_LEVEL: int = logging.INFO
    FILE_DIR: str = os.path.dirname(__file__)
    RES_DIR: str = os.path.join(FILE_DIR, "res", "single-cfg")
    AE_FN: str = os.path.join(FILE_DIR, "res", "autoenc", "autoencoder.pkl")

    class SIM:
        FS: float = 250.0
        N_RUNS: int = 100
        N_BEATS: int = 50
        SIGMA: float = 0.5
        GAMMA: float = 8.0
        FREQS: list[float] = [13.0, 37.0]
        WIDTHS: list[float] = [2.0, 4.2]
        ST_DURATION: float = 0.08
        N_ST: int = round(ST_DURATION * FS) + 1
        N_TAU: int = 2 * N_ST
        F_CO_HP: float = 0.1
        MIN_PEAK_DIST: int = round(60 / 180 * FS)

        assert len(FREQS) == len(WIDTHS)

    class FFT:
        NFFT = 512
        NPERSEG = NFFT

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
        PALETTE = CM(np.linspace(0, 0.7, 5))

        class FD_ZOOM_BOX:
            x = (5, 55)
            y = (-35, -10)


logger = logging.getLogger(__name__)


@dataclasses.dataclass
class Estimates:
    d: list[np.ndarray | float] = dataclasses.field(default_factory=list)
    x: list[np.ndarray | float] = dataclasses.field(default_factory=list)


@dataclasses.dataclass
class Evaluations:
    data: list[prsynth.SynthData | float] = dataclasses.field(default_factory=list)
    wt: Estimates = dataclasses.field(default_factory=Estimates)
    ae: Estimates = dataclasses.field(default_factory=Estimates)

    @property
    def n(self) -> int:
        return len(self.data)

    def append(
        self,
        data: prsynth.SynthData,
        xhwt: np.ndarray,
        dhwt: np.ndarray,
        xhae: np.ndarray,
        dhae: np.ndarray,
    ):
        self.data.append(data)
        self.wt.x.append(xhwt)
        self.wt.d.append(dhwt)
        self.ae.x.append(xhae)
        self.ae.d.append(dhae)

    def __iter__(self):
        for ii in range(self.n):
            yield self.data[ii], self.wt.x[ii], self.wt.d[ii], self.ae.x[ii], self.ae.d[
                ii
            ]


def setup():
    logging.basicConfig(level=CFG.LOG_LEVEL)
    logger.info(__doc__)

    if not os.path.exists(CFG.RES_DIR):
        os.makedirs(CFG.RES_DIR)

    logger.info("Setting up plotting library")
    for kk, vv in CFG.VIZ.PLT_RC.items():
        pltlib.rc(kk, **vv)


def evaluate_models() -> Evaluations:
    logger.info("Evaluating models")
    res = Evaluations()
    datas = []
    xhats_wt = []
    xhats_ae = []
    dhats_wt = []
    dhats_ae = []
    search_template = templating.mexican(CFG.SIM.N_ST, fs=CFG.SIM.FS)
    autoenc = ae.Autoencoder.load(CFG.AE_FN)

    for ii in range(CFG.SIM.N_RUNS):
        logger.info(f"Running simulation {ii+1}/{CFG.SIM.N_RUNS}")
        data = prsynth.generate_synthetic_wave_with_cardiac_artifacts(
            CFG.SIM.FS,
            CFG.SIM.FREQS,
            CFG.SIM.WIDTHS,
            CFG.SIM.GAMMA,
            CFG.SIM.SIGMA,
            nbeats=CFG.SIM.N_BEATS,
        )
        xhat_wt, dhat_wt = cleaning.clean_with_adaptive_shape_correlation(
            data.z,
            data.fs,
            search_template,
            CFG.SIM.N_TAU,
            CFG.SIM.F_CO_HP,
            CFG.SIM.MIN_PEAK_DIST,
        )
        xhats_wt.append(xhat_wt)
        dhats_wt.append(dhat_wt)

        dhat_ae = autoenc(data.z)
        xhat_ae = data.z - dhat_ae
        xhats_ae.append(xhat_ae)
        dhats_ae.append(dhat_ae)

        datas.append(data)

        res.append(data, xhat_wt, dhat_wt, xhat_ae, dhat_ae)

    return res


def quantify_results(evaluations: Evaluations):
    logger.info("Quantifying results")
    rmse = Evaluations()
    rmsle = Evaluations()
    tpr = Evaluations()
    fpr = Evaluations()
    WELCH_KWARGS = dict(fs=CFG.SIM.FS, nperseg=CFG.FFT.NPERSEG)
    for d, xhwt, dhwt, xhae, dhae in evaluations:
        _, X = signal.welch(d.x, **WELCH_KWARGS)
        _, Z = signal.welch(d.z, **WELCH_KWARGS)
        _, D = signal.welch(d.meta.gamma * d.d, **WELCH_KWARGS)
        _, XHWT = signal.welch(xhwt, **WELCH_KWARGS)
        _, DHWT = signal.welch(dhwt, **WELCH_KWARGS)
        _, XHAE = signal.welch(xhae, **WELCH_KWARGS)
        _, DHAE = signal.welch(dhae, **WELCH_KWARGS)
        rmse_b = perfeval.compute_rmse(d.x, d.z)
        rmsle_b = perfeval.compute_rmsle(X, Z)
        rmse_wt = perfeval.compute_rmse(d.x, xhwt)
        rmsle_wt = perfeval.compute_rmsle(X, XHWT)
        rmse_ae = perfeval.compute_rmse(d.x, xhae)
        rmsle_ae = perfeval.compute_rmsle(X, XHAE)
        drmse_wt = perfeval.compute_rmse(d.meta.gamma * d.d, dhwt)
        drmsle_wt = perfeval.compute_rmsle(D, DHWT)
        drmse_ae = perfeval.compute_rmse(d.meta.gamma * d.d, dhae)
        drmsle_ae = perfeval.compute_rmsle(D, DHAE)

        tpr_wt, fpr_wt = perfeval.evaluate_classification(
            d.d, dhwt, margin=round(d.fs / 10)
        )
        tpr_ae, fpr_ae = perfeval.evaluate_classification(
            d.d, dhae, margin=round(d.fs / 10)
        )
        rmse.append(rmse_b, rmse_wt, drmse_wt, rmse_ae, drmse_ae)
        rmsle.append(rmsle_b, rmsle_wt, drmsle_wt, rmsle_ae, drmsle_ae)
        tpr.append(None, None, tpr_wt, None, tpr_ae)
        fpr.append(None, None, fpr_wt, None, fpr_ae)

    rmse_b = np.array(rmse_b)
    rmsle_b = np.array(rmsle_b)
    rmse_wt = np.array(rmse_wt)
    rmsle_wt = np.array(rmsle_wt)
    drmse_wt = np.array(drmse_wt)
    drmsle_wt = np.array(drmsle_wt)
    tpr_wt = np.array(tpr_wt)
    fpr_wt = np.array(fpr_wt)
    rmse_ae = np.array(rmse_ae)
    rmsle_ae = np.array(rmsle_ae)
    drmse_ae = np.array(drmse_ae)
    drmsle_ae = np.array(drmsle_ae)
    tpr_ae = np.array(tpr_ae)
    fpr_ae = np.array(fpr_ae)

    logger.info("###### WT performance (median, P95, ∆ median, ∆ P95) ######")
    delta = np.array(rmse.wt.x) - np.array(rmse.data)
    logger.info(
        f"x RMSE: {np.median(rmse.wt.x)}, {np.percentile(rmse.wt.x, 95)}, {np.median(delta)}, {np.percentile(delta, 95)}"
    )
    delta = np.array(rmsle.wt.x) - np.array(rmsle.data)
    logger.info(
        f"x RMSLE: {np.median(rmsle.wt.x)}, {np.percentile(rmsle.wt.x, 95)}, {np.median(delta)}, {np.percentile(delta, 95)}"
    )
    logger.info(
        f"d RMSE: {np.median(rmse.wt.d)}, {np.percentile(rmse.wt.d, 95)}, NA, NA"
    )
    logger.info(
        f"d RMSLE: {np.median(rmsle.wt.d)}, {np.percentile(rmsle.wt.d, 95)}, NA, NA"
    )
    logger.info(f"d TPR: {np.median(tpr.wt.d)}, {np.percentile(tpr.wt.d, 95)}, NA, NA")
    logger.info(f"d FPR: {np.median(fpr.wt.d)}, {np.percentile(fpr.wt.d, 95)}, NA, NA")

    logger.info("###### AE performance (median, P95, ∆ median, ∆ P95) ######")
    delta = np.array(rmse.ae.x) - np.array(rmse.data)
    logger.info(
        f"x RMSE: {np.median(rmse.ae.x)}, {np.percentile(rmse.ae.x, 95)}, {np.median(delta)}, {np.percentile(delta, 95)}"
    )
    delta = np.array(rmsle.ae.x) - np.array(rmsle.data)
    logger.info(
        f"x RMSLE: {np.median(rmsle.ae.x)}, {np.percentile(rmsle.ae.x, 95)}, {np.median(delta)}, {np.percentile(delta, 95)}"
    )
    logger.info(
        f"d RMSE: {np.median(rmse.ae.d)}, {np.percentile(rmse.ae.d, 95)}, NA, NA"
    )
    logger.info(
        f"d RMSLE: {np.median(rmsle.ae.d)}, {np.percentile(rmsle.ae.d, 95)}, NA, NA"
    )
    logger.info(f"d TPR: {np.median(tpr.ae.d)}, {np.percentile(tpr.ae.d, 95)}, NA, NA")
    logger.info(f"d FPR: {np.median(fpr.ae.d)}, {np.percentile(fpr.ae.d, 95)}, NA, NA")
    logger.info("###### ###### ###### ###### ###### ###### ######")


def draw_box_on_axs(x: tuple[float, float], y: tuple[float, float], axs: pltlib.Axes):
    return axs.plot(
        [x[0], x[1], x[1], x[0], x[0]], [y[0], y[0], y[1], y[1], y[0]], c="black"
    )


def visualize_results(
    data: list[prsynth.SynthData],
    xhats_wt: list[np.ndarray],
    dhats_wt: list[np.ndarray],
    xhats_ae: list[np.ndarray],
    dhats_ae: list[np.ndarray],
):
    logger.info("Visualizing results")
    WELCH_KWARGS = dict(fs=CFG.SIM.FS, nperseg=CFG.FFT.NPERSEG)

    Z = [signal.welch(d.z, **WELCH_KWARGS) for d in data]
    D = [signal.welch(d.meta.gamma * d.d, **WELCH_KWARGS) for d in data]
    X = [signal.welch(d.x, **WELCH_KWARGS) for d in data]
    DHAT_WT = [signal.welch(d, **WELCH_KWARGS) for d in dhats_wt]
    DHAT_AE = [signal.welch(d, **WELCH_KWARGS) for d in dhats_ae]
    XHAT_WT = [signal.welch(x, **WELCH_KWARGS) for x in xhats_wt]
    XHAT_AE = [signal.welch(x, **WELCH_KWARGS) for x in xhats_ae]
    fDhat_wt, Dhat_wt = zip(*DHAT_WT)
    fDhat_ae, Dhat_ae = zip(*DHAT_AE)
    fXhat_wt, Xhat_wt = zip(*XHAT_WT)
    fXhat_ae, Xhat_ae = zip(*XHAT_AE)
    fX, X = zip(*X)
    fD, D = zip(*D)
    fZ, Z = zip(*Z)
    fN = fD[0][1:]
    # 0.25 = 1/2**2 to compensate single sided scaling
    N = 0.25 * data[0].meta.sigma**2 / fN

    logger.info("Plotting median disturbance estimation in frequency domain")
    fig, axs = pltlib.subplots(figsize=CFG.VIZ.WIDE_FIG_SIZE)
    axs.plot(fN, scaling.power_to_db(N), c="black", ls=":")
    axs.plot(
        fD[0],
        scaling.power_to_db(np.median(D, axis=0)),
        c=CFG.VIZ.PALETTE[-1],
        lw=2,
        label="$d$",
    )
    axs.plot(
        fDhat_wt[0],
        scaling.power_to_db(np.median(Dhat_wt, axis=0)),
        c=CFG.VIZ.PALETTE[0],
        lw=2,
        label="WT",
    )
    axs.plot(
        fDhat_ae[0],
        scaling.power_to_db(np.median(Dhat_ae, axis=0)),
        c=CFG.VIZ.PALETTE[3],
        lw=2,
        label="AE",
        ls="--",
    )

    axs.legend(loc="upper right", ncols=3)
    axs.set(
        xlim=CFG.VIZ.FD_ZOOM_BOX.x,
        ylim=CFG.VIZ.FD_ZOOM_BOX.y,
        xlabel="Frequency [Hz]",
        ylabel="PSD [dB/Hz]",
    )
    fig.tight_layout()
    fig.savefig(os.path.join(CFG.RES_DIR, "disturbance-estimation-performance-fd-zoom"))
    axs.set(
        xlim=(0, CFG.SIM.FS / 2),
        ylim=(-70, 0),
        xticks=[0, CFG.SIM.FS / 2],
        yticks=[-70, 0],
    )
    fig.set_size_inches(*CFG.VIZ.NARROW_FIG_SIZE)
    fig.tight_layout()
    axs.legend(ncols=1)
    fig.savefig(os.path.join(CFG.RES_DIR, "disturbance-estimation-performance-fd-full"))
    axs.legend([])
    draw_box_on_axs(CFG.VIZ.FD_ZOOM_BOX.x, CFG.VIZ.FD_ZOOM_BOX.y, axs)
    fig.savefig(os.path.join(CFG.RES_DIR, "disturbance-estimation-performance-fd"))

    logger.info("Plotting median signal estimation in frequency domain")
    fig, axs = pltlib.subplots(figsize=CFG.VIZ.WIDE_FIG_SIZE)
    axs.plot(fN, scaling.power_to_db(N), c="black", ls=":")
    axs.plot(
        fZ[0],
        scaling.power_to_db(np.median(Z, axis=0)),
        c="black",
        lw=2,
        label="$z$",
        ls="--",
    )
    axs.plot(
        fX[0],
        scaling.power_to_db(np.median(X, axis=0)),
        c=CFG.VIZ.PALETTE[-1],
        lw=2,
        label="$x$",
    )
    axs.plot(
        fXhat_wt[0],
        scaling.power_to_db(np.median(Xhat_wt, axis=0)),
        c=CFG.VIZ.PALETTE[0],
        lw=2,
        label="WT",
    )
    axs.plot(
        fXhat_ae[0],
        scaling.power_to_db(np.median(Xhat_ae, axis=0)),
        c=CFG.VIZ.PALETTE[3],
        lw=2,
        label="AE",
        ls="--",
    )

    axs.legend(loc="upper right", ncols=4)
    axs.set(
        xlim=CFG.VIZ.FD_ZOOM_BOX.x,
        ylim=CFG.VIZ.FD_ZOOM_BOX.y,
        xlabel="Frequency [Hz]",
        ylabel="PSD [dB/Hz]",
    )
    fig.tight_layout()
    fig.savefig(os.path.join(CFG.RES_DIR, "signal-estimation-performance-fd-zoom"))
    axs.set(
        xlim=(0, CFG.SIM.FS / 2),
        ylim=(-70, 0),
        xticks=[0, CFG.SIM.FS / 2],
        yticks=[-70, 0],
    )
    fig.set_size_inches(*CFG.VIZ.NARROW_FIG_SIZE)
    fig.tight_layout()
    axs.legend(ncols=1)
    fig.savefig(os.path.join(CFG.RES_DIR, "signal-estimation-performance-fd-full"))
    axs.legend([])
    draw_box_on_axs(CFG.VIZ.FD_ZOOM_BOX.x, CFG.VIZ.FD_ZOOM_BOX.y, axs)
    fig.savefig(os.path.join(CFG.RES_DIR, "signal-estimation-performance-fd"))


def main():
    res = evaluate_models()
    quantify_results(res)
    visualize_results(res.data, res.wt.x, res.wt.d, res.ae.x, res.ae.d)

    pltlib.close("all")


if __name__ == "__main__":
    setup()
    main()
