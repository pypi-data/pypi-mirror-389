"""
Parametric Sweep and Performance Evaluation
===========================================

@author A. Schaer, H. Maurenbrecher
@copyright Magnes AG, (C) 2025
"""

import argparse
import dataclasses
import logging
import os
import pickle
import time

import matplotlib.pyplot as pltlib
import numpy as np

from martrem.aux import templating
from scripts import singlerun
from scripts.exper import expdm


logger = logging.getLogger(__name__)


class CFG:
    FILE_DIR = os.path.dirname(__file__)
    RES_DIR = os.path.join(FILE_DIR, "res", "sweep")
    RES_FN = os.path.join(RES_DIR, "sweep-res.pkl")
    LOG_LEVEL = logging.INFO
    PLT_RC = {
        "font": {"size": 16},
        "savefig": {"format": "svg", "dpi": 300},
        "axes": {"spines.right": False, "spines.top": False},
        "lines": {"linewidth": 0.75},
    }
    NREPS = 100
    GAMMAS = np.array([2, 3, 4, 5, 6, 7, 8])
    SIGMAS = np.array([0.1, 0.5, 1.0, 1.5, 2.0])
    RANDOMIZE_DATA = True

    class DATA:
        FS = 250.0
        X_PEAK_FREQS = [10.7, 27, 62.5]
        X_PEAK_WIDTHS = [1.0, 2.0, 1.0]
        NBEATS = 100
        SEED = None
        HPF_FCO = 0.1

    class RANDOMIZATION:
        NFREQ_MIN = 1
        NFREQ_MAX = 10
        MIN_FREQ = 1.0
        MAX_FREQ = 120.0
        MIN_FW = 1.0
        MAX_FW_FACTOR = 0.5

        assert MIN_FREQ > 0.0, "Minimum peak frequency must be positive"
        assert MIN_FW > 0.0, "Minimum frequency peak width must be positive"

    class CLEANING:
        FS = 250.0
        TPSI = 0.1
        NPSI = round(FS * TPSI) + 1
        PSI_BOUND = 6
        PSI = templating.mexican(NPSI, fs=FS, bound=PSI_BOUND)
        NTAU = 2 * NPSI
        XCORR_MIN_PEAK_DIST = round(60 / 180 * FS)
        AUTOENCODER_FN = os.path.join(
            os.path.dirname(__file__), "res", "autoenc", "autoencoder.pkl"
        )

    assert DATA.FS == CLEANING.FS, "Make sure to specify matching sampling frequencies!"
    assert (
        NREPS > 1
    ), "It is expected that more than one dataset is evaluated over the entire search grid"
    assert (
        RANDOMIZATION.MAX_FREQ < 0.5 * DATA.FS
    ), "Maximum peak frequency must be below Nyquist limit"


@dataclasses.dataclass
class SweepResults:
    baseline: np.ndarray
    res: np.ndarray
    ae_res: np.ndarray
    gammas: np.ndarray
    sigmas: np.ndarray


def setup():
    logging.basicConfig(level=CFG.LOG_LEVEL, force=True)
    logger.info(__doc__)

    logger.info("Setting up plotting library")
    for kk, vv in CFG.PLT_RC.items():
        pltlib.rc(kk, **vv)

    if not os.path.exists(CFG.RES_DIR):
        os.makedirs(CFG.RES_DIR)

    parser = argparse.ArgumentParser()
    parser.add_argument("--force", action="store_true", default=False, required=False)
    return parser.parse_args()


def dump_res(
    res: SweepResults,
    fn: str = CFG.RES_FN,
):
    """Dump results to file

    Parameters
    ----------
    res : SweepResults
        Sweep results to save
    fn : str, optional
        Filename in which to save results. Default: `CFG.RES_FN`
    """
    logger.info("Dumping results to disk")
    if not os.path.exists(os.path.dirname(fn)):
        os.makedirs(os.path.dirname(fn))

    with open(fn, "wb") as fp:
        pickle.dump(res, fp)

    logger.info(f"Saved results to {os.path.relpath(fn)}")


def load_res(fn: str = CFG.RES_FN) -> SweepResults:
    """Load results from file

    Parameters
    ----------
    fn : str, optional
        File to be loaded. Default: `CFG.RES_FN`

    Returns
    -------
    SweepResults
        Sweep results
    """
    logger.info(f"Loading sweep results from {os.path.relpath(fn)}")
    with open(fn, "rb") as fp:
        res = pickle.load(fp)

    return res


def grid_run(randomize_data: bool = True) -> tuple[
    np.ndarray[tuple[int, int], expdm.ExperimentResults],
    np.ndarray[tuple[int, int], expdm.ExperimentResults],
    np.ndarray[tuple[int, int], expdm.ExperimentResults],
]:
    """Run a single sweep over the search grid (gamma, sigma) using the same data

    Parameters
    ----------
    randomize_data : bool, optional
        Whether to randomize frequencies or peak widths before each run. Default: True

    Returns
    -------
    res : np.ndarray[tuple[int, int], expdm.ExperimentResults]
        Grid-run experiment results
    baseline : np.ndarray[tuple[int, int], expdm.ExperimentResults]
        Baseline results
    res_ae : np.ndarray[tuple[int, int], expdm.ExperimentResults]
        Autoencoder results
    """
    if randomize_data:
        nfreqs = np.random.randint(
            CFG.RANDOMIZATION.NFREQ_MIN, CFG.RANDOMIZATION.NFREQ_MAX + 1
        )
        freqs = np.random.uniform(
            CFG.RANDOMIZATION.MIN_FREQ, CFG.RANDOMIZATION.MAX_FREQ, nfreqs
        )
        ws = np.random.uniform(
            CFG.RANDOMIZATION.MIN_FW, CFG.RANDOMIZATION.MAX_FW_FACTOR * freqs, nfreqs
        )

        expcfg = expdm.ExperimentConfiguration(
            CFG.DATA.FS,
            freqs,
            ws,
            1,
            1,
            nbeats=CFG.DATA.NBEATS,
            dest=CFG.RES_DIR,
            plot=False,
        )
    else:
        expcfg = expdm.ExperimentConfiguration(
            CFG.DATA.FS,
            CFG.DATA.X_PEAK_FREQS,
            CFG.DATA.X_PEAK_WIDTHS,
            1,
            1,
            nbeats=CFG.DATA.NBEATS,
            dest=CFG.RES_DIR,
            seed=CFG.DATA.SEED,
            plot=False,
        )
    data = expdm.generate_data(expcfg)

    res = np.empty((len(CFG.GAMMAS), len(CFG.SIGMAS)), dtype=expdm.ExperimentResults)
    res_ae = np.empty((len(CFG.GAMMAS), len(CFG.SIGMAS)), dtype=expdm.ExperimentResults)
    baseline = np.empty(
        (len(CFG.GAMMAS), len(CFG.SIGMAS)), dtype=expdm.ExperimentResults
    )
    for ii, gamma in enumerate(CFG.GAMMAS):
        for jj, sigma in enumerate(CFG.SIGMAS):
            expcfg.gamma = gamma
            expcfg.sigma = sigma
            data.meta.gamma = gamma
            data.meta.sigma = sigma
            logger.debug(f"Evaluating on gamma {gamma:.1f}, sigma {sigma:.1f}")
            res[ii, jj], baseline[ii, jj] = (
                singlerun.run_experiment_adaptive_shape_correlation_cleaning(
                    data,
                    expcfg,
                    CFG.CLEANING.PSI.copy(),
                    CFG.CLEANING.NTAU,
                    CFG.CLEANING.XCORR_MIN_PEAK_DIST,
                )
            )
            res_ae[ii, jj], _ = singlerun.run_experiment_autoencoder_cleaning(
                data, expcfg, CFG.CLEANING.AUTOENCODER_FN
            )

    return res, baseline, res_ae


def visualize_errors_lines(
    errors: np.ndarray[tuple[int, int, int]],
    baseline: np.ndarray[tuple[int, int, int]],
    sigmas: np.ndarray,
    gammas: np.ndarray,
    key: str,
    units: str = None,
    as_baseline_delta: bool = False,
    label: str = None,
    ylims: tuple[float, float] = None,
    dest: str = CFG.RES_DIR,
):
    """Visualize errors as line plots

    Notes
    -----
    An alternative visualization could be using bars

    Parameters
    ----------
    errors : np.ndarray[tuple[int, int, int]]
        Data array of error results
    baseline : np.ndarray[tuple[int, int, int]]
        Data array of baseline results
    sigmas : np.ndarray
        Noise gain coefficients
    gammas : np.ndarray
        Artifact gain coefficients
    key : str
        Result key to plot
    units : str, optional
        Units to put in the plot's y-label. Default: None
    as_baseline_delta : bool, optional
        Whether to plot the difference to the baseline. Default: False
    label : str, optional
        Additional identifier. Default: None
    ylims : tuple[float, float], optional
        y limits of the generated plot. Default: None
    dest : str, optional
        Directory to save generated plot. Default: `CFG.RES_DIR`
    """
    msg = f"Visualizing {key}"
    if as_baseline_delta:
        msg += " as baseline delta (estimation error - baseline error)"

    if label:
        msg += f" [{label}]"

    logger.info(msg)
    colors = pltlib.cm.YlGnBu_r(np.linspace(0, 0.7, len(sigmas)))
    ylabel = key
    if isinstance(units, str):
        ylabel = " ".join([ylabel, units])

    if as_baseline_delta:
        ylabel = r"$\Delta$" + ylabel

    fig, axs = pltlib.subplots(figsize=(8, 5))
    mean = np.nanmean(errors, axis=-1)
    bmean = np.nanmean(baseline, axis=-1)
    mean_delta = mean - bmean
    for si, sigma in enumerate(sigmas):
        for rk in range(errors.shape[2]):
            if as_baseline_delta:
                y = errors[:, si, rk] - baseline[:, si, rk]
            else:
                y = errors[:, si, rk]

            axs.plot(gammas, y, c=colors[si], alpha=0.1, zorder=1)

        if as_baseline_delta:
            axs.plot(
                gammas,
                mean_delta[:, si],
                c=colors[si],
                label=rf"$\sigma$: {sigma:.1f}",
                lw=1.5,
                zorder=10,
            )

        else:
            axs.plot(
                gammas,
                mean[:, si],
                c=colors[si],
                label=rf"$\sigma$: {sigma:.1f}",
                lw=1.5,
            )
            axs.plot(
                gammas,
                bmean[:, si],
                c=colors[si],
                ls="--",
                lw=1.5,
            )

    axs.legend(loc="upper left", bbox_to_anchor=(1, 1))
    axs.set(xlim=(gammas[0], gammas[-1]), xlabel=r"$\gamma$ [-]", ylabel=ylabel)
    if ylims:
        axs.set_ylim(ylims)

    fig.tight_layout()
    fn = os.path.join(dest, f"sweep-{key.lower()}")
    if as_baseline_delta:
        fn = fn + "-baseline-delta"

    if label:
        fn = fn + f"-{label}"

    fig.savefig(fn)
    logger.info(f"Saved figure to {os.path.relpath(fn)}")


def visualize_classification_performance(
    res: np.ndarray[tuple[int, int, int]],
    sigmas: np.ndarray,
    gammas: np.ndarray,
    key: str,
    rev_cm: bool = False,
    label: str = None,
    dest: str = CFG.RES_DIR,
):
    """Visualize performance results using a 2D colormap plot

    Parameters
    ----------
    res : np.ndarray[tuple[int, int, int]]
        Classification performance metric result array
    sigmas : np.ndarray
        Noise gain coefficients
    gammas : np.ndarray
        Artifact gain coefficients
    key : str
        Key/name/label of metric
    rev_cm : bool, optional
        Whether to enable colormap reversal - Enable for cases where "high" values have a negative connotation. Default: False
    label : str, optional
        Identifier, typically only used in titles. Default: None
    dest : str, optional
        Directory to save generated plot. Default: `CFG.RES_DIR`
    """
    logger.info("Visualizing classification performance")

    cm = pltlib.cm.Spectral
    if rev_cm:
        cm = pltlib.cm.Spectral_r

    median = np.median(res, axis=-1)
    p95 = np.percentile(res, 95, -1)

    for name, val in zip(("median", "p95"), (median, p95)):
        fig, axs = pltlib.subplots(figsize=(8, 5))
        axs.pcolormesh(
            gammas,
            sigmas,
            val.T,
            cmap=cm,
            vmin=0,
            vmax=1,
            shading="nearest",
        )

        maxidx = np.argmax(val)
        minidx = np.argmin(val)
        maxval = val.flatten()[maxidx]
        minval = val.flatten()[minidx]
        axs.text(
            gammas[minidx // len(sigmas)],
            sigmas[minidx % len(sigmas)],
            f"{minval:.2f}",
            va="center",
            ha="center",
        )
        axs.text(
            gammas[maxidx // len(sigmas)],
            sigmas[maxidx % len(sigmas)],
            f"{maxval:.2f}",
            va="center",
            ha="center",
        )

        axs.set(xticks=gammas, yticks=sigmas, xlabel=r"$\gamma$", ylabel=r"$\sigma$")
        cb = fig.colorbar(axs.collections[0], ax=axs)
        cb.set_label(key.upper())
        fig.tight_layout()
        fn = os.path.join(dest, f"sweep-{key}-{name}")
        if label:
            fn = fn + f"-{label}"

        fig.savefig(fn)
        logger.info(f"Saved figure to {os.path.relpath(fn)}")


def visualize_results(
    res: np.ndarray[tuple[int, int], expdm.ExperimentResults],
    baseline: np.ndarray[tuple[int, int], expdm.ExperimentResults],
    sigmas: np.ndarray,
    gammas: np.ndarray,
    label: str = None,
    dest: str = CFG.RES_DIR,
):
    """Wrapper visualization function

    Parameters
    ----------
    res : np.ndarray[tuple[int, int], expdm.ExperimentResults]
        Sweep run results
    baseline : np.ndarray[tuple[int, int], expdm.ExperimentResults]
        Sweep run baseline results
    sigmas : np.ndarray
        Noise gain coefficients
    gammas : np.ndarray
        Artifact gain coefficients
    label : str, optional
        Identifier, typically only used in titles. Default: None
    dest : str, optional
        Directory to save generated plot. Default: `CFG.RES_DIR`
    """
    transposed = expdm.extract_ndarrays_from_array_of_results(res)
    transposed_base = expdm.extract_ndarrays_from_array_of_results(baseline)

    for abd in (True, False):
        for key, units in (("rmse", "[a.u.]"), ("rmsle", "[dB]")):
            visualize_errors_lines(
                transposed[key],
                transposed_base[key],
                sigmas,
                gammas,
                key.upper(),
                units,
                as_baseline_delta=abd,
                label=label,
                ylims=(-2, 0.2),
                dest=dest,
            )

    for key, rev in zip(("tpr", "fpr"), (False, True)):
        visualize_classification_performance(
            transposed[key], sigmas, gammas, key, rev_cm=rev, label=label, dest=dest
        )


def main(force=False):
    nevals = CFG.NREPS * len(CFG.SIGMAS) * len(CFG.GAMMAS)
    res_fn = os.path.join(
        CFG.RES_DIR,
        f"2025105-{nevals}-low-noise-strict-tpr",
        f"sweep-res-{nevals}-evals.pkl",
    )

    if force or not os.path.exists(res_fn):
        logger.info("Running full sweep grid")

        res = np.empty(
            (len(CFG.GAMMAS), len(CFG.SIGMAS), CFG.NREPS), dtype=expdm.ExperimentResults
        )
        base = res.copy()
        res_ae = res.copy()
        tic = time.time()
        for kk in range(CFG.NREPS):
            logger.info(
                f"Evaluating (gamma,sigma) grid on test signal {kk+1}/{CFG.NREPS}"
            )
            res[:, :, kk], base[:, :, kk], res_ae[:, :, kk] = grid_run()

        toc = time.time()
        logger.info(
            f"Full grid evaluation for N = {nevals  } took approximately {toc-tic:.2f} seconds."
        )
        all_res = SweepResults(
            baseline=base,
            res=res,
            ae_res=res_ae,
            sigmas=CFG.SIGMAS.copy(),
            gammas=CFG.GAMMAS.copy(),
        )
        dump_res(all_res, res_fn)
        logger.info("Finished grid sweep and dumping results")

    else:
        all_res = load_res(res_fn)

    dest = os.path.dirname(res_fn)
    visualize_results(
        all_res.res, all_res.baseline, all_res.sigmas, all_res.gammas, dest=dest
    )
    visualize_results(
        all_res.ae_res,
        all_res.baseline,
        all_res.sigmas,
        all_res.gammas,
        label="autoencoder",
        dest=dest,
    )


if __name__ == "__main__":
    args = setup()
    main(force=args.force)
