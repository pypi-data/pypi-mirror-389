"""
Experiment datamodel
====================

@author A. Schaer, H. Maurenbrecher
@copyright Magnes AG, (C) 2025
"""

from __future__ import annotations
import dataclasses
import os

import numpy as np

from msgu.periodic import tidal
from msgu.mixture import prsynth


@dataclasses.dataclass
class ExperimentConfiguration:
    fs: float
    freqs: list[float]
    widths: list[float]
    gamma: float
    sigma: float
    nbeats: int = 1000
    scaling: tidal.WAVE_SCALING = tidal.WAVE_SCALING.IDENTITY
    dest: str = "."
    plot: bool = True
    seed: int = None

    def __post_init__(self):
        self._nfreqs = len(self.freqs)

        if self.gamma <= 0:
            raise ValueError(f"Invalid gamma {self.gamma} value detected")

        if self.sigma <= 0:
            raise ValueError(f"Invalid sigma {self.sigma} value detected")

        if self.plot and not os.path.exists(self.dest):
            os.makedirs(self.dest)

    @property
    def short_str(self) -> str:
        return f"[fs: {self.fs:.0f}; gamma: {self.gamma:.1f}; sigma: {self.sigma:.2f}; nbeats: {self.nbeats}; nfreqs: {len(self.freqs)}]"


@dataclasses.dataclass
class ExperimentResults:
    rmse: float
    rmsle: float
    tpr: float
    fpr: float

    def __sub__(self, other: ExperimentResults) -> ExperimentResults:
        return ExperimentResults(
            self.rmse - other.rmse,
            self.rmsle - other.rmsle,
            self.tpr - other.tpr,
            self.fpr - other.fpr,
        )


def extract_ndarrays_from_array_of_results(
    res: np.ndarray[tuple[int, ...], ExperimentResults],
) -> dict[str, np.ndarray[tuple[int, ...], float]]:
    """Extract arrays of values from array of results

    Sort of "transpose" operation.

    Parameters
    ----------
    res : np.ndarray[tuple[int, ...], ExperimentResults]
        Array of results

    Returns
    -------
    dict[str, np.ndarray[tuple[int, ...], float]]
        Dictionary of results, with a key for each field in the results model
    """
    transposed = {
        key: np.empty(res.shape, dtype=float)
        for key in ExperimentResults.__dataclass_fields__
    }
    for index, val in np.ndenumerate(res):
        for key, field in val.__dataclass_fields__.items():
            transposed[key][index] = getattr(val, field.name)

    return transposed


def generate_data(expcfg: ExperimentConfiguration) -> prsynth.SynthData:
    return prsynth.generate_synthetic_wave_with_cardiac_artifacts(
        expcfg.fs,
        expcfg.freqs,
        expcfg.widths,
        gamma=expcfg.gamma,
        sigma=expcfg.sigma,
        bwscaling=expcfg.scaling,
        nbeats=expcfg.nbeats,
        seed=expcfg.seed,
    )
