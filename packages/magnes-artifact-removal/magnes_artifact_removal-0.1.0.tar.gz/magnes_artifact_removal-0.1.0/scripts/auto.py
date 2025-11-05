"""
Train Autoencoder for Artifact Removal
======================================

@author A. Schaer, H. Maurenbrecher
@copyright Magnes AG, (C) 2025
"""

from __future__ import annotations
import logging
import os

import matplotlib.pyplot as pltlib
import numpy as np
from scipy import signal

from msgu.mixture import prsynth
from martrem.autoenc import autoencoder
from scripts.exper import perfeval


np.random.seed(0)


class CFG:
    FILE_DIR = os.path.dirname(__file__)
    RES_DIR = os.path.join(FILE_DIR, "res", "autoenc")

    LOG_LEVEL = logging.INFO
    FS = 250.0
    PLT_RC = {
        "font": {"size": 16},
        "savefig": {"format": "jpg", "dpi": 300},
        "axes": {"spines.right": False, "spines.top": False},
        "lines": {"linewidth": 0.75},
        "figure": {"figsize": (8, 5)},
    }

    class TRAIN:
        SIGMAS = np.linspace(0, 2, 6)
        GAMMAS = np.linspace(8, 1, 6)
        NBEATS = 50
        BATCH_SIZE = 100

        class NFREQS:
            MIN = 1
            MAX = 10 + 1

            assert MIN > 0

        class FREQS:
            MIN = 1.0
            MAX = 80.0

        class WIDTHS:
            MIN = 0.01
            MAX_FRACTION = 0.1

    class TEST:
        SIGMA = 1.0
        GAMMA = 4.5
        NBEATS = 100
        FREQS = [5.2, 14.6, 62.5]
        WIDTHS = [1.0, 2.0, 1.0]

    class MODEL:
        N_IN = 125
        N_OUT = N_IN
        AUTOENC_LAYERS = (N_IN // 2,)
        HYPERP = dict(
            activation="relu",
            solver="adam",
            alpha=0.0001,
            batch_size="auto",
            learning_rate="adaptive",
            learning_rate_init=0.001,
            power_t=0.5,
            max_iter=200,
            shuffle=False,
            random_state=None,
            tol=0.001,
            verbose=False,
            warm_start=True,
            momentum=0.9,
            nesterovs_momentum=True,
            early_stopping=True,
            validation_fraction=0.1,
            beta_1=0.9,
            beta_2=0.999,
            epsilon=1e-8,
            n_iter_no_change=10,
            max_fun=15000,
        )

        assert N_IN == N_OUT


logger = logging.getLogger(__name__)


def generate_train_data() -> tuple[np.ndarray, np.ndarray]:
    """Generate training data as per script configuration

    The features are windows of the measurement z.
    The targets are windows of the noise-corrupted ground-truth,
    i.e. measurement without artifacts.

    Returns
    -------
    X : np.ndarray
        Stacks of features to be used in autoencoder training
    Y : np.ndarray
        Stacks of targets to be used in autoencoder training
    """
    x = []
    y = []
    for sigma in CFG.TRAIN.SIGMAS:
        for gamma in CFG.TRAIN.GAMMAS:
            tx = []
            ty = []
            for nfreqs in range(CFG.TRAIN.NFREQS.MIN, CFG.TRAIN.NFREQS.MAX):
                freqs = np.random.uniform(
                    CFG.TRAIN.FREQS.MIN, CFG.TRAIN.FREQS.MAX, nfreqs
                )
                widths = np.random.uniform(
                    CFG.TRAIN.WIDTHS.MIN, freqs * CFG.TRAIN.WIDTHS.MAX_FRACTION
                )
                synth = prsynth.generate_synthetic_wave_with_cardiac_artifacts(
                    CFG.FS,
                    freqs,
                    widths,
                    gamma=gamma,
                    sigma=sigma,
                    nbeats=CFG.TRAIN.NBEATS,
                )

                for stop_idx in range(
                    CFG.MODEL.N_IN, len(synth.z), CFG.MODEL.N_IN // 2
                ):
                    _x = synth.z[stop_idx - CFG.MODEL.N_IN : stop_idx]
                    _y = (
                        synth.x[stop_idx - CFG.MODEL.N_IN : stop_idx]
                        + synth.meta.sigma
                        * synth.n[stop_idx - CFG.MODEL.N_IN : stop_idx]
                    )

                    tx.append(_x)
                    ty.append(_y)

            shuffled_idx = np.random.permutation(len(tx))
            x.extend(np.array(tx)[shuffled_idx].tolist().copy())
            y.extend(np.array(ty)[shuffled_idx].tolist().copy())

    logger.info(f"Number of training samples: {len(x)}")
    return np.stack(x), np.stack(y)


def generate_test_data() -> prsynth.SynthData:
    """Generate test data

    Returns
    -------
    prsynth.SynthData
        Synthetic test data
    """
    return prsynth.generate_synthetic_wave_with_cardiac_artifacts(
        CFG.FS,
        CFG.TEST.FREQS,
        CFG.TEST.WIDTHS,
        gamma=CFG.TEST.GAMMA,
        sigma=CFG.TEST.SIGMA,
        nbeats=CFG.TEST.NBEATS,
    )


def train_model(x: np.ndarray, y: np.ndarray) -> autoencoder.Autoencoder:
    """Instantiate and train a model

    Parameters
    ----------
    x : np.ndarray
        Training features
    y : np.ndarray
        Training targets

    Returns
    -------
    autoencoder.Autoencoder
        Trained model
    """
    logger.info("Instantiating model")
    ae = autoencoder.Autoencoder(CFG.MODEL.AUTOENC_LAYERS, CFG.MODEL.HYPERP)
    logger.info("Training model...")
    ae = ae.train(x, y)
    logger.info(f"Trained model with {ae.size} parameters")
    return ae


def score_performance(
    data: prsynth.SynthData,
    xhat: np.ndarray,
    dhat: np.ndarray,
    label: str = "autoencoder",
):
    """Score and visualize performance of model

    Parameters
    ----------
    data : prsynth.SynthData
        Test data
    xhat : np.ndarray
        Signal estimate
    dhat : np.ndarray
        Artifacts estimate
    label : str, optional
        Model label/name. Default: "autoencoder"
    """
    baseline = perfeval.compute_rmse(data.z, data.x)
    rmse = perfeval.compute_rmse(xhat, data.x)
    logger.info(f"{label} estimate RMSE: {rmse:.4f} (∆ = {rmse-baseline:.4f})")

    NPERSEG = 256
    fz, Pz = signal.welch(data.z, fs=data.fs, nperseg=NPERSEG)
    fx, Px = signal.welch(data.x, fs=data.fs, nperseg=NPERSEG)
    fd, Pd = signal.welch(data.meta.gamma * data.d, fs=data.fs, nperseg=NPERSEG)
    fy, Py = signal.welch(xhat, fs=data.fs, nperseg=NPERSEG)
    fa, Pa = signal.welch(dhat, fs=data.fs, nperseg=NPERSEG)

    rmsle_artifact = perfeval.compute_rmsle(Pd, Pa)
    logger.info(f"{label} artifact RMSLE: {rmsle_artifact:.4f} dB")

    t0 = 0
    t1 = 2
    fig, axs = pltlib.subplots()
    axs.plot(data.t, data.z, c="gray", lw=2)
    axs.plot(data.t, xhat, c="deepskyblue", lw=1.5, ls="--")
    axs.plot(data.t, data.x, c="black", lw=0.75)
    axs.plot(data.t, data.meta.gamma * data.d - 10, c="red", lw=2.0, ls=":")
    axs.plot(data.t, dhat - 10, c="black", lw=0.75, ls="-.")
    axs.set(
        xlim=(t0, t1),
        xlabel="Time [s]",
        ylabel="Signal [a.u.]",
    )
    fig.tight_layout()
    fig.savefig(os.path.join(CFG.RES_DIR, f"tdcomp-{label}"))

    fig, axs = pltlib.subplots()
    axs.plot(fz, 10 * np.log10(Pz), c="gray", lw=2)
    axs.plot(fy, 10 * np.log10(Py), c="deepskyblue", lw=1.5, ls="--")
    axs.plot(fx, 10 * np.log10(Px), c="black", lw=0.75)
    axs.plot(fd, 10 * np.log10(Pd), c="red", lw=2.0, ls=":")
    axs.plot(fa, 10 * np.log10(Pa), c="black", lw=0.75, ls="-.")
    axs.set(
        xlim=(0, data.fs / 2),
        ylim=(-40, 0),
        xlabel="Frequency [Hz]",
        ylabel="PSD [dB/Hz]",
    )
    fig.tight_layout()
    fig.savefig(os.path.join(CFG.RES_DIR, f"fdcomp-{label}"))


def setup():
    logging.basicConfig(level=logging.INFO)
    logger.info(__doc__)

    if not os.path.exists(CFG.RES_DIR):
        os.makedirs(CFG.RES_DIR)

    for kk, vv in CFG.PLT_RC.items():
        pltlib.rc(kk, **vv)


def main():
    logger.info("Generating training data")
    x, y = generate_train_data()
    logger.info("Generating testing data")
    data = generate_test_data()

    logger.info("--- Artifact estimator ---")
    artifact_estimator = train_model(x, x - y)
    fn = artifact_estimator.dump(CFG.RES_DIR)
    logger.info(f"Saved trained model to {fn}")

    logger.info("Evaluating artifact estimator on test data")
    dhat_artest = artifact_estimator(data.z)
    xhat_artest = data.z - dhat_artest
    logger.info("Scoring artifact estimator")
    score_performance(data, xhat_artest, dhat_artest, label="artifact-estimator")

    pltlib.close("all")


if __name__ == "__main__":
    setup()
    main()
