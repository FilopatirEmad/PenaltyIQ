"""
Unit Tests — physics_engine.py
================================
All expected values are analytically computed — no magic numbers.

Test categories:
  T1: Scale conversion (ball px → metric positions)
  T2: v0 estimation (3-interval average, dimensional analysis)
  T3: Speed regime classification (boundary conditions)
  T4: θh computation (known geometry, arctan verification)
  T5: θv computation (inverse formula verification)
  T6: Forward projection consistency (inverse → forward round-trip)
  T7: Crossbar safety margin
  T8: Full pipeline integration (reference table verification)
  T9: Edge cases and error handling
"""

import numpy as np
import pytest
from core.physics_engine import (
    pixel_ball_centers_to_metric,
    estimate_v0,
    classify_speed_regime,
    compute_horizontal_launch_angle,
    compute_vertical_launch_angle,
    compute_launch_angles_for_zone,
    compute_predicted_height_at_goal,
    check_crossbar_safety_margin,
    run_physics_pipeline,
    BallPosition,
    V0_HIGH_THRESHOLD_MS,
    V0_LOW_THRESHOLD_MS,
)
from constants.fifa_constants import (
    BALL_DIAMETER_M,
    PENALTY_DISTANCE_M,
    GOAL_HEIGHT_M,
    GRAVITY_MS2,
    CROSSBAR_SAFETY_MARGIN_M,
    GOAL_ZONES,
)


# ─── T1: Pixel → Metric Conversion ───────────────────────────────────────────

class TestPixelToMetricConversion:

    def test_scale_applied_correctly(self):
        """
        S = 0.005 m/px. Ball at (100, 200)px → (0.5, 1.0)m.
        x_m = 0.005 × 100 = 0.5m
        y_m = 0.005 × 200 = 1.0m
        """
        scale = BALL_DIAMETER_M / 44.0  # 0.005 m/px
        positions = pixel_ball_centers_to_metric(
            [(100.0, 200.0), (110.0, 205.0)], scale
        )
        assert abs(positions[0].x_m - 0.5)  < 1e-10
        assert abs(positions[0].y_m - 1.0)  < 1e-10
        assert abs(positions[1].x_m - 0.55) < 1e-10
        assert abs(positions[1].y_m - 1.025) < 1e-10

    def test_round_trip_with_ball_diameter(self):
        """
        At scale = 0.22/44 = 0.005 m/px:
        Ball at 44px diameter → S × 44 = 0.22m. [FIFA-2024] round-trip.
        """
        scale = BALL_DIAMETER_M / 44.0
        assert abs(scale * 44.0 - BALL_DIAMETER_M) < 1e-12


# ─── T2: v0 Estimation ───────────────────────────────────────────────────────

class TestV0Estimation:

    def _make_linear_motion(
        self,
        v0_ms: float,
        fps: float = 60.0,
        n_frames: int = 4
    ) -> list[BallPosition]:
        """
        Generate ball positions for constant-speed motion along x-axis.
        Each frame advances by v0 × dt = v0/fps metres.
        """
        dt = 1.0 / fps
        step = v0_ms * dt
        positions = []
        for i in range(n_frames):
            positions.append(BallPosition(
                frame_index=i,
                x_m=float(i) * step,
                y_m=0.0
            ))
        return positions

    def test_constant_speed_exact_recovery(self):
        """
        For constant linear motion at v0=25 m/s:
        Each frame step = 25/60 = 0.41667m.
        All three intervals give 0.41667m / (1/60s) = 25.0 m/s.
        Average = 25.0 m/s exactly.
        """
        TARGET_V0 = 25.0
        positions = self._make_linear_motion(v0_ms=TARGET_V0, fps=60.0)
        v0_est, displacements = estimate_v0(positions, fps=60.0)

        assert abs(v0_est - TARGET_V0) < 1e-8, (
            f"Expected v0={TARGET_V0}, got {v0_est:.10f}"
        )
        # All three displacements should be equal = v0 × dt
        expected_displacement = TARGET_V0 / 60.0  # 0.41667m
        for d in displacements:
            assert abs(d - expected_displacement) < 1e-8

    def test_three_displacements_returned(self):
        """Exactly 3 displacement values must be returned. [SPEC §2.4]"""
        positions = self._make_linear_motion(v0_ms=20.0)
        _, displacements = estimate_v0(positions)
        assert len(displacements) == 3

    def test_dimensional_consistency(self):
        """
        v0 units: displacement [m] / dt [s] = m/s.
        For displacement = 0.40m, dt = 1/60s:
        v0 = 0.40 / (1/60) = 24.0 m/s.
        """
        positions = [
            BallPosition(frame_index=0, x_m=0.00, y_m=0.0),
            BallPosition(frame_index=1, x_m=0.40, y_m=0.0),
            BallPosition(frame_index=2, x_m=0.80, y_m=0.0),
            BallPosition(frame_index=3, x_m=1.20, y_m=0.0),
        ]
        v0_est, _ = estimate_v0(positions, fps=60.0)
        expected = 0.40 / (1.0 / 60.0)  # 24.0 m/s
        assert abs(v0_est - expected) < 1e-8

    def test_insufficient_positions_raises(self):
        """Fewer than 4 positions → ValueError. [SPEC §2.4]"""
        positions = [
            BallPosition(0, 0.0, 0.0),
            BallPosition(1, 0.4, 0.0),
        ]  # Only 2 — need 4
        with pytest.raises(ValueError, match="4 ball positions"):
            estimate_v0(positions)

    def test_diagonal_motion_2d_norm(self):
        """
        Ball moves at 45° angle: Δx = Δy = 0.3m per frame.
        Euclidean displacement = sqrt(0.3² + 0.3²) = 0.4243m.
        v0 = 0.4243 / (1/60) = 25.46 m/s.
        """
        delta = 0.3  # m per frame along each axis
        positions = [
            BallPosition(frame_index=i, x_m=i*delta, y_m=i*delta)
            for i in range(4)
        ]
        v0_est, displacements = estimate_v0(positions, fps=60.0)
        expected_disp = np.sqrt(delta**2 + delta**2)
        expected_v0 = expected_disp / (1.0/60.0)
        assert abs(v0_est - expected_v0) < 1e-8
        for d in displacements:
            assert abs(d - expected_disp) < 1e-8


# ─── T3: Speed Regime ────────────────────────────────────────────────────────

class TestSpeedRegime:

    def test_high_boundary_exact(self):
        """v0 = V0_HIGH_THRESHOLD_MS → HIGH."""
        assert classify_speed_regime(V0_HIGH_THRESHOLD_MS) == "HIGH"

    def test_high_above_threshold(self):
        assert classify_speed_regime(25.0) == "HIGH"
        assert classify_speed_regime(30.0) == "HIGH"

    def test_moderate_range(self):
        assert classify_speed_regime(14.0) == "MODERATE"
        assert classify_speed_regime(17.0) == "MODERATE"
        assert classify_speed_regime(19.99) == "MODERATE"

    def test_low_below_threshold(self):
        assert classify_speed_regime(13.99) == "LOW"
        assert classify_speed_regime(10.0) == "LOW"
        assert classify_speed_regime(5.0) == "LOW"


# ─── T4: Horizontal Launch Angle θh ─────────────────────────────────────────

class TestHorizontalAngle:

    def test_straight_ahead_zero_deflection(self):
        """
        x_target = 0 → θh = arctan(0/11) = 0°.
        Straight ahead — no horizontal deflection.
        """
        _, theta_h_deg = compute_horizontal_launch_angle(0.0)
        assert abs(theta_h_deg - 0.0) < 1e-10

    def test_far_corner_analytical(self):
        """
        Zone T1: x_target = -3.36m, D = 11.0m.
        θh = arctan(-3.36/11.0) = arctan(-0.30545...) = -16.99...°
        [SPEC Table 2.2] reports |θh| = 17.0° for T1.
        """
        x_target = GOAL_ZONES["T1"]["x_m"]  # -3.36
        _, theta_h_deg = compute_horizontal_launch_angle(x_target)
        expected_deg = np.degrees(np.arctan(-3.36 / 11.0))
        assert abs(theta_h_deg - expected_deg) < 1e-8
        # Magnitude should be ≈ 17.0° [SPEC Table 2.2]
        assert abs(abs(theta_h_deg) - 17.0) < 0.1

    def test_centre_zone_small_angle(self):
        """
        Zone T2: x_target = -1.22m, D = 11.0m.
        θh = arctan(-1.22/11.0). [SPEC Table 2.2] reports |θh| = 6.3°.
        """
        x_target = GOAL_ZONES["T2"]["x_m"]  # -1.22
        _, theta_h_deg = compute_horizontal_launch_angle(x_target)
        assert abs(abs(theta_h_deg) - 6.3) < 0.1

    def test_sign_symmetry(self):
        """
        θh(+x) = -θh(-x): left and right deflections are symmetric.
        """
        _, left  = compute_horizontal_launch_angle(-3.36)
        _, right = compute_horizontal_launch_angle(+3.36)
        assert abs(left + right) < 1e-10  # left = -right


# ─── T5: Vertical Launch Angle θv ────────────────────────────────────────────

class TestVerticalAngle:

    def test_reference_table_top_zones_v0_25(self):
        """
        [SPEC Table 2.2]: At v0=25m/s, θv for all top zones = 11.8°.
        y_target = 2.20m, D = 11.0m, g = 9.80665m/s², v0 = 25m/s.
        Compute analytically and verify against spec table.
        """
        y_target = 2.20
        v0 = 25.0
        geometry_term = y_target / PENALTY_DISTANCE_M
        gravity_term  = (GRAVITY_MS2 * PENALTY_DISTANCE_M) / (2.0 * v0**2)
        expected_theta_v = np.degrees(np.arctan(geometry_term + gravity_term))

        _, theta_v_deg = compute_vertical_launch_angle(y_target, v0)

        assert abs(theta_v_deg - expected_theta_v) < 1e-8
        # Spec table reports 11.8° — verify within 0.2° (rounding)
        assert abs(theta_v_deg - 11.8) < 0.2

    def test_reference_table_bottom_zones_v0_25(self):
        """
        [SPEC Table 2.2]: At v0=25m/s, θv for bottom zones = 1.6°.
        """
        y_target = 0.30
        v0 = 25.0
        _, theta_v_deg = compute_vertical_launch_angle(y_target, v0)
        assert abs(theta_v_deg - 1.6) < 0.2

    def test_higher_speed_requires_lower_angle(self):
        """
        Physical law: higher v0 → less gravity correction needed → smaller θv.
        [SPEC §2.7.1] Table 2.3 confirms this monotonic relationship.
        """
        y_target = 2.20
        _, theta_low_speed  = compute_vertical_launch_angle(y_target, 10.0)
        _, theta_high_speed = compute_vertical_launch_angle(y_target, 25.0)
        assert theta_low_speed > theta_high_speed

    def test_spec_table_2_3_sensitivity(self):
        """
        [SPEC Table 2.3]: Required θv for Zone T1 at various v0.
        v0=10 m/s → θv ≈ 36.5°
        v0=15 m/s → θv ≈ 17.5°
        v0=25 m/s → θv ≈ 11.8°
        Tolerance: ±0.5° (spec table is rounded to 1 decimal).
        """
        y_target = 2.20  # Zone T1
        expected = {10.0: 36.5, 15.0: 17.5, 25.0: 11.8}
        for v0, theta_expected in expected.items():
            _, theta_v = compute_vertical_launch_angle(y_target, v0)
            assert abs(theta_v - theta_expected) < 0.5, (
                f"v0={v0} m/s: expected θv≈{theta_expected}°, got {theta_v:.2f}°"
            )

    def test_zero_v0_raises(self):
        """v0 = 0 is physically impossible → ValueError."""
        with pytest.raises(ValueError, match="v0_ms must be > 0"):
            compute_vertical_launch_angle(2.20, 0.0)

    def test_negative_v0_raises(self):
        with pytest.raises(ValueError, match="v0_ms must be > 0"):
            compute_vertical_launch_angle(2.20, -5.0)


# ─── T6: Forward Projection Round-Trip ───────────────────────────────────────

class TestForwardProjectionRoundTrip:
    """
    Verify that forward projection of θv (exact formula) recovers y_target.
    This validates the small-angle approximation used in the inverse formula.
    Acceptable residual: < 0.01m (< 1cm) for all penalty zones.
    """

    @pytest.mark.parametrize("zone_id,v0", [
        ("T1", 25.0), ("T2", 25.0), ("T3", 20.0), ("T4", 30.0),
        ("B1", 25.0), ("B2", 25.0), ("B3", 20.0), ("B4", 15.0),
    ])
    def test_inverse_forward_residual(self, zone_id, v0):
        """
        For every zone and speed combination:
        1. Compute θv from inverse formula (approximate).
        2. Forward-project y(D) using exact formula.
        3. Residual |y_predicted - y_target| must be < 0.01m.
        """
        zone = GOAL_ZONES[zone_id]
        y_target = zone["y_m"]

        _, theta_v_rad_list = compute_vertical_launch_angle.__wrapped__ \
            if hasattr(compute_vertical_launch_angle, '__wrapped__') \
            else (None, None)

        # Direct computation
        theta_v_rad, theta_v_deg = compute_vertical_launch_angle(y_target, v0)

        y_predicted = compute_predicted_height_at_goal(
            v0_ms=v0,
            theta_v_rad=theta_v_rad
        )

        residual = abs(y_predicted - y_target)

        assert residual < 0.01, (
            f"Zone {zone_id}, v0={v0}m/s: "
            f"y_target={y_target}m, y_predicted={y_predicted:.4f}m, "
            f"residual={residual:.4f}m ≥ 0.01m tolerance. "
            f"Small-angle approximation violated."
        )


# ─── T7: Crossbar Safety Margin ──────────────────────────────────────────────

class TestCrossbarSafetyMargin:

    def test_safe_clearance_passes(self):
        """
        Ball at 2.10m < H-Δbar = 2.44-0.15 = 2.29m → safety satisfied.
        Clearance = 2.44 - 2.10 = 0.34m ≥ 0.15m.
        """
        clearance, satisfied = check_crossbar_safety_margin(2.10)
        assert satisfied is True
        assert abs(clearance - (GOAL_HEIGHT_M - 2.10)) < 1e-10
        assert clearance >= CROSSBAR_SAFETY_MARGIN_M

    def test_exactly_at_margin_boundary(self):
        """
        y = H - Δbar = 2.44 - 0.15 = 2.29m → clearance = 0.15m = Δbar → passes.
        Boundary condition: ≤ not <.
        """
        y_at_margin = GOAL_HEIGHT_M - CROSSBAR_SAFETY_MARGIN_M  # 2.29m
        clearance, satisfied = check_crossbar_safety_margin(y_at_margin)
        assert satisfied is True
        assert abs(clearance - CROSSBAR_SAFETY_MARGIN_M) < 1e-10

    def test_over_margin_fails(self):
        """
        y = 2.30m > H - Δbar = 2.29m → clearance = 0.14m < 0.15m → fails.
        """
        clearance, satisfied = check_crossbar_safety_margin(2.30)
        assert satisfied is False
        assert clearance < CROSSBAR_SAFETY_MARGIN_M

    def test_crossbar_height_exceeded_fails(self):
        """Ball above crossbar (y > 2.44m) → negative clearance → fails."""
        clearance, satisfied = check_crossbar_safety_margin(2.50)
        assert satisfied is False
        assert clearance < 0.0


# ─── T8: Full Pipeline Reference Table Verification ─────────────────────────

class TestFullPipelineReferenceTable:
    """
    Verify the full pipeline against [SPEC Table 2.2] reference values.
    Reference: v0 = 25 m/s. All zones.
    """

    REFERENCE_ANGLES = {
        # [SPEC Table 2.2]
        "T1": {"theta_v": 11.8, "theta_h": 17.0},
        "T2": {"theta_v": 11.8, "theta_h": 6.3},
        "T3": {"theta_v": 11.8, "theta_h": 6.3},
        "T4": {"theta_v": 11.8, "theta_h": 17.0},
        "B1": {"theta_v": 1.6,  "theta_h": 17.0},
        "B2": {"theta_v": 1.6,  "theta_h": 6.3},
        "B3": {"theta_v": 1.6,  "theta_h": 6.3},
        "B4": {"theta_v": 1.6,  "theta_h": 17.0},
    }

    @pytest.mark.parametrize("zone_id", list(REFERENCE_ANGLES.keys()))
    def test_angles_match_spec_table_2_2(self, zone_id):
        """
        All computed angles must match [SPEC Table 2.2] within ±0.3°.
        Tolerance: spec table is rounded to 1 decimal place.
        """
        angles = compute_launch_angles_for_zone(zone_id, v0_ms=25.0)
        ref = self.REFERENCE_ANGLES[zone_id]

        assert abs(angles.theta_v_deg - ref["theta_v"]) < 0.3, (
            f"Zone {zone_id}: θv={angles.theta_v_deg:.3f}° ≠ {ref['theta_v']}° "
            f"(from [SPEC Table 2.2])"
        )
        assert abs(abs(angles.theta_h_deg) - ref["theta_h"]) < 0.3, (
            f"Zone {zone_id}: |θh|={abs(angles.theta_h_deg):.3f}° ≠ {ref['theta_h']}° "
            f"(from [SPEC Table 2.2])"
        )

    def test_full_pipeline_run(self):
        """
        End-to-end pipeline test with synthetic ball tracking data.
        v0 = 25 m/s → step per frame = 25/60 m = 0.41667m.
        Scale = 0.22/44 = 0.005 m/px.
        Ball positions in pixels: step_px = 0.41667/0.005 = 83.33px per frame.
        """
        scale = BALL_DIAMETER_M / 44.0  # 0.005 m/px
        v0_target = 25.0
        step_m = v0_target / 60.0       # 0.41667m per frame
        step_px = step_m / scale        # 83.33px per frame

        # 4 ball positions along x-axis (horizontal motion)
        ball_positions_px = [
            (i * step_px, 500.0)        # constant y_px (horizontal flight)
            for i in range(4)
        ]

        result = run_physics_pipeline(
            ball_positions_px=ball_positions_px,
            scale_m_per_px=scale,
            zone_id="T1",
            fps=60.0
        )

        assert abs(result.v0_ms - 25.0) < 0.01
        assert abs(result.launch_angles.theta_v_deg - 11.8) < 0.3
        assert abs(abs(result.launch_angles.theta_h_deg) - 17.0) < 0.3
        assert result.speed_regime == "HIGH"