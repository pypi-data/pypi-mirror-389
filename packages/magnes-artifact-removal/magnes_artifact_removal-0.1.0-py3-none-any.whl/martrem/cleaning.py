"""
Artifact removal module
=======================

@author A. Schaer, H. Maurenbrecher
@copyright Magnes AG, (C) 2025.
"""

from typing import Callable

import numpy as np
from scipy import signal

from martrem.aux import filtering
from martrem.aux import templating


def clean_with_shape_template(
    x: np.ndarray,
    fs: float,
    psi: np.ndarray,
    fco_hp: float,
    xcorr_min_peak_distance: int,
    xcorr_peak_height_std: float = 2.0,
    midres: dict = None,
) -> tuple[np.ndarray, np.ndarray]:
    """Remove artifacts from signal based on shape-template-crosscorrelation

    Parameters
    ----------
    x : np.ndarray
        Signal to clean (measurement)
    fs : float
        Sampling rate in Hz
    psi : np.ndarray
        Artifact template to be used for cleaning.
    fco_hp : float
        Cut-off frequency for high-pass filter
    xcorr_min_peak_distance : int
        Minimum distance between peak indices in the cross-correlation array
    xcorr_peak_height_std : float, optional
        Std-deviation multiplier used in peak detection in the cross-correlation array
    midres : dict, optional
        Dictionary to store intermediate results for visualization purposes.

    Returns
    -------
    corrected : np.ndarray
        Corrected cleaned signal
    artifact : np.ndarray
        Artifact
    """
    y = filtering.highpass(x.copy(), fs, fco_hp)
    xcorr = signal.correlate(y, psi, mode="same", method="direct")
    xcorr_peak_idx, _ = signal.find_peaks(
        xcorr,
        height=xcorr_peak_height_std * np.nanstd(xcorr),
        distance=xcorr_min_peak_distance,
    )
    if isinstance(midres, dict):
        midres.update(
            {
                "fs": fs,
                "y": y.copy(),
                "psi": psi.copy(),
                "xcorr": xcorr.copy(),
                "xcorr-peaks": xcorr_peak_idx.copy(),
            }
        )

    corrected = y.copy()
    n = len(psi)
    for ii in xcorr_peak_idx:
        i0 = ii - n // 2
        i1 = ii + (n + 1) // 2
        if i0 >= 0 and i1 < len(x):
            corrected[i0:i1] -= psi * xcorr[ii] / fs

    artifact = y - corrected
    return corrected, artifact


def clean_with_shape_template_multipass(
    x: np.ndarray,
    fs: float,
    psis: list[np.ndarray],
    fco_hp: float,
    xcorr_min_peak_distance: int,
    xcorr_peak_height_std: float = 2.0,
    midres: dict = None,
) -> tuple[np.ndarray, np.ndarray]:
    """Remove artifacts from signal based on shape-template-crosscorrelation using multiple templates

    Parameters
    ----------
    x : np.ndarray
        Signal to clean (measurement)
    fs : float
        Sampling rate in Hz
    psis : list[np.ndarray]
        List of artifacts templates to be used for cleaning.
    fco_hp : float
        Cut-off frequency for high-pass filter
    xcorr_min_peak_distance : int
        Minimum distance between peak indices in the cross-correlation array
    xcorr_peak_height_std : float, optional
        Std-deviation multiplier used in peak detection in the cross-correlation array
    midres : dict, optional
        Dictionary to store intermediate results for visualization purposes.

    Returns
    -------
    corrected : np.ndarray
        Corrected cleaned signal
    artifact : np.ndarray
        Artifact reconstructed from all iterations
    """
    artifact = np.zeros_like(x)
    corrected = x.copy()
    for psi in psis:
        corrected, art = clean_with_shape_template(
            corrected,
            fs,
            psi,
            fco_hp,
            xcorr_min_peak_distance,
            xcorr_peak_height_std,
            midres=midres,
        )
        artifact += art

    return corrected, artifact


def clean_with_adaptive_shape_correlation(
    x: np.ndarray,
    fs: float,
    psi: np.ndarray,
    tau_n: int,
    fco_hp: float,
    xcorr_min_peak_distance: int,
    xcorr_peak_height_std: float = 2.0,
    midres: dict = None,
) -> tuple[np.ndarray, np.ndarray]:
    """Remove artifacts from signal based on shape-template-crosscorrelation with adaptive template

    Parameters
    ----------
    x : np.ndarray
        Signal to clean (measurement)
    fs : float
        Sampling rate in Hz
    psi : np.ndarray
        Artifact search-template to be used for cleaning
    tau_n : int
        Length of artifact template to estimate from data
    fco_hp : float
        Cut-off frequency for high-pass filter
    xcorr_min_peak_distance : int
        Minimum distance between peak indices in the cross-correlation array
    xcorr_peak_height_std : float, optional
        Std-deviation multiplier used in peak detection in the cross-correlation array
    midres : dict, optional
        Dictionary to store intermediate results for visualization purposes

    Returns
    -------
    corrected : np.ndarray
        Corrected cleaned signal
    artifact : np.ndarray
        Artifact signal (disturbance estimate)
    """
    y = filtering.highpass(x.copy(), fs, fco_hp)
    xcorr = signal.correlate(y, psi, mode="same", method="direct")
    xcorr_peak_idx, _ = signal.find_peaks(
        xcorr,
        height=xcorr_peak_height_std * np.nanstd(xcorr),
        distance=xcorr_min_peak_distance,
    )
    if isinstance(midres, dict):
        midres.update(
            {
                "fs": fs,
                "y": y.copy(),
                "psi": psi.copy(),
                "xcorr": xcorr.copy(),
                "xcorr-peaks": xcorr_peak_idx.copy(),
                "template-windows": [],
            }
        )

    template = np.zeros(tau_n)
    for ii in xcorr_peak_idx:
        i0 = ii - tau_n // 2
        i1 = ii + (tau_n + 1) // 2
        if i0 >= 0 and i1 < len(x):
            if isinstance(midres, dict):
                midres["template-windows"].append(y[i0:i1].copy())

            template += y[i0:i1] / len(xcorr_peak_idx)

    template = templating.uniform_wavelet(template, fs=fs)

    if isinstance(midres, dict):
        midres["tau"] = template.copy()
        midres["tau-gains"] = []

    corrected = y.copy()
    for ii in xcorr_peak_idx:
        i0 = ii - tau_n // 2
        i1 = ii + (tau_n + 1) // 2
        if i0 >= 0 and i1 < len(x):
            gain = np.sum(y[i0:i1] * template / fs)
            if isinstance(midres, dict):
                midres["tau-gains"].append(gain)

            corrected[i0:i1] -= template * gain

    artifact = y - corrected
    return corrected, artifact
