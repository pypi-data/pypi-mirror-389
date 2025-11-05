"""
Run an artifact removal experiment
==================================

@author A. Schaer, H. Maurenbrecher
@copyright Magnes AG, (C) 2025
"""

import logging
import os
import time

import matplotlib.pyplot as pltlib
import numpy as np
from scipy import signal


from msgu.mixture import prsynth

from martrem import cleaning
from martrem.aux import templating
from martrem.aux import scaling
from martrem.autoenc import autoencoder as ae
from scripts.exper import expdm
from scripts.exper import perfeval


class CFG:
    FILE_DIR = os.path.dirname(__file__)
    RES_DIR = os.path.join(FILE_DIR, "res", "single-run")
    LOG_LEVEL = logging.INFO
    PLT_RC = {
        "font": {"size": 16},
        "savefig": {"format": "jpg", "dpi": 300},
        "axes": {"spines.right": False, "spines.top": False},
        "lines": {"linewidth": 0.75},
    }

    class DEFAULTS:
        FS = 250.0
        X_PEAK_FREQS = [10.7, 27, 62.5]
        X_PEAK_WIDTHS = [1.0, 2.0, 1.0]
        GAMMA = 5.0
        SIGMA = 2.0
        NBEATS = 100
        SEED = 0
        HPF_FCO = 0.1

    class FFT:
        NPERSEG = 500
        NFFT = 1000

    class ADAPTIVE_TEMPLATE:
        PSI_T = 0.1
        TAU_EXTENSION_FACTOR = 2

    class VIZ:
        ZOOM_SPAN = 4
        XSTYLE = dict(c="black", ls="-", zorder=100, label="$x$")
        ZSTYLE = dict(c="gray", lw=1.5, zorder=10, label="$z$")
        DSTYLE = dict(c="red", lw=1.2, zorder=50, label="$d$")
        NSTYLE = dict(c="magenta", lw=1.5, ls=":", zorder=60, label="$n$")
        YSTYLE = dict(c="deepskyblue", ls="-", lw=1.2, zorder=30, label=r"$\hat{x}$")
        ASTYLE = dict(c="black", ls="-.", zorder=60, label=r"$\hat{d}$")
        LEGENDS_ON = True
        ANNOTATE_SIGMA_GAMMA = True
        DB_LIMS = (-40, 0)


logger = logging.getLogger(__name__)


def setup():
    logging.basicConfig(level=CFG.LOG_LEVEL)
    logger.info(__doc__)

    logger.info("Setting up plotting library")
    for kk, vv in CFG.PLT_RC.items():
        pltlib.rc(kk, **vv)


def visualize_results_time_domain(
    data: prsynth.SynthData,
    y: np.ndarray,
    a: np.ndarray,
    expcfg: expdm.ExperimentConfiguration,
    label: str = None,
):
    """Visualize data and results in time domain

    Parameters
    ----------
    data : prsynth.SynthData
        Experiment signals and meta-information
    y : np.ndarray
        Result estimate of signal-to-clean
    a : np.ndarray
        Result estimate of artifacts
    expcfg : expdm.ExperimentConfiguration
        Experiment configuration object
    label : str, optional
        Additional identifier
    """
    tm = 0.5 * (data.t[0] + data.t[-1])
    d_offset = np.min(data.z) - 2 * data.meta.gamma
    fig, axs = pltlib.subplots(figsize=(8, 5))
    axs.plot(data.t, data.z, **CFG.VIZ.ZSTYLE)
    axs.plot(data.t, y, **CFG.VIZ.YSTYLE)
    axs.plot(data.t, data.x, **CFG.VIZ.XSTYLE)
    axs.plot(data.t, data.meta.gamma * data.d + d_offset, **CFG.VIZ.DSTYLE)
    axs.plot(data.t, a + d_offset, **CFG.VIZ.ASTYLE)

    if CFG.VIZ.LEGENDS_ON:
        axs.legend(loc="upper left", bbox_to_anchor=(1, 1))

    if CFG.VIZ.ANNOTATE_SIGMA_GAMMA:
        axs.text(
            0.95,
            0.95,
            rf"$\gamma = {data.meta.gamma:.1f}$, $\sigma = {data.meta.sigma:.1f}$",
            transform=axs.transAxes,
            ha="right",
            va="top",
        )

    axs.set(xlim=(data.t[0], data.t[-1]), xlabel="Time [s]", ylabel="Signals [a.u.]")
    fig.tight_layout()
    basename = "time-domain-visualization" + ("-" + label if label else "")
    fn = os.path.join(expcfg.dest, basename)
    fig.savefig(fn)
    logger.info(f"Saved figure to {os.path.relpath(fn)}")

    axs.set(xlim=(tm - CFG.VIZ.ZOOM_SPAN * 0.5, tm + CFG.VIZ.ZOOM_SPAN * 0.5))
    fn = os.path.join(expcfg.dest, basename + "-zoom")
    fig.savefig(fn)
    logger.info(f"Saved figure to {os.path.relpath(fn)}")


def visualize_results_frequency_domain(
    data: prsynth.SynthData,
    y: np.ndarray,
    a: np.ndarray,
    expcfg: expdm.ExperimentConfiguration,
    label: str = None,
):
    """Visualize results in frequency domain

    Parameters
    ----------
    data : prsynth.SynthData
        Experiment signals and meta-information
    y : np.ndarray
        Result estimate of signal-to-clean
    a : np.ndarray
        Result estimate of artifacts
    expcfg : expdm.ExperimentConfiguration
        Experiment configuration object
    label : str, optional
        Additional identifier
    """
    welch_kwargs = dict(nperseg=CFG.FFT.NPERSEG, nfft=CFG.FFT.NFFT)
    fx, Px = signal.welch(data.x, data.fs, **welch_kwargs)
    fxn, Pxn = signal.welch(data.x + data.meta.sigma * data.n, data.fs, **welch_kwargs)
    fd, Pd = signal.welch(data.meta.gamma * data.d, data.fs, **welch_kwargs)
    fn, Pn = signal.welch(data.meta.sigma * data.n, data.fs, **welch_kwargs)
    fz, Pz = signal.welch(data.z, data.fs, **welch_kwargs)
    fy, Py = signal.welch(y, data.fs, **welch_kwargs)
    fa, Pa = signal.welch(a, data.fs, **welch_kwargs)

    fig, axs = pltlib.subplots(figsize=(8, 5))
    axs.plot(fx, scaling.power_to_db(Px), **CFG.VIZ.XSTYLE)
    axs.plot(fn, scaling.power_to_db(Pn), **CFG.VIZ.NSTYLE)
    # axs.plot(fxn, scaling.power_to_db(Pxn), **CFG.VIZ.XSTYLE)
    axs.plot(fd, scaling.power_to_db(Pd), **CFG.VIZ.DSTYLE)
    axs.plot(fz, scaling.power_to_db(Pz), **CFG.VIZ.ZSTYLE)
    axs.plot(fy, scaling.power_to_db(Py), **CFG.VIZ.YSTYLE)
    axs.plot(fa, scaling.power_to_db(Pa), **CFG.VIZ.ASTYLE)
    axs.set(
        xlim=(0, data.fs / 2),
        ylim=CFG.VIZ.DB_LIMS,
        xlabel="Frequency [Hz]",
        ylabel="PSD [dB/Hz]",
    )
    if CFG.VIZ.LEGENDS_ON:
        axs.legend(loc="upper left", bbox_to_anchor=(1, 1))

    if CFG.VIZ.ANNOTATE_SIGMA_GAMMA:
        axs.text(
            0.95,
            0.95,
            rf"$\gamma = {data.meta.gamma:.1f}$, $\sigma = {data.meta.sigma:.1f}$",
            transform=axs.transAxes,
            ha="right",
            va="top",
        )

    fig.tight_layout()
    basename = "frequency-domain-visualization" + ("-" + label if label else "")
    filename = os.path.join(expcfg.dest, basename)
    fig.savefig(filename)
    logger.info(f"Saved figure to {os.path.relpath(filename)}")


def run_experiment_adaptive_shape_correlation_cleaning(
    data: prsynth.SynthData,
    expcfg: expdm.ExperimentConfiguration,
    psi: np.ndarray,
    n_tau: int,
    xcorr_min_pdist: int,
) -> tuple[expdm.ExperimentResults, expdm.ExperimentResults]:
    """Run single experiment

    Parameters
    ----------
    data : prsynth.SynthData
        Signal data used in experiment
    expcfg : expdm.ExperimentConfiguration
        Experiment configuration
    psi : np.ndarray
        Artifact template for artifact localization
    n_tau : int
        Length of artifact template to be estimated from data
    xcorr_min_pdist : int
        Minimum distance between detected peaks in the cross-correlation function

    Returns
    -------
    res : expdm.ExperimentResults
        Experiment results
    baseline : expdm.ExperimentResults
        Baseline results
    """
    xhat, dhat = cleaning.clean_with_adaptive_shape_correlation(
        data.z,
        data.fs,
        psi,
        n_tau,
        CFG.DEFAULTS.HPF_FCO,
        xcorr_min_peak_distance=xcorr_min_pdist,
    )
    res, baseline = evaluate_results(data, xhat, dhat, expcfg)

    if expcfg.plot:
        visualize_results_time_domain(data, xhat, dhat, expcfg)
        visualize_results_frequency_domain(data, xhat, dhat, expcfg)

    return res, baseline


def run_experiment_autoencoder_cleaning(
    data: prsynth.SynthData,
    expcfg: expdm.ExperimentConfiguration,
    modelfn: str,
) -> tuple[expdm.ExperimentResults, expdm.ExperimentResults]:
    """Run an experiment where the autoencoder is used to clean the synthetic signal data

    Parameters
    ----------
    data : prsynth.SynthData
        Data to be cleaned
    expcfg : expdm.ExperimentConfiguration
        Experiment configuration
    modelfn : str
        Binary model file name (with path)

    Returns
    -------
    res : expdm.ExperimentResults
        Experiment results
    baseline : expdm.ExperimentResults
        Baseline results
    """
    model = ae.Autoencoder.load(modelfn)
    dhat = model(data.z)
    xhat = data.z - dhat

    res, baseline = evaluate_results(data, xhat, dhat, expcfg)

    if expcfg.plot:
        visualize_results_time_domain(data, xhat, dhat, expcfg, label="autoencoder")
        visualize_results_frequency_domain(
            data, xhat, dhat, expcfg, label="autoencoder"
        )

    return res, baseline


def evaluate_results(
    data: prsynth.SynthData,
    xhat: np.ndarray,
    dhat: np.ndarray,
    expcfg: expdm.ExperimentConfiguration,
) -> tuple[expdm.ExperimentResults, expdm.ExperimentResults]:
    """Evaluate resutls error metrics

    Parameters
    ----------
    data : prsynth.SynthData
        Input (and groundtruth) signals
    xhat : np.ndarray
        Signal estimation
    dhat : np.ndarray
        Disturbance estimation
    expcfg : expdm.ExperimentConfiguration
        Experiment configuration

    Returns
    -------
    res : expdm.ExperimentResults
        Experiment results
    baseline : expdm.ExperimentResults
        Baseline results
    """
    _, Px = signal.welch(data.x, fs=data.fs)
    _, Pxhat = signal.welch(xhat, fs=data.fs)
    _, Pz = signal.welch(data.z, fs=data.fs)

    baseline_rmse = perfeval.compute_rmse(data.x, data.z)
    baseline_rmsle = perfeval.compute_rmsle(Px, Pz)

    rmse = perfeval.compute_rmse(data.x, xhat)
    rmsle = perfeval.compute_rmsle(Px, Pxhat)
    logger.debug(f"RMSE: {rmse:.4f} (∆ = {rmse - baseline_rmse:.4f})")
    logger.debug(f"RMSLE: {rmsle:.4f} dB (∆ = {rmsle - baseline_rmsle:.4f} dB)")

    tpr, fpr = perfeval.evaluate_classification(
        data.d, dhat, nevents=expcfg.nbeats, margin=round(data.fs / 10)
    )
    res = expdm.ExperimentResults(rmse, rmsle, tpr, fpr)
    baseline = expdm.ExperimentResults(baseline_rmse, baseline_rmsle, 0.0, 1.0)

    return res, baseline


def main():
    tic = time.time()
    expcfg = expdm.ExperimentConfiguration(
        CFG.DEFAULTS.FS,
        CFG.DEFAULTS.X_PEAK_FREQS,
        CFG.DEFAULTS.X_PEAK_WIDTHS,
        gamma=CFG.DEFAULTS.GAMMA,
        sigma=CFG.DEFAULTS.SIGMA,
        nbeats=CFG.DEFAULTS.NBEATS,
        dest=CFG.RES_DIR,
        plot=True,
        seed=CFG.DEFAULTS.SEED,
    )
    logger.info(f"Generating data for configuration {expcfg.short_str}")
    data = expdm.generate_data(expcfg)
    logger.info(f"Defining search template and algorithm parameters")
    psi_n = round(CFG.ADAPTIVE_TEMPLATE.PSI_T * expcfg.fs) + 1
    tau_n = round(CFG.ADAPTIVE_TEMPLATE.TAU_EXTENSION_FACTOR * psi_n)
    psi = templating.mexican(psi_n, fs=expcfg.fs, bound=3)
    min_xcorr_peak_distance = round(60 / 180 * expcfg.fs)
    logger.info(f"Search template length: {psi_n}")
    logger.info(f"Data template length: {tau_n}")
    logger.info("Running adaptive-shape correlation cleaining experiment")
    results, baseline = run_experiment_adaptive_shape_correlation_cleaning(
        data, expcfg, psi, tau_n, min_xcorr_peak_distance
    )
    logger.info(f"Experiment results: {results}")
    logger.info(f"Baseline: {baseline}")

    try:
        logger.info("Evaluating autoencoder")
        aeres, aebaseline = run_experiment_autoencoder_cleaning(
            data,
            expcfg,
            modelfn=os.path.join(CFG.FILE_DIR, "res", "autoenc", "autoencoder.pkl"),
        )
        logger.info(f"Experiment results: {aeres}")
        logger.info(f"Baseline: {aebaseline}")
    except NotImplementedError as e:
        logger.error(e)

    except FileNotFoundError as e:
        logger.error(e)

    toc = time.time()
    logger.info(f"Ran script {__file__} in approximately {toc - tic:.4f} seconds")


if __name__ == "__main__":
    setup()
    main()
