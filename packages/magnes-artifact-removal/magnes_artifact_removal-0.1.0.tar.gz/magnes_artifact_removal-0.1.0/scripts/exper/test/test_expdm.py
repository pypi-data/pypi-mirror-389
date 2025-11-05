"""
Experument data model testing
=============================

@author A. Schaer, H. Maurenbrecher
@copyright Magnes AG, (C) 2025
"""

import numpy as np

from scripts.exper import expdm


def test_extract_ndarrays_from_array_of_results():
    results_array = np.array(
        [
            [
                expdm.ExperimentResults(0.1, 0.05, 0.8, 0.2),
                expdm.ExperimentResults(0.2, 0.1, 0.7, 0.3),
            ],
            [
                expdm.ExperimentResults(0.15, 0.08, 0.75, 0.25),
                expdm.ExperimentResults(0.25, 0.12, 0.65, 0.35),
            ],
        ]
    )

    extracted = expdm.extract_ndarrays_from_array_of_results(results_array)

    # Verify the structure
    assert isinstance(extracted, dict)
    assert extracted.keys() == {"rmse", "rmsle", "tpr", "fpr"}

    # Verify shapes match original array
    for array in extracted.values():
        assert array.shape == results_array.shape
        assert array.dtype == float

    # Verify values are correctly extracted
    assert extracted["rmse"][0, 0] == 0.1
    assert extracted["rmse"][0, 1] == 0.2
    assert extracted["rmse"][1, 0] == 0.15
    assert extracted["rmse"][1, 1] == 0.25

    assert extracted["rmsle"][0, 0] == 0.05
    assert extracted["tpr"][0, 0] == 0.8
    assert extracted["fpr"][0, 0] == 0.2
