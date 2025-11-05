"""
Performance evaluation module
=============================

@author A. Schaer, H. Maurenbrecher
@copyright Magnes AG, (C) 2025
"""

import numpy as np
from scipy import signal

from martrem.aux import scaling


def compute_rmse(ref: np.ndarray, est: np.ndarray) -> float:
    """Compute RMSE

    Parameters
    ----------
    ref : np.ndarray
        Reference signal
    est : np.ndarray
        Estimate signal

    Returns
    -------
    float
        Root mean squared error
    """

    return np.sqrt(np.mean(np.square(ref - est)))


def compute_rmsle(ref: np.ndarray, est: np.ndarray) -> float:
    """Compute RMSLE

    As defined in 10.3389/fnins.2021.637274

    Parameters
    ----------
    ref : np.ndarray
        Reference signal
    est : np.ndarray
        Estimate signal

    Returns
    -------
    float
        Root mean squared log error
    """
    if np.any(ref < 0) or np.any(est < 0):
        raise ValueError("Arguments must be fully non-negative")

    return np.sqrt(np.mean(np.square(scaling.power_to_db(ref / est))))


def evaluate_classification(
    ref: np.ndarray, est: np.ndarray, nevents: int = None, margin: int = 50
) -> tuple[float, float]:
    """Evaluate classification performance, compute TPR and FPR

    Parameters
    ----------
    ref : np.ndarray
        Reference signal/classes
    est : np.ndarray
        Estimated signal/classes
    nevents : int, optional
        Number of ground truth events, if not given it is estimated from the reference
    margin : int, optional
        Min. required samples between events. Default: 50

    Returns
    -------
    tpr : float
        True positive rate
    fpr : float
        False positive rate
    """
    if nevents is None:
        positives = count_events(ref)
    else:
        positives = nevents

    detected_positive_indices, _ = signal.find_peaks(
        est, distance=margin, height=np.std(est)
    )
    true_positive_indices, _ = signal.find_peaks(
        ref, distance=margin, height=np.std(ref)
    )
    true_positives = len(
        set(detected_positive_indices).intersection(true_positive_indices)
    )
    detected_positives = len(detected_positive_indices)

    false_positives = detected_positives - true_positives

    return true_positives / positives, false_positives / detected_positives


def count_events(x: np.ndarray, threshold: float = None, dmin: int = None) -> int:
    """Count events in signal

    I.e. peaks above a given height/threshold

    Parameters
    ----------
    x : np.ndarray
        Signal of interest
    threshold : float, optional
        Minimum peak height
    dmin : int, optional
        Minimum distance between peaks

    Returns
    -------
    int
        Number of events in signal
    """
    if threshold is None:
        threshold = 3 * np.std(x)

    peaks, _ = signal.find_peaks(x, height=threshold, distance=dmin)
    return len(peaks)


def construct_indicator_signal(
    x: np.ndarray, peak_height: float, indication_width: int = 25
) -> np.ndarray:
    """Construct indicator signal from input signal

    Parameters
    ----------
    x : np.ndarray
        Input signal
    peak_height : float
        Height threshold for peak detection
    indication_width : int, optional
        Width of indication around each peak. Default: 25

    Returns
    -------
    np.ndarray
        Indicator signal with peaks marked
    """
    peaks, _ = signal.find_peaks(x, height=peak_height)
    indicator = np.zeros_like(x)
    hill = signal.windows.hann(indication_width)
    for peak in peaks:
        start = max(0, peak - indication_width // 2)
        end = min(len(x), peak + (indication_width + 1) // 2)

        if end - start == indication_width:
            indicator[start:end] = hill.copy()
        elif start == 0:
            indicator[:end] = hill[-end:].copy()
        else:
            indicator[start:] = hill[: end - start].copy()

    return indicator
