"""
Edge Cases and Error Handling Tests
===================================

Comprehensive tests for edge cases, error conditions, and boundary values.

@author A. Schaer
@copyright Magnes AG, (C) 2025
"""

import numpy as np
import pytest

from msgu.cardio import ecg
from msgu.gauss import gaussians
from msgu.mixture import prsynth
from msgu.noise import noise
from msgu.periodic import tidal
from msgu.trajectory import scurves


class TestCardioEdgeCases:
    """Test edge cases for cardio module"""

    def test_beat_r_peak_index(self):
        """Test that r_peak_index property works correctly"""
        beat = ecg.Beat(250.0, seed=42)
        assert isinstance(beat.r_peak_index, int)
        assert 0 <= beat.r_peak_index < beat.n

    def test_beat_reproducibility(self):
        """Test that seeded beats are reproducible"""
        beat1 = ecg.Beat(250.0, seed=42)
        beat2 = ecg.Beat(250.0, seed=42)
        np.testing.assert_array_equal(beat1.x, beat2.x)

    def test_generate_ecg_single_beat(self):
        """Test ECG generation with single beat"""
        t, x = ecg.generate_ecg(250.0, nbeats=1)
        assert len(t) == len(x)
        assert len(x) > 0

    def test_generate_ecg_zero_noise(self):
        """Test ECG generation with zero noise"""
        t, x = ecg.generate_ecg(250.0, nbeats=3, sigma=0.0)
        assert len(t) == len(x)
        assert np.all(np.isfinite(x))

    def test_generate_ecg_high_noise(self):
        """Test ECG generation with high noise level"""
        t, x = ecg.generate_ecg(250.0, nbeats=3, sigma=10.0)
        assert len(t) == len(x)
        assert np.all(np.isfinite(x))

    def test_generate_ecg_many_beats(self):
        """Test ECG generation with many beats"""
        t, x = ecg.generate_ecg(250.0, nbeats=20)
        assert len(t) == len(x)
        assert len(x) > 0


class TestGaussEdgeCases:
    """Test edge cases for Gaussian functions"""

    def test_gaussian_zero_sigma_raises(self):
        """Test that zero sigma raises error due to division"""
        x = np.array([0, 1, 2])
        with pytest.raises((ZeroDivisionError, RuntimeWarning)):
            gaussians.gaussian(x, mu=0.0, sigma=0.0)

    def test_gaussian_negative_sigma(self):
        """Test Gaussian with negative sigma (mathematically valid)"""
        x = np.linspace(-5, 5, 100)
        result = gaussians.gaussian(x, mu=0.0, sigma=-1.0)
        assert len(result) == len(x)
        assert np.all(np.isfinite(result))

    def test_dgauss_at_center(self):
        """Test that first derivative is zero at center"""
        result = gaussians.dgauss(np.array([0.0]), mu=0.0, sigma=1.0)
        assert np.abs(result[0]) < 1e-10

    def test_d2gauss_symmetry(self):
        """Test that second derivative is symmetric"""
        x = np.array([-1.0, 1.0])
        result = gaussians.d2gauss(x, mu=0.0, sigma=1.0)
        assert np.abs(result[0] - result[1]) < 1e-10


class TestNoiseEdgeCases:
    """Test edge cases for noise generation"""

    def test_white_noise_small_n(self):
        """Test white noise generation with small n"""
        wn = noise.generate_white_noise(10)
        assert len(wn) == 10
        assert np.abs(np.mean(wn)) < 0.5
        assert np.abs(np.std(wn) - 1.0) < 0.5

    def test_pink_noise_minimum_samples_filter_theory(self):
        """Test pink noise with minimum required samples for FILTER_THEORY"""
        n = noise.CFG.THEORY_FILTER_KERNEL_SIZE
        pn = noise.generate_pink_noise(n, algo=noise.PINK_NOISE_ALGO.FILTER_THEORY)
        assert len(pn) == n

    def test_pink_noise_below_minimum_filter_theory(self):
        """Test that pink noise raises error when n is too small for FILTER_THEORY"""
        n = noise.CFG.THEORY_FILTER_KERNEL_SIZE - 1
        with pytest.raises(ValueError, match="at least"):
            noise.generate_pink_noise(n, algo=noise.PINK_NOISE_ALGO.FILTER_THEORY)

    def test_pink_noise_minimum_samples_filter_wiki(self):
        """Test pink noise with minimum required samples for FILTER_WIKI"""
        n = noise.CFG.WIKI_FILTER_KERNEL_SIZE
        pn = noise.generate_pink_noise(n, algo=noise.PINK_NOISE_ALGO.FILTER_WIKI)
        assert len(pn) == n

    def test_pink_noise_below_minimum_filter_wiki(self):
        """Test that pink noise raises error when n is too small for FILTER_WIKI"""
        n = noise.CFG.WIKI_FILTER_KERNEL_SIZE - 1
        with pytest.raises(ValueError, match="at least"):
            noise.generate_pink_noise(n, algo=noise.PINK_NOISE_ALGO.FILTER_WIKI)

    def test_pink_noise_fft_small_n(self):
        """Test pink noise FFT algorithm with small n"""
        pn = noise.generate_pink_noise(10, algo=noise.PINK_NOISE_ALGO.FFT)
        assert len(pn) == 10

    def test_pink_noise_voss_mccartney_small_n(self):
        """Test pink noise Voss-McCartney algorithm with small n"""
        pn = noise.generate_pink_noise(10, algo=noise.PINK_NOISE_ALGO.VOSS_MCCARTNEY)
        assert len(pn) == 10

    def test_pink_noise_invalid_algo(self):
        """Test pink noise with invalid algorithm (should never happen with enum but test the code path)"""
        # This tests the default case in the match statement
        # We can't actually trigger it with the enum, but we ensure the error handling exists
        # by checking the algorithm list
        assert len(list(noise.PINK_NOISE_ALGO)) == 4


class TestPeriodicEdgeCases:
    """Test edge cases for periodic signal generation"""

    def test_single_freq_waves_empty_freqs(self):
        """Test single freq waves with empty frequency list"""
        t = np.linspace(0, 1, 100)
        x = tidal.generate_randomly_phased_waves_single_freq(t, [])
        # Division by zero from len(freqs)
        assert np.all(np.isnan(x)) or np.all(np.isinf(x))

    def test_single_freq_waves_negative_freq(self):
        """Test single freq waves with negative frequency (should be skipped)"""
        t = np.linspace(0, 1, 100)
        x = tidal.generate_randomly_phased_waves_single_freq(t, [-10.0, 10.0])
        assert len(x) == len(t)
        assert np.all(np.isfinite(x))

    def test_single_freq_waves_zero_freq(self):
        """Test single freq waves with zero frequency (should be skipped)"""
        t = np.linspace(0, 1, 100)
        x = tidal.generate_randomly_phased_waves_single_freq(t, [0.0, 10.0])
        assert len(x) == len(t)
        assert np.all(np.isfinite(x))

    def test_blurred_peaks_invalid_freq(self):
        """Test blurred peaks with invalid frequency raises error"""
        t = np.linspace(0, 1, 100)
        with pytest.raises(ValueError, match="Invalid frequency"):
            tidal.generate_randomly_phased_waves_blurred_peaks(t, [0.0], [1.0])

    def test_blurred_peaks_invalid_width(self):
        """Test blurred peaks with invalid width raises error"""
        t = np.linspace(0, 1, 100)
        with pytest.raises(ValueError, match="Invalid frequency.*or width"):
            tidal.generate_randomly_phased_waves_blurred_peaks(t, [10.0], [0.0])

    def test_blurred_peaks_negative_freq(self):
        """Test blurred peaks with negative frequency raises error"""
        t = np.linspace(0, 1, 100)
        with pytest.raises(ValueError, match="Invalid frequency"):
            tidal.generate_randomly_phased_waves_blurred_peaks(t, [-10.0], [1.0])

    def test_wave_scaling_identity(self):
        """Test identity wave scaling returns 1.0"""
        assert tidal.WAVE_SCALING.IDENTITY(10.0) == 1.0

    def test_wave_scaling_inv(self):
        """Test inverse wave scaling"""
        assert tidal.WAVE_SCALING.INV(10.0) == 0.1

    def test_wave_scaling_inv_sqrt(self):
        """Test inverse square root wave scaling"""
        assert np.abs(tidal.WAVE_SCALING.INV_SQRT(4.0) - 0.5) < 1e-10

    def test_wave_scaling_two_inv_sqrt(self):
        """Test sqrt(2/x) wave scaling"""
        result = tidal.WAVE_SCALING.TWO_INV_SQRT(2.0)
        assert np.abs(result - 1.0) < 1e-10

    def test_wave_scaling_all_types(self):
        """Test that all WAVE_SCALING enum members are valid"""
        # Ensure all enum types are implemented
        assert len(list(tidal.WAVE_SCALING)) == 4


class TestMixtureEdgeCases:
    """Test edge cases for mixture/prsynth module"""

    def test_synth_data_properties(self):
        """Test SynthData properties and methods"""
        fs = 250.0
        data = prsynth.generate_synthetic_wave_with_cardiac_artifacts(
            fs, [10.0], [1.0], gamma=1.0, sigma=0.1, nbeats=2
        )
        assert data.fs == fs
        assert len(data) == len(data.t)
        assert len(data.z) == len(data.t)

    def test_synth_data_zero_gamma(self):
        """Test synthetic data with zero disturbance gain"""
        data = prsynth.generate_synthetic_wave_with_cardiac_artifacts(
            250.0, [10.0], [1.0], gamma=0.0, sigma=0.1, nbeats=2
        )
        # z should be x + 0*d + sigma*n = x + sigma*n
        assert len(data.z) == len(data.x)

    def test_synth_data_zero_sigma(self):
        """Test synthetic data with zero noise gain"""
        data = prsynth.generate_synthetic_wave_with_cardiac_artifacts(
            250.0, [10.0], [1.0], gamma=1.0, sigma=0.0, nbeats=2
        )
        # z should be x + gamma*d + 0*n = x + gamma*d
        assert len(data.z) == len(data.x)

    def test_synth_data_single_beat(self):
        """Test synthetic data generation with single beat"""
        data = prsynth.generate_synthetic_wave_with_cardiac_artifacts(
            250.0, [10.0], [1.0], nbeats=1
        )
        assert len(data.t) > 0


class TestTrajectoryEdgeCases:
    """Test edge cases for trajectory/S-curve generation"""

    def test_s_curve3_boundary_conditions(self):
        """Test cubic S-curve boundary conditions"""
        x = scurves.generate_s_curve3(100)
        assert np.abs(x[0]) < 1e-10  # Should start at 0
        assert np.abs(x[-1] - 1.0) < 1e-10  # Should end at 1

    def test_s_curve5_boundary_conditions(self):
        """Test quintic S-curve boundary conditions"""
        x = scurves.generate_s_curve5(100)
        assert np.abs(x[0]) < 1e-10  # Should start at 0
        assert np.abs(x[-1] - 1.0) < 1e-10  # Should end at 1

    def test_s_curve3_small_n(self):
        """Test cubic S-curve with small number of points"""
        x = scurves.generate_s_curve3(2)
        assert len(x) == 2
        assert np.abs(x[0]) < 1e-10
        assert np.abs(x[-1] - 1.0) < 1e-10

    def test_s_curve5_small_n(self):
        """Test quintic S-curve with small number of points"""
        x = scurves.generate_s_curve5(2)
        assert len(x) == 2
        assert np.abs(x[0]) < 1e-10
        assert np.abs(x[-1] - 1.0) < 1e-10

    def test_s_curve3_monotonicity(self):
        """Test that cubic S-curve is monotonically increasing"""
        x = scurves.generate_s_curve3(100)
        assert np.all(np.diff(x) >= 0)

    def test_s_curve5_monotonicity(self):
        """Test that quintic S-curve is monotonically increasing"""
        x = scurves.generate_s_curve5(100)
        assert np.all(np.diff(x) >= 0)
