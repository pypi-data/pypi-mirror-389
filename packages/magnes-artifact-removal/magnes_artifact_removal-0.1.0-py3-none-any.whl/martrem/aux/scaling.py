"""
Scaling utility
===============

@author A. Schaer, H. Maurenbrecher
@copyright Magnes AG, (C) 2025
"""

import numpy as np


def standardize(x: np.ndarray, mu: float = None, sigma: float = None) -> np.ndarray:
    """Standardize

    According to `(x - mu) / sigma`, where mu and sigma denote the mean and
    std of x, respectively.

    Parameters
    ----------
    x : np.ndarray
        Signal
    mu : float, optional
        Signal mean. Defaults to None.
    sigma : float, optional
        Signal STD. Defaults to None.

    Returns
    -------
    np.ndarray
        Standardized signal
    """
    if mu is None:
        mu = np.nanmean(x)

    if sigma is None:
        sigma = np.nanstd(x)

    return (x - mu) / (sigma + np.spacing(1))


def power_to_db(pwr: np.ndarray) -> np.ndarray:
    """Power to decibel

    Parameters
    ----------
    pwr : np.ndarray
        Power values

    Returns
    -------
    np.ndarray
        Power values in dB
    """
    return 10 * np.log10(pwr)


def amplitude_to_db(amp: np.ndarray) -> np.ndarray:
    """Amplitude to decibel

    Parameters
    ----------
    amp : np.ndarray
        Amplitude values

    Returns
    -------
    np.ndarray
        Amplitude in decibel
    """
    return 2 * power_to_db(amp)
