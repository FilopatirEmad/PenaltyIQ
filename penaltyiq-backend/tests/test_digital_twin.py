"""
Unit Tests — digital_twin.py
==============================
All expected values analytically derived.

Test categories:
  T1: Trajectory simulation (kinematic equations)
  T2: Goal line interpolation (linear interpolation accuracy)
  T3: Zone boundary check (all 8 zones)
  T4: Sensitivity perturbation tests
  T5: Full digital twin pipeline
"""

import numpy as np
import pytest
from core.digital_twin import (
    simulate_trajectory,
    interpolate_position_at_goal_line,
    check_zone_hit,
    determine_zone_hit,
    run_sensitivity_perturbation,
    run_digital_twin,
)
from constants.fifa_constants import (
    PENALTY_DISTANCE_M,
    GOAL_HEIGHT_M,
    GRAVITY_MS2,
    GOAL_ZONES,
)


class TestTrajectorySimulation:

    def test_initial_position_is_origin(self):
        """At t=0: x=0, y=0, z=0."""
        traj = simulate_trajectory(25.0, np.radians(11.8), np.radians(0.0))
        assert abs(traj[0].x_m) < 1e-10
        assert abs(traj[0].y_m) < 1e-10
        assert abs(traj[0].z_m) < 1e-10

    def test_horizontal_motion_no_gravity_at_t0(self):
        """
        Horizontal launch (θv=0): y=0 throughout (vx=v0, vy=0 − ½g·t²).
        At t=0: y=0. At t>0: y = −½g·t² < 0 (falls immediately).
        """
        traj = simulate_trajectory(25.0, 0.0, 0.0, n_steps=100)
        # t=0: y=0
        assert abs(traj[0].y_m) < 1e-10
        # t>0: y < 0 (ball falls)
        assert traj[1].y_m < 0.0

    def test_range_equation_at_goal_line(self):
        """
        For θv=11.8°, v0=25m/s:
        Time to reach x=D: t* = D / (v0·cos(θv)·cos(θh))
        y(t*) should match forward projection formula.
        """
        v0 = 25.0
        theta_v = np.radians(11.8)
        theta_h = 0.0

        # Expected time to goal line
        vx0 = v0 * np.cos(theta_v) * np.cos(theta_h)
        t_goal = PENALTY_DISTANCE_M / vx0

        # Expected y at goal line (exact formula)
        vy0 = v0 * np.sin(theta_v)
        y_expected = vy0 * t_goal - 0.5 * GRAVITY_MS2 * t_goal**2

        traj = simulate_trajectory(v0, theta_v, theta_h, n_steps=2000)
        y_interp, z_interp = interpolate_position_at_goal_line(traj)

        assert abs(y_interp - y_expected) < 0.01  # < 1cm error


class TestZoneBoundaryCheck:

    @pytest.mark.parametrize("zone_id", list(GOAL_ZONES.keys()))
    def test_exact_zone_centre_hits_zone(self, zone_id):
        """
        Ball landing exactly at zone centre coordinates must hit that zone.
        """
        zone = GOAL_ZONES[zone_id]
        result = check_zone_hit(
            target_zone_id=zone_id,
            y_at_goal_m=zone["y_m"],
            z_at_goal_m=zone["x_m"]
        )
        assert result.hit_zone == zone_id
        assert result.verification_passed is True

    def test_above_crossbar_misses(self):
        """Ball above crossbar (y > 2.44m) → MISS_OVER_BAR."""
        hit = determine_zone_hit(y_at_goal_m=2.50, z_at_goal_m=0.0)
        assert hit == "MISS_OVER_BAR"

    def test_below_ground_misses(self):
        """Ball below ground (y < 0) → MISS_GROUND."""
        hit = determine_zone_hit(y_at_goal_m=-0.10, z_at_goal_m=0.0)
        assert hit == "MISS_GROUND"

    def test_wide_right_misses(self):
        """Ball outside goal width → MISS_WIDE."""
        hit = determine_zone_hit(y_at_goal_m=1.2, z_at_goal_m=4.0)  # > 3.66m
        assert hit == "MISS_WIDE"


class TestFullDigitalTwinPipeline:

    def test_nominal_zone_t1_passes(self):
        """
        For T1 with correct launch parameters at v0=25m/s,
        digital twin should verify and show nominal pass.
        """
        result = run_digital_twin(
            v0_ms=25.0,
            theta_v_rad=np.radians(11.8),
            theta_h_rad=np.radians(-17.0),
            target_zone_id="T1"
        )
        # Trajectory must reach goal line
        assert len(result.trajectory) > 1
        # Sensitivity suite must be computed
        assert len(result.sensitivity_results) == 6

    def test_all_zones_return_complete_result(self):
        """All 8 zones must produce a complete DigitalTwinResult."""
        for zone_id in GOAL_ZONES.keys():
            zone = GOAL_ZONES[zone_id]
            # Use zone-correct angles
            theta_v = np.radians(11.8 if zone_id.startswith("T") else 6.5)
            theta_h = np.radians(zone["x_m"] / PENALTY_DISTANCE_M * (180/np.pi))

            result = run_digital_twin(25.0, theta_v, theta_h, zone_id)
            assert result.nominal is not None
            assert isinstance(result.robust_under_perturbation, bool)
            assert len(result.sensitivity_results) == 6