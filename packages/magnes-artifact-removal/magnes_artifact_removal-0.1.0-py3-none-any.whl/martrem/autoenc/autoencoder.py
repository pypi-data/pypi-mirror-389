"""
Autoencoder interface module
============================

@author A. Schaer, H. Maurenbrecher
@copyright Magnes AG, (C) 2025
"""

from __future__ import annotations
import dataclasses
import datetime
import enum
import os
import pickle
from typing import Any

import numpy as np
from sklearn import neural_network as sklnn
from skl2onnx import to_onnx
from skl2onnx.common import data_types as onnxdt


@dataclasses.dataclass
class ModelBinModeMixin:
    ext: str


class MODEL_BIN_MODE(ModelBinModeMixin, enum.Enum):
    ONNX = "onnx"
    PICKLE = "pkl"

    @classmethod
    def infer_from_filename(cls, fn: str) -> MODEL_BIN_MODE:
        for candidate in cls:
            if fn.endswith(f".{candidate.ext}"):
                return candidate

        raise ValueError(f"Invalid model filename '{fn}'")


class Autoencoder:
    """Autoencoder for artifact detection and removal in time series signals

    This class wraps scikit-learn's MLPRegressor to provide autoencoder functionality
    for signal processing tasks.
    """

    _model: sklnn.MLPRegressor

    def __init__(
        self, hidden_layers_sizes: tuple[int, ...], hyperp: dict[str, Any]
    ) -> None:
        """Initialize the autoencoder

        Parameters
        ----------
        hidden_layers_sizes : tuple[int, ...]
            Tuple defining the number of neurons in each hidden layer
        hyperp : dict[str, Any]
            Dictionary of hyperparameters for MLPRegressor
        """
        self._model = sklnn.MLPRegressor(
            hidden_layer_sizes=hidden_layers_sizes, **hyperp
        )

    def train(self, x: np.ndarray[float], y: np.ndarray[float]) -> Autoencoder:
        """Train the autoencoder model

        Parameters
        ----------
        x : NDArray[np.floating[Any]]
            Training features (input samples)
        y : NDArray[np.floating[Any]]
            Training targets (output samples)

        Returns
        -------
        Autoencoder
            Self for method chaining
        """
        self._model = self._model.fit(x, y)
        return self

    def __call__(self, x: np.ndarray[float]) -> np.ndarray[float]:
        """Apply the autoencoder to input signal

        Parameters
        ----------
        x : NDArray[np.floating[Any]]
            Input signal array

        Returns
        -------
        NDArray[np.floating[Any]]
            Predicted output signal array
        """
        if x.size == self.insize:
            return self._model.predict(x)

        y = np.zeros_like(x)
        for stop_idx in range(self.insize, x.size):
            y[stop_idx - self.insize : stop_idx] = self._model.predict(
                x[stop_idx - self.insize : stop_idx].reshape(1, -1)
            )
        return y

    @property
    def size(self) -> int:
        """Get total number of parameters in the model

        Returns
        -------
        int
            Total parameter count (weights + biases)
        """
        return sum([v.size for v in self._model.coefs_]) + sum(
            [v.size for v in self._model.intercepts_]
        )

    @property
    def insize(self) -> int:
        """Get input size of the model

        Returns
        -------
        int
            Number of input features
        """
        return len(self._model.coefs_[0])

    def dump(self, dest: str, mode: MODEL_BIN_MODE = MODEL_BIN_MODE.PICKLE) -> str:
        """Dump model to disk

        Parameters
        ----------
        dest : str
            Target directory path
        mode : MODEL_BIN_MODE, optional
            Serialization mode (PICKLE or ONNX)

        Returns
        -------
        str
            Filename of saved (binary) file
        """
        today = datetime.datetime.today().strftime("%Y%m%d")
        fn = os.path.join(dest, f"autoencoder-{today}.{mode.ext}")

        if mode == MODEL_BIN_MODE.PICKLE:
            with open(fn, "wb") as fd:
                pickle.dump(self, fd)

        elif mode == MODEL_BIN_MODE.ONNX:
            onx = to_onnx(
                self._model,
                initial_types=[
                    (
                        "float_input",
                        onnxdt.FloatTensorType([None, self._model.n_features_in_]),
                    )
                ],
            )
            with open(fn, "wb") as fd:
                fd.write(onx.SerializeToString())

        return fn

    @staticmethod
    def load(fn: str) -> Autoencoder:
        """Load model from (binary) file

        Parameters
        ----------
        fn : str
            File path to be loaded

        Returns
        -------
        Autoencoder
            Loaded Autoencoder instance

        Raises
        ------
        NotImplementedError
            If attempting to load ONNX format
        """
        mode = MODEL_BIN_MODE.infer_from_filename(fn)

        if mode == MODEL_BIN_MODE.ONNX:
            raise NotImplementedError("ONNX autoencoder loading is not implemented yet")

        elif mode == MODEL_BIN_MODE.PICKLE:
            with open(fn, "rb") as fp:
                return pickle.load(fp)

        raise ValueError(f"Unsupported model format for file: {fn}")
