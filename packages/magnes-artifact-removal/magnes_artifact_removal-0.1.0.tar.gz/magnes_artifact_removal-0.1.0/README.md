# Magnes Artifact Removal
Magnes utility for the removal of artifacts from time series.


## Installation
Install the package using
```bash
    pip install artrem 
```
*Note*, might need to be adapted to the final location of the package.

## Quick Start

``` python
    import numpy as np
    from martrem import clean_with_adaptive_shape_correlation
    from martrem.aux import templating

    # Prepare your signal data
    fs = 250.0  # Sampling frequency
    signal_data = np.array([...])  # Your time series data

    # Create a search template
    psi_n = 25
    psi = templating.mexican(psi_n, fs=fs, bound=3)

    # Clean the signal
    corrected, artifact = clean_with_adaptive_shape_correlation(
        signal_data,
        fs=fs,
        psi=psi,
        tau_n=50,
        fco_hp=0.1,
        xcorr_min_peak_distance=80
    )
```
## Submodules
### Autoenc
Autoencoder-based signal filtering/artifact detection.

### Auxiliary Tools
Collection of submodules for filtering, scaling, and generating signal templates (shapelets/wavelets).

### Cleaning
Main interface of the package. Collection of functions cleaning corrupted time series using a specific method.

## Scripts
The package is evaluated using a number of scripts. Scripts can be seen as studies of a specific
strategy or a comparison thereof. For example, scripts to evaluate the search-template-based ECG artifact
removal strategy from blurred-peak waves are provided, including a single-experiment run `scripts/singlerun.py`
and a parametric sweep `scripts/sweep.py`.

Due to the folder hierarchy, scripts are to be run from root as modules, i.e. to run the
script `scripts/foo.py` call
```bash
uv run -m scripts.foo [ARGS]
```

**Note** The scripts are not included in package, but are only available in the full source.

## Testing
Testing is performed using `pytest`. Package tests are defined in `tests/`, replicating the
To run the package unittests, call
```bash
uv run -m pytest tests [OPTIONS]
```
To run the scripts' tests call
```bash
uv run -m pytest scripts [OPTIONS]
```
To run the all tests call
```bash
uv run -m pytest [OPTIONS]
```

All calls are assumed to be made from the project root.


