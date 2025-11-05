"""
Test Scaling Auxiliary Tool
============================

@author H. Maurenbrecher
@copyright Magnes AG, (C) 2025
"""

import numpy as np
import pytest

from martrem.aux import scaling


class TestStandardize:
    def test_standardize_default(self):
        x = np.array([1.0, 2.0, 3.0, 4.0, 5.0])
        result = scaling.standardize(x)

        assert pytest.approx(np.nanmean(result), abs=1e-10) == 0.0
        assert pytest.approx(np.nanstd(result), abs=1e-10) == 1.0

    def test_standardize_with_mu_sigma(self):
        x = np.array([1.0, 2.0, 3.0, 4.0, 5.0])
        mu = 3.0
        sigma = 2.0
        result = scaling.standardize(x, mu=mu, sigma=sigma)

        expected = (x - mu) / (sigma + np.spacing(1))
        assert np.allclose(result, expected)

    def test_standardize_zero_sigma(self):
        x = np.array([5.0, 5.0, 5.0, 5.0])
        mu = 5.0
        sigma = 0.0
        result = scaling.standardize(x, mu=mu, sigma=sigma)

        assert not np.any(np.isinf(result))
        assert not np.any(np.isnan(result))

    def test_standardize_with_nan(self):
        x = np.array([1.0, 2.0, np.nan, 4.0, 5.0])
        result = scaling.standardize(x)

        assert not np.isnan(result[0])
        assert np.isnan(result[2])


class TestPowerToDb:
    def test_power_to_db_basic(self):
        pwr = np.array([1.0, 10.0, 100.0, 1000.0])
        result = scaling.power_to_db(pwr)

        expected = np.array([0.0, 10.0, 20.0, 30.0])
        assert np.allclose(result, expected)

    def test_power_to_db_fraction(self):
        pwr = np.array([0.1, 0.01, 0.001])
        result = scaling.power_to_db(pwr)

        expected = np.array([-10.0, -20.0, -30.0])
        assert np.allclose(result, expected)

    def test_power_to_db_single_value(self):
        pwr = np.array([100.0])
        result = scaling.power_to_db(pwr)

        assert pytest.approx(result[0]) == 20.0


class TestAmplitudeToDb:
    def test_amplitude_to_db_basic(self):
        amp = np.array([1.0, 10.0, 100.0])
        result = scaling.amplitude_to_db(amp)

        expected = 2 * 10 * np.log10(amp)
        assert np.allclose(result, expected)

    def test_amplitude_to_db_relationship(self):
        amp = np.array([2.0, 5.0, 10.0])
        pwr = amp**2

        amp_db = scaling.amplitude_to_db(amp)
        pwr_db = scaling.power_to_db(pwr)

        assert np.allclose(amp_db, pwr_db)

    def test_amplitude_to_db_unity(self):
        amp = np.array([1.0])
        result = scaling.amplitude_to_db(amp)

        assert pytest.approx(result[0]) == 0.0
