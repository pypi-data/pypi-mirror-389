"""Tests for hrvlib detrend functionality."""

import numpy as np
import pytest
from pathlib import Path
from hrvlib.detrend import detrend_og, detrend_sparse
from hrvlib._core import detrend
from hrvlib import cmc


# Path to test data directory
TEST_DATA_DIR = Path(__file__).parent / "data"


class TestDetrendOg:
    """Test suite for detrend_og function."""

    def test_basic_detrending(self):
        """Test basic detrending with simple RR interval data."""
        rr = np.array([800.0, 820.0, 810.0, 830.0, 815.0])
        result = detrend_og(rr, lambada=10)

        assert isinstance(result, np.ndarray)
        assert result.shape == rr.shape
        assert len(result) == len(rr)

    def test_output_type(self):
        """Test that output is numpy array."""
        rr = np.array([800.0, 820.0, 810.0])
        result = detrend_og(rr)

        assert isinstance(result, np.ndarray)
        assert result.dtype == np.float64 or result.dtype == np.float32

    def test_different_lambada_values(self):
        """Test detrending with different lambda values."""
        rr = np.array([800.0, 820.0, 810.0, 830.0, 815.0])

        result_low = detrend_og(rr, lambada=1)
        result_mid = detrend_og(rr, lambada=10)
        result_high = detrend_og(rr, lambada=100)

        assert not np.array_equal(result_low, result_mid)
        assert not np.array_equal(result_mid, result_high)

    def test_default_lambada(self):
        """Test that default lambda value is 10."""
        rr = np.array([800.0, 820.0, 810.0, 830.0])

        result_default = detrend_og(rr)
        result_explicit = detrend_og(rr, lambada=10)

        np.testing.assert_array_equal(result_default, result_explicit)

    def test_trend_removal(self):
        """Test that linear trend is removed from data."""
        # Create data with strong linear trend
        t = np.arange(20)
        trend = 5 * t  # Linear trend
        noise = np.random.RandomState(42).randn(20) * 2
        rr = 800 + trend + noise

        result = detrend_og(rr, lambada=50)

        # Detrended data should have smaller magnitude than original
        assert np.abs(result).max() < np.abs(rr - rr.mean()).max()

    def test_constant_signal(self):
        """Test with constant RR intervals."""
        rr = np.ones(10) * 800.0
        result = detrend_og(rr, lambada=10)

        assert isinstance(result, np.ndarray)
        assert result.shape == rr.shape

    def test_minimum_length(self):
        """Test with minimum viable array length."""
        # Function uses D2 matrix which is (T-2) x T, so need at least 3 elements
        rr = np.array([800.0, 820.0, 810.0])
        result = detrend_og(rr, lambada=10)

        assert isinstance(result, np.ndarray)
        assert result.shape == rr.shape

    def test_longer_signal(self):
        """Test with longer RR interval signal."""
        rr = np.random.RandomState(42).randn(100) * 50 + 800
        result = detrend_og(rr, lambada=100)

        assert isinstance(result, np.ndarray)
        assert result.shape == rr.shape
        assert len(result) == 100

    def test_preserves_shape(self):
        """Test that output shape matches input shape."""
        for length in [5, 10, 50]:
            rr = np.random.RandomState(42).randn(length) * 50 + 800
            result = detrend_og(rr, lambada=10)
            assert result.shape == rr.shape

    def test_lambada_zero(self):
        """Test with lambda=0 (no smoothing)."""
        rr = np.array([800.0, 820.0, 810.0, 830.0, 815.0])
        result = detrend_og(rr, lambada=0)

        # With lambda=0, should return zero array (no detrending)
        assert isinstance(result, np.ndarray)
        np.testing.assert_array_almost_equal(result, np.zeros_like(rr))

    def test_realistic_hrv_data(self):
        """Test with realistic HRV data ranges."""
        # Typical RR intervals in milliseconds (60-100 bpm range)
        rr = np.array([950, 920, 880, 910, 900, 870, 890, 920, 950, 940])
        result = detrend_og(rr, lambada=10)

        assert isinstance(result, np.ndarray)
        assert result.shape == rr.shape
        # Detrended values should be smaller in magnitude
        assert np.abs(result).mean() < np.abs(rr - rr.mean()).mean()

    def test_with_negative_values_raises_no_error(self):
        """Test that function handles negative values (though unusual for RR)."""
        rr = np.array([-10.0, -5.0, 0.0, 5.0, 10.0])
        # Should not raise an error
        result = detrend_og(rr, lambada=10)
        assert isinstance(result, np.ndarray)

    def test_with_real_training_session_data(self):
        """Test detrending with real HRV training session data from CSV file."""
        csv_file = TEST_DATA_DIR / "training_session_63dce1ec-6804-473e-b3cd-fe1d1e75b816_hrv_1149.csv"

        # Load RR intervals from CSV (skip header)
        rr_data = np.loadtxt(csv_file, skiprows=1)

        # Verify data loaded correctly
        assert len(rr_data) > 0
        assert rr_data.min() > 0  # RR intervals should be positive
        assert rr_data.max() < 2000  # Reasonable upper bound for RR intervals in ms

        # Apply detrending with default lambda
        result = detrend_og(rr_data, lambada=10)

        # Validate output
        assert isinstance(result, np.ndarray)
        assert result.shape == rr_data.shape
        assert len(result) == len(rr_data)

        # Detrended signal should have smaller variance than centered original
        centered_rr = rr_data - rr_data.mean()
        assert np.var(result) < np.var(centered_rr)

        # Test with higher lambda (more smoothing)
        # result_smooth = detrend_og(rr_data, lambada=100)
        # assert isinstance(result_smooth, np.ndarray)
        # assert result_smooth.shape == rr_data.shape

        # Higher lambda should produce smoother (lower variance) output
        # assert np.var(result_smooth) < np.var(result)

    def test_cmc(self):
        """Test that cmc function computes mean-centered vector correctly."""
        vec = np.array([1.0, 2.0, 3.0, 4.0, 5.0])
        expected = vec - vec.mean()

        result = cmc(vec)

        np.testing.assert_array_almost_equal(result, expected)


class TestDetrendComparison:
    """Test suite comparing different detrend implementations."""

    def test_all_implementations_basic_data(self):
        """Compare all three detrend implementations on basic data."""
        rr = np.array([800.0, 820.0, 810.0, 830.0, 815.0, 825.0, 805.0])
        lambda_val = 10.0

        result_og = detrend_og(rr, lambada=lambda_val)
        result_sparse = detrend_sparse(rr, lambada=lambda_val)
        result_cpp = detrend(rr, lambda_val=lambda_val)

        # All should return arrays of same shape
        assert result_og.shape == result_sparse.shape == result_cpp.shape

        # Results should be numerically close (within 1e-6 tolerance)
        np.testing.assert_allclose(result_og, result_sparse, rtol=1e-6, atol=1e-6,
                                   err_msg="detrend_og and detrend_sparse differ")
        np.testing.assert_allclose(result_og, result_cpp, rtol=1e-6, atol=1e-6,
                                   err_msg="detrend_og and detrend (C++) differ")
        np.testing.assert_allclose(result_sparse, result_cpp, rtol=1e-6, atol=1e-6,
                                   err_msg="detrend_sparse and detrend (C++) differ")

    def test_all_implementations_different_lambdas(self):
        """Compare implementations with different lambda values."""
        rr = np.array([950.0, 920.0, 880.0, 910.0, 900.0, 870.0, 890.0])

        for lambda_val in [1.0, 10.0, 50.0, 100.0]:
            result_og = detrend_og(rr, lambada=lambda_val)
            result_sparse = detrend_sparse(rr, lambada=lambda_val)
            result_cpp = detrend(rr, lambda_val=lambda_val)

            np.testing.assert_allclose(result_og, result_sparse, rtol=1e-6, atol=1e-6,
                                       err_msg=f"Mismatch at lambda={lambda_val}")
            np.testing.assert_allclose(result_og, result_cpp, rtol=1e-6, atol=1e-6,
                                       err_msg=f"Mismatch at lambda={lambda_val}")

    def test_all_implementations_longer_signal(self):
        """Compare implementations on longer signal."""
        np.random.seed(42)
        rr = np.random.randn(100) * 50 + 850
        lambda_val = 20.0

        result_og = detrend_og(rr, lambada=lambda_val)
        result_sparse = detrend_sparse(rr, lambada=lambda_val)
        result_cpp = detrend(rr, lambda_val=lambda_val)

        # Should be very close even for longer signals
        np.testing.assert_allclose(result_og, result_sparse, rtol=1e-5, atol=1e-5)
        np.testing.assert_allclose(result_og, result_cpp, rtol=1e-5, atol=1e-5)

    def test_all_implementations_real_data(self):
        """Compare all implementations on real training session data."""
        csv_file = TEST_DATA_DIR / "training_session_63dce1ec-6804-473e-b3cd-fe1d1e75b816_hrv_1149.csv"
        rr_data = np.loadtxt(csv_file, skiprows=1)

        lambda_val = 10.0

        result_og = detrend_og(rr_data, lambada=lambda_val)
        result_sparse = detrend_sparse(rr_data, lambada=lambda_val)
        result_cpp = detrend(rr_data, lambda_val=lambda_val)

        # All should have same shape
        assert result_og.shape == result_sparse.shape == result_cpp.shape
        assert len(result_og) == len(rr_data)

        # Results should be numerically close
        np.testing.assert_allclose(result_og, result_sparse, rtol=1e-6, atol=1e-6,
                                   err_msg="detrend_og and detrend_sparse differ on real data")
        np.testing.assert_allclose(result_og, result_cpp, rtol=1e-6, atol=1e-6,
                                   err_msg="detrend_og and detrend (C++) differ on real data")

    def test_all_implementations_with_trend(self):
        """Compare implementations on data with strong linear trend."""
        t = np.arange(50)
        trend = 5 * t
        noise = np.random.RandomState(42).randn(50) * 2
        rr = 800 + trend + noise

        lambda_val = 50.0

        result_og = detrend_og(rr, lambada=lambda_val)
        result_sparse = detrend_sparse(rr, lambada=lambda_val)
        result_cpp = detrend(rr, lambda_val=lambda_val)

        # All should remove trend similarly
        np.testing.assert_allclose(result_og, result_sparse, rtol=1e-6, atol=1e-6)
        np.testing.assert_allclose(result_og, result_cpp, rtol=1e-6, atol=1e-6)

        # All detrended signals should have smaller magnitude than original
        for result in [result_og, result_sparse, result_cpp]:
            assert np.abs(result).max() < np.abs(rr - rr.mean()).max()

    def test_all_implementations_minimum_length(self):
        """Compare implementations on minimum viable array length."""
        rr = np.array([800.0, 820.0, 810.0])
        lambda_val = 10.0

        result_og = detrend_og(rr, lambada=lambda_val)
        result_sparse = detrend_sparse(rr, lambada=lambda_val)
        result_cpp = detrend(rr, lambda_val=lambda_val)

        np.testing.assert_allclose(result_og, result_sparse, rtol=1e-6, atol=1e-6)
        np.testing.assert_allclose(result_og, result_cpp, rtol=1e-6, atol=1e-6)

    def test_all_implementations_lambda_zero(self):
        """Compare implementations with lambda=0."""
        rr = np.array([800.0, 820.0, 810.0, 830.0, 815.0])
        lambda_val = 0.0

        result_og = detrend_og(rr, lambada=lambda_val)
        result_sparse = detrend_sparse(rr, lambada=lambda_val)
        result_cpp = detrend(rr, lambda_val=lambda_val)

        # All should produce zero or near-zero output with lambda=0
        np.testing.assert_allclose(result_og, result_sparse, rtol=1e-6, atol=1e-6)
        np.testing.assert_allclose(result_og, result_cpp, rtol=1e-6, atol=1e-6)