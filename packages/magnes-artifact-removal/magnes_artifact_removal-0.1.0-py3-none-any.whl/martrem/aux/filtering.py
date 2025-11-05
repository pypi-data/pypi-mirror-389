"""
Filtering Utility
=================

@author A. Schaer, H. Maurenbrecher
@copyright Magnes AG, (C) 2025
"""

import numpy as np
from scipy import signal


def maf(x: np.ndarray, n: int) -> np.ndarray:
    """Apply moving average filter to x

    Parameters
    ----------
    x : np.ndarray
        Signal of interest
    n : int
        Size of moving average window

    Returns
    -------
    np.ndarray
        Filtered signal
    """
    kernel = np.ones(n) / n
    return np.convolve(x, kernel, mode="same")


def lowpass(x: np.ndarray, fs: float, fc: float) -> np.ndarray:
    """Apply a lowpass filter to the input signal

    Uses a second order Butterworth filter, passed forwards
    and backwards, using second-order sections for stability
    and numerical accuracy.

    Parameters
    ----------
    x : np.ndarray
        Signal of interest
    fs : float
        Sampling frequency in Hertz
    fc : float
        Cutoff frequency for low-pass filter in Hertz

    Returns
    -------
    np.ndarray
        Filtered signal
    """
    wn = fc / (fs / 2)
    sos = signal.butter(2, wn, "low", output="sos")
    return signal.sosfiltfilt(sos, x)


def highpass(x: np.ndarray, fs: float, fc: float) -> np.ndarray:
    """Apply a highpass filter to the input signal

    Uses a second order Butterworth filter, passed forwards
    and backwards, using second-order sections for stability
    and numerical accuracy.

    Parameters
    ----------
    x : np.ndarray
        Signal of interest
    fs : float
        Sampling frequency in Hertz
    fc : float
        Cutoff frequency for high-pass filter in Hertz

    Returns
    -------
    np.ndarray
        Filtered signal
    """
    wn = fc / (fs / 2)
    sos = signal.butter(2, wn, "high", output="sos", analog=False)
    return signal.sosfiltfilt(sos, x)


def bandpass(
    x: np.ndarray, fs: float, lims: tuple[float, float], getfilter: bool = False
) -> np.ndarray:
    """Apply a bandpass filter to the input signal

    Filter is applied along last dimension of signal. Filter is a
    second order Butterworth filter, passed forwards and backwards,
    i.e. resulting in a 4-th order, zero-phase filtering.

    Parameters
    ----------
    x : np.ndarray
        Signal of interest
    fs : float
        Sampling frequency
    lims : tuple[float, float]
        Band-pass limits
    getfilter : bool, optional
        Option to get filter parameters (mainly for testing)

    Returns
    -------
    np.ndarray or tuple
        Filtered signal (and optionally filter parameters as second order slices)
    """
    wn = [l for l in lims]
    sos = signal.butter(2, wn, btype="bp", output="sos", analog=False, fs=fs)
    if getfilter:
        return signal.sosfiltfilt(sos, x), sos

    return signal.sosfiltfilt(sos, x)


def notch(x: np.ndarray, fs: float, fc: float, getfilter: bool = False) -> np.ndarray:
    """Apply a notch filter to the input signal

    Filter is applied along last dimension of signal. Filter is a
    second order Butterworth filter, passed forwards and backwards,
    i.e. resulting in a 4-th order, zero-phase filtering.

    Parameters
    ----------
    x : np.ndarray
        Signal of interest
    fs : float
        Sampling frequency
    fc : float
        Center frequency for notch filter
    getfilter : bool, optional
        Option to get filter parameters (mainly for testing)

    Returns
    -------
    np.ndarray or tuple
        Filtered signal (and optionally filter parameters as second order slices)
    """

    sos = signal.butter(
        2, [fc - 0.1, fc + 0.1], btype="bandstop", output="sos", analog=False, fs=fs
    )
    if getfilter:
        return signal.sosfiltfilt(sos, x), sos

    return signal.sosfiltfilt(sos, x)
