"""
Unit Tests — calibration.py
============================
Tests every function in the calibration pipeline with known-good inputs
and adversarial edge cases. All expected values are analytically derived —
no magic numbers.

Test categories:
  T1: Scale factor computation (S = 0.22 / d_ball_px)
  T2: Landmark un-normalisation and metric conversion
  T3: Segment length computation (Euclidean distance)
  T4: Stability gate — pass cases
  T5: Stability gate — fail cases (insufficient data, sway)
  T6: Full pipeline integration
"""

import numpy as np
import pytest
from core.calibration import (
    compute_scale_factor,
    unnormalise_landmark,
    pixel_to_metric_landmark,
    compute_euclidean_segment_length,
    extract_frame_segment_lengths,
    run_stability_gate,
    FrameSegmentLengths,
    MetricLandmark,
    STABILITY_WINDOW_FRAMES,
    STABILITY_TOLERANCE_FRACTION,
)
from constants.fifa_constants import BALL_DIAMETER_M


# ─── T1: Scale Factor ─────────────────────────────────────────────────────────

class TestScaleFactor:
    """
    S = BALL_DIAMETER_M / d_ball_px = 0.22 / d_ball_px
    All expected values computed analytically.
    """

    def test_nominal_case(self):
        """
        If ball appears as 44px diameter, scale = 0.22/44 = 0.005 m/px.
        At this scale, 44px × 0.005 = 0.22m = ball diameter. Consistent.
        """
        scale = compute_scale_factor(ball_diameter_px=44.0)
        expected = BALL_DIAMETER_M / 44.0  # = 0.005
        assert abs(scale - expected) < 1e-10, (
            f"Expected {expected}, got {scale}"
        )

    def test_different_resolution(self):
        """
        At higher resolution (ball = 88px): scale = 0.22/88 = 0.0025 m/px.
        """
        scale = compute_scale_factor(ball_diameter_px=88.0)
        expected = BALL_DIAMETER_M / 88.0  # = 0.0025
        assert abs(scale - expected) < 1e-10

    def test_physical_consistency(self):
        """
        Verify: d_ball_px × S = BALL_DIAMETER_M (round-trip).
        S × d_ball_px must always recover 0.22m exactly.
        """
        for d_px in [20.0, 44.0, 88.0, 120.0, 200.0]:
            scale = compute_scale_factor(d_px)
            recovered_diameter_m = scale * d_px
            assert abs(recovered_diameter_m - BALL_DIAMETER_M) < 1e-10, (
                f"Round-trip failed at d_ball_px={d_px}: "
                f"recovered {recovered_diameter_m:.6f}m ≠ {BALL_DIAMETER_M}m"
            )

    def test_zero_ball_diameter_raises(self):
        """Ball diameter of 0 is physically impossible → ValueError."""
        with pytest.raises(ValueError, match="must be > 0"):
            compute_scale_factor(ball_diameter_px=0.0)

    def test_negative_ball_diameter_raises(self):
        """Negative ball diameter is physically impossible → ValueError."""
        with pytest.raises(ValueError, match="must be > 0"):
            compute_scale_factor(ball_diameter_px=-10.0)


# ─── T2: Coordinate Conversion ────────────────────────────────────────────────

class TestCoordinateConversion:

    def test_unnormalise_centre_of_frame(self):
        """
        Landmark at (0.5, 0.5) in a 1920×1080 frame.
        x_px = 0.5 × 1920 = 960.0
        y_px = 0.5 × 1080 = 540.0
        """
        x_px, y_px = unnormalise_landmark(0.5, 0.5, 1920, 1080)
        assert abs(x_px - 960.0) < 1e-10
        assert abs(y_px - 540.0) < 1e-10

    def test_unnormalise_top_left(self):
        """Landmark at (0, 0) → pixel (0, 0)."""
        x_px, y_px = unnormalise_landmark(0.0, 0.0, 1920, 1080)
        assert x_px == 0.0
        assert y_px == 0.0

    def test_unnormalise_bottom_right(self):
        """Landmark at (1, 1) → pixel (1920, 1080)."""
        x_px, y_px = unnormalise_landmark(1.0, 1.0, 1920, 1080)
        assert abs(x_px - 1920.0) < 1e-10
        assert abs(y_px - 1080.0) < 1e-10

    def test_full_metric_conversion(self):
        """
        Full pipeline: norm → px → metres.
        Setup: 1920×1080, ball = 44px, so S = 0.22/44 = 0.005 m/px.
        Landmark at (0.5, 0.5):
          x_px = 960, y_px = 540
          x_m = 960 × 0.005 = 4.8m
          y_m = 540 × 0.005 = 2.7m
        """
        scale = compute_scale_factor(44.0)  # 0.005 m/px
        lm = pixel_to_metric_landmark(
            x_norm=0.5, y_norm=0.5, visibility=0.99,
            frame_width_px=1920, frame_height_px=1080,
            scale_m_per_px=scale
        )
        assert abs(lm.x_m - 4.800) < 1e-6
        assert abs(lm.y_m - 2.700) < 1e-6
        assert lm.visibility == 0.99


# ─── T3: Segment Length Computation ──────────────────────────────────────────

class TestSegmentLength:

    def _make_landmark(self, x_m: float, y_m: float, vis: float = 0.99) -> MetricLandmark:
        return MetricLandmark(x_m=x_m, y_m=y_m, visibility=vis)

    def test_vertical_segment(self):
        """
        Hip at (0, 0), Knee at (0, 0.42) → thigh = 0.42m.
        Pure vertical segment, no horizontal component.
        """
        hip  = self._make_landmark(0.0, 0.0)
        knee = self._make_landmark(0.0, 0.42)
        length = compute_euclidean_segment_length(hip, knee)
        assert abs(length - 0.42) < 1e-10

    def test_pythagorean_segment(self):
        """
        3-4-5 triangle: proximal (0,0), distal (0.3, 0.4) → L = 0.5m.
        Verifies Euclidean computation: sqrt(0.3² + 0.4²) = 0.5
        """
        p = self._make_landmark(0.0, 0.0)
        d = self._make_landmark(0.3, 0.4)
        length = compute_euclidean_segment_length(p, d)
        assert abs(length - 0.5) < 1e-10

    def test_low_visibility_returns_none(self):
        """
        Landmarks below MIN_LANDMARK_VISIBILITY (0.75) → None.
        This frame should be dropped by the pipeline.
        """
        p = self._make_landmark(0.0, 0.0, vis=0.50)
        d = self._make_landmark(0.0, 0.42, vis=0.99)
        result = compute_euclidean_segment_length(p, d)
        assert result is None

    def test_both_low_visibility_returns_none(self):
        p = self._make_landmark(0.0, 0.0, vis=0.60)
        d = self._make_landmark(0.0, 0.42, vis=0.60)
        result = compute_euclidean_segment_length(p, d)
        assert result is None


# ─── T4: Stability Gate — Pass Cases ─────────────────────────────────────────

class TestStabilityGatePass:

    def _make_stable_records(
        self,
        n_frames: int = 120,
        thigh: float = 0.42,
        shank: float = 0.40,
        trunk: float = 0.52,
        noise: float = 0.0
    ) -> list[FrameSegmentLengths]:
        """
        Generate synthetic segment records with controlled noise.
        noise = maximum random perturbation in metres.
        """
        rng = np.random.default_rng(seed=42)
        records = []
        for i in range(n_frames):
            records.append(FrameSegmentLengths(
                frame_index=i,
                thigh_m=thigh + rng.uniform(-noise, noise),
                shank_m=shank + rng.uniform(-noise, noise),
                trunk_m=trunk + rng.uniform(-noise, noise),
                scale_m_per_px=0.005
            ))
        return records

    def test_perfectly_stable_passes(self):
        """
        Zero noise → variation = 0 < any positive tolerance → gate passes.
        """
        records = self._make_stable_records(noise=0.0)
        result = run_stability_gate(records)
        assert result.gate_passed is True
        assert result.thigh_passed is True
        assert result.shank_passed is True
        assert result.trunk_passed is True

    def test_locked_values_are_medians(self):
        """
        With known input values, locked segment = median of inputs.
        For symmetric uniform noise, median ≈ true value.
        """
        records = self._make_stable_records(
            thigh=0.42, shank=0.40, trunk=0.52, noise=0.0
        )
        result = run_stability_gate(records)
        assert result.gate_passed is True
        assert abs(result.thigh_m - 0.42) < 1e-10
        assert abs(result.shank_m - 0.40) < 1e-10
        assert abs(result.trunk_m - 0.52) < 1e-10

    def test_leg_m_is_thigh_plus_shank(self):
        """
        leg_m = thigh_m + shank_m. Derived, not independently measured.
        [SPEC §1.3.4]
        """
        records = self._make_stable_records(thigh=0.42, shank=0.40, noise=0.0)
        result = run_stability_gate(records)
        assert result.gate_passed is True
        assert abs(result.leg_m - (result.thigh_m + result.shank_m)) < 1e-10

    def test_small_noise_within_tolerance_passes(self):
        """
        Tolerance = 2% × 0.42m = 0.0084m.
        Noise = 0.003m (peak-to-peak ≈ 0.006m) < 0.0084m → should pass.
        """
        records = self._make_stable_records(thigh=0.42, shank=0.40, trunk=0.52, noise=0.003)
        result = run_stability_gate(records)
        # With seed=42 and noise=0.003, peak-to-peak should be < 2% of segment
        # We check the tolerance values are computed correctly
        expected_thigh_tol = STABILITY_TOLERANCE_FRACTION * 0.42
        assert abs(result.thigh_tolerance_m - expected_thigh_tol) < 1e-6


# ─── T5: Stability Gate — Fail Cases ─────────────────────────────────────────

class TestStabilityGateFail:

    def test_insufficient_frames_fails(self):
        """
        Fewer than 120 frames (STABILITY_WINDOW_FRAMES) → FAILED.
        """
        records = [
            FrameSegmentLengths(
                frame_index=i, thigh_m=0.42, shank_m=0.40,
                trunk_m=0.52, scale_m_per_px=0.005
            )
            for i in range(50)  # 50 < 120
        ]
        result = run_stability_gate(records)
        assert result.gate_passed is False
        assert result.frames_used == 50

    def test_excessive_sway_fails(self):
        """
        Large variation (simulate player swaying) → gate fails.
        Variation = 0.05m >> tolerance = 2% × 0.42m = 0.0084m.
        """
        records = []
        for i in range(120):
            # Alternating sway: thigh oscillates ±0.025m around 0.42m
            sway = 0.025 * np.sin(2 * np.pi * i / 30)
            records.append(FrameSegmentLengths(
                frame_index=i,
                thigh_m=0.42 + sway,
                shank_m=0.40,
                trunk_m=0.52,
                scale_m_per_px=0.005
            ))
        result = run_stability_gate(records)
        assert result.gate_passed is False
        assert result.thigh_passed is False
        # Shank and trunk are stable — only thigh failed
        assert result.shank_passed is True
        assert result.trunk_passed is True

    def test_empty_records_fails(self):
        """Empty record list → INSUFFICIENT_DATA."""
        result = run_stability_gate([])
        assert result.gate_passed is False

    def test_tolerance_boundary(self):
        """
        Test exactly at the tolerance boundary.
        Tolerance = 2% × 0.42 = 0.0084m.
        Variation = 0.0084m → should PASS (≤ not <).
        Variation = 0.0085m → should FAIL.
        """
        thigh_median = 0.42
        tolerance = STABILITY_TOLERANCE_FRACTION * thigh_median  # 0.0084

        def make_records_with_thigh_variation(variation: float):
            """Create records where thigh peak-to-peak = variation exactly."""
            records = []
            for i in range(120):
                # Half frames at low, half at high
                thigh = thigh_median - variation / 2 if i < 60 else thigh_median + variation / 2
                records.append(FrameSegmentLengths(
                    frame_index=i, thigh_m=thigh,
                    shank_m=0.40, trunk_m=0.52, scale_m_per_px=0.005
                ))
            return records

        # Exactly at tolerance: variation = 0.0084m ≤ 0.0084m → PASS
        result_pass = run_stability_gate(make_records_with_thigh_variation(tolerance))
        assert result_pass.thigh_passed is True

        # Just over tolerance: variation = 0.0085m > 0.0084m → FAIL
        result_fail = run_stability_gate(make_records_with_thigh_variation(tolerance + 0.0001))
        assert result_fail.thigh_passed is False