"""
Search templates definitions and utilities
==========================================

@author A. Schaer, H. Maurenbrecher
@copyright Magnes AG, (C) 2025
"""

import numpy as np


def mexican(n: int, fs: float = 1.0, bound: float = 3.0) -> np.ndarray:
    """Construct Mexican hat template

    Can be used as a template for the QRS complex. The unit standard deviation
    gaussian (sigma = 1) is used as generating bell.

    NOTE The mexican hat is the negative second derivative of the Gaussian bell
    x = exp(-(t^2)/2 sigma**2)

    Parameters
    ----------
    n : int
        Number of samples
    fs : float, optional
        Sampling frequency in Hz. Defaults to 1.0
    bound : float, optional
        Template extension in number of standard deviations. Defaults to 3.0

    Returns
    -------
    np.ndarray
        Template centered at sample n/2
    """
    t = np.linspace(-bound, bound, n)
    x = (1 - t**2) * np.exp(-(t**2) / 2)
    return uniform_wavelet(x, fs)


def uniform_wavelet(wavelet: np.ndarray, fs: float = 1) -> np.ndarray:
    """Adjust input to star and end at 0, and have unit physical energy

    Parameters
    ----------
    wavelet : np.ndarray
        Packet to be uniformed
    fs : float, optional
        Sampling frequency of wavelet. Defaults to 1.0.

    Returns
    -------
    np.ndarray
        Wavelet packet starting and stopping at zero and having unit energy
    """
    w = wavelet.copy()
    x0 = wavelet[0]
    x1 = wavelet[-1]
    w -= x0
    w -= np.linspace(0, x1 - x0, len(wavelet))
    energy = np.sum(np.square(w)) / fs
    return w / np.sqrt(energy)
