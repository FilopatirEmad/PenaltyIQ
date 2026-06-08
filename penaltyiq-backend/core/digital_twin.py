"""
Digital Twin — Forward Verification Module
============================================
Implements the forward simulation loop described in [SPEC §5].

Purpose:
    After the physics engine computes (θv, θh, v0) and the IK solver
    computes joint targets, the Digital Twin forward-simulates the ball
    trajectory to verify that the computed launch parameters actually
    land the ball in the selected goal zone (with safety margins).

    This provides an independent consistency check before coaching
    feedback is delivered to the user.

Pipeline [SPEC §5.2]:
    1. Receive (v0, θv, θh) from physics engine.
    2. Forward-simulate 3D projectile trajectory.
    3. Compute ball position at x = D (goal line).
    4. Check if (z_goal, y_goal) lies within the zone rectangle.
    5. Run sensitivity perturbation tests [SPEC §5.3].
    6. Return verification result with zone hit and error metrics.

Coordinate system [MODEL]:
    - Origin: penalty spot (ball position at kick).
    - x-axis: forward (toward goal), range [0, D=11m].
    - y-axis: vertical (upward), range [0, H=2.44m].
    - z-axis: lateral (right = positive), range [−W/2, W/2].
    - θv: vertical launch angle (x-y plane).
    - θh: horizontal deflection angle (x-z plane).

Projectile model assumptions [MODEL][SPEC §6.2]:
    - Vacuum projectile (no aerodynamic drag in trajectory computation).
    - Drag effect handled via crossbar safety margin in physics_engine.py.
    - Ball launched from ground level (y0 = 0).
    - No spin/Magnus effect (not measurable from 2D monocular video).

Scientific basis:
    [SPEC §5.1–5.3]   Digital twin verification framework.
    [SPEC §2.8]        Aerodynamic safety margin.
    [FIFA-2024]        Goal dimensions, zone geometry.
    [WINTER-2009] Ch.3 Sensitivity analysis methodology.
"""

import numpy as np
import logging
from dataclasses import dataclass, field
from typing import Optional

from constants.fifa_constants import (
    PENALTY_DISTANCE_M,
    GOAL_WIDTH_M,
    GOAL_HEIGHT_M,
    GRAVITY_MS2,
    GOAL_ZONES,
    ZONE_WIDTH_M,
    ZONE_HEIGHT_M,
    CROSSBAR_SAFETY_MARGIN_M,
)

logger = logging.getLogger("penaltyiq.digital_twin")


# ─── Sensitivity Perturbation Parameters ──────────────────────────────────────

# [SPEC §5.3]: Perturbation ranges for robustness testing.
# "Landmark noise equivalent to ±1–2° angle jitter"
ANGLE_PERTURBATION_DEG: float = 2.0   # degrees

# "Scaling uncertainty: ±5% ball-size measurement error"
SCALE_PERTURBATION_FRACTION: float = 0.05  # ±5%

# "Speed variation: plausible v0 fluctuation"
# At 60fps, v0 uncertainty ≈ ±0.3 m/s from pixel detection noise [SPEC §2.4 LIMIT]
V0_PERTURBATION_MS: float = 0.5   # m/s (conservative ±0.5 m/s)

# Tolerance for zone boundary check [MODEL]
# Zone is W/4 wide = 1.83m, H/2 tall = 1.22m.
# We use exact boundaries (no padding) — safety margin is in physics_engine.py.
ZONE_BOUNDARY_TOLERANCE_M: float = 0.0


# ─── Data Structures ──────────────────────────────────────────────────────────

@dataclass
class TrajectoryPoint:
    """Ball position at a single time step in the forward simulation."""
    t_s: float      # time [s]
    x_m: float      # forward (toward goal) [m]
    y_m: float      # vertical (upward) [m]
    z_m: float      # lateral (rightward) [m]


@dataclass
class ZoneHitResult:
    """Result of the zone boundary check at the goal line."""
    zone_id: str          # target zone
    hit_zone: str         # zone that was actually hit (or "MISS")
    verification_passed: bool

    # Ball position at goal line
    y_at_goal_m: float    # vertical [m]
    z_at_goal_m: float    # lateral [m]

    # Error metrics
    y_error_m: float      # |y_at_goal − y_target| [m]
    z_error_m: float      # |z_at_goal − z_target| [m]

    # Zone boundary information
    y_target_m: float
    z_target_m: float
    y_zone_min_m: float
    y_zone_max_m: float
    z_zone_min_m: float
    z_zone_max_m: float

    # Safety margin
    crossbar_clearance_m: float
    above_ground: bool


@dataclass
class SensitivityResult:
    """Result of a single sensitivity perturbation test."""
    perturbation_type: str   # "ANGLE_V", "ANGLE_H", "SPEED", "SCALE"
    perturbation_value: float
    zone_hit: str
    verification_passed: bool
    y_at_goal_m: float
    z_at_goal_m: float


@dataclass
class DigitalTwinResult:
    """
    Complete output of the digital twin verification.
    Includes nominal trajectory, zone check, and sensitivity tests.
    """
    # Nominal result
    nominal: ZoneHitResult
    trajectory: list[TrajectoryPoint]

    # Sensitivity analysis [SPEC §5.3]
    sensitivity_results: list[SensitivityResult]
    robust_under_perturbation: bool   # True if all sensitivity tests pass

    # Summary
    overall_verified: bool   # nominal AND (robust OR acceptable_failure_rate)
    warnings: list[str] = field(default_factory=list)


# ─── Module 1: 3D Projectile Forward Simulation ───────────────────────────────

def simulate_trajectory(
    v0_ms: float,
    theta_v_rad: float,
    theta_h_rad: float,
    n_steps: int = 200,
    t_max_s: float = 1.0,
    gravity_ms2: float = GRAVITY_MS2
) -> list[TrajectoryPoint]:
    """
    Simulate the 3D ball trajectory under vacuum projectile model.

    Equations of motion [SPEC §5.2][MODEL]:
        x(t) = v0 · cos(θv) · cos(θh) · t        [forward]
        y(t) = v0 · sin(θv) · t − ½ · g · t²     [vertical]
        z(t) = v0 · cos(θv) · sin(θh) · t         [lateral]

    Derivation:
        The initial velocity vector is decomposed as:
            vx0 = v0 · cos(θv) · cos(θh)   [forward component]
            vy0 = v0 · sin(θv)              [vertical component]
            vz0 = v0 · cos(θv) · sin(θh)   [lateral component]

        In the x-direction (no forces): x(t) = vx0 · t
        In the y-direction (gravity):  y(t) = vy0 · t − ½g·t²
        In the z-direction (no forces): z(t) = vz0 · t

        These are the standard equations of projectile motion.
        [SPEC §5.2] specifies this as the forward simulation loop.

    Parameters
    ----------
    v0_ms : float
        Ball launch speed [m/s].
    theta_v_rad : float
        Vertical launch angle [radians].
    theta_h_rad : float
        Horizontal deflection angle [radians].
    n_steps : int
        Number of time steps for trajectory discretisation.
    t_max_s : float
        Maximum simulation time [s]. Ball crosses D=11m in ~0.4s at 25m/s.
    gravity_ms2 : float
        Standard gravity [m/s²].

    Returns
    -------
    trajectory : list of TrajectoryPoint
        Time-ordered ball positions. Simulation stops when y < 0 (ground)
        or x > D + 1m (past goal line).
    """
    # Initial velocity components
    vx0 = v0_ms * np.cos(theta_v_rad) * np.cos(theta_h_rad)
    vy0 = v0_ms * np.sin(theta_v_rad)
    vz0 = v0_ms * np.cos(theta_v_rad) * np.sin(theta_h_rad)

    logger.debug(
        f"Trajectory simulation: v0={v0_ms:.3f}m/s, "
        f"θv={np.degrees(theta_v_rad):.3f}°, "
        f"θh={np.degrees(theta_h_rad):.3f}°. "
        f"Initial velocities: vx={vx0:.3f}, vy={vy0:.3f}, vz={vz0:.3f} m/s"
    )

    t_values = np.linspace(0.0, t_max_s, n_steps)
    trajectory: list[TrajectoryPoint] = []

    for t in t_values:
        x = vx0 * t
        y = vy0 * t - 0.5 * gravity_ms2 * t**2
        z = vz0 * t

        trajectory.append(TrajectoryPoint(t_s=float(t), x_m=float(x),
                                          y_m=float(y), z_m=float(z)))

        # Stop if ball hits ground or goes past goal line + 1m margin
        if y < 0.0 and t > 0.01:   # t > 0.01 avoids stopping at t=0
            logger.debug(f"Trajectory stopped at t={t:.4f}s: ball hit ground (y={y:.4f}m)")
            break
        if x > PENALTY_DISTANCE_M + 1.0:
            logger.debug(f"Trajectory stopped at t={t:.4f}s: ball past goal line (x={x:.4f}m)")
            break

    return trajectory


def interpolate_position_at_goal_line(
    trajectory: list[TrajectoryPoint],
    penalty_distance_m: float = PENALTY_DISTANCE_M
) -> tuple[float, float]:
    """
    Interpolate ball position (y, z) at x = D (goal line).

    Uses linear interpolation between the two trajectory points that
    bracket x = D. This avoids discretisation error from the fixed
    time grid.

    Parameters
    ----------
    trajectory : list of TrajectoryPoint
        Simulated ball trajectory.
    penalty_distance_m : float
        Goal line distance [m]. Default 11.00m [FIFA-2024].

    Returns
    -------
    y_at_goal : float — vertical position at goal line [m]
    z_at_goal : float — lateral position at goal line [m]

    Raises
    ------
    ValueError
        If trajectory does not reach the goal line (ball hits ground first).
    """
    D = penalty_distance_m

    # Find the two points bracketing x = D
    for i in range(len(trajectory) - 1):
        p0 = trajectory[i]
        p1 = trajectory[i + 1]

        if p0.x_m <= D <= p1.x_m:
            # Linear interpolation factor
            if abs(p1.x_m - p0.x_m) < 1e-12:
                alpha = 0.0
            else:
                alpha = (D - p0.x_m) / (p1.x_m - p0.x_m)

            y_at_goal = p0.y_m + alpha * (p1.y_m - p0.y_m)
            z_at_goal = p0.z_m + alpha * (p1.z_m - p0.z_m)

            logger.debug(
                f"Goal line interpolation at x={D}m: "
                f"y={y_at_goal:.4f}m, z={z_at_goal:.4f}m "
                f"(α={alpha:.4f} between frames {i} and {i+1})"
            )

            return float(y_at_goal), float(z_at_goal)

    # If we reach here, trajectory never reached x = D
    max_x = max(p.x_m for p in trajectory)
    raise ValueError(
        f"Ball trajectory did not reach goal line (x={D}m). "
        f"Maximum x reached: {max_x:.3f}m. "
        f"This indicates v0 is too low for this zone. "
        f"Check speed regime feasibility flag."
    )


# ─── Module 2: Zone Boundary Check ───────────────────────────────────────────

def determine_zone_hit(
    y_at_goal_m: float,
    z_at_goal_m: float
) -> str:
    """
    Determine which goal zone (if any) the ball lands in.

    Zone boundary computation [MODEL][SPEC §2.3]:
        Each zone is ZONE_WIDTH_M = W/4 = 1.83m wide and
                        ZONE_HEIGHT_M = H/2 = 1.22m tall.

        Zone boundaries:
            z_min = z_target − ZONE_WIDTH_M/2
            z_max = z_target + ZONE_WIDTH_M/2
            y_min = y_target − ZONE_HEIGHT_M/2
            y_max = y_target + ZONE_HEIGHT_M/2

        Ball hits zone if z_min ≤ z ≤ z_max AND y_min ≤ y ≤ y_max.

    Parameters
    ----------
    y_at_goal_m : float — ball height at goal line [m]
    z_at_goal_m : float — ball lateral position at goal line [m]

    Returns
    -------
    zone_id : str — hit zone ("T1"–"B4") or "MISS" or "OUT_OF_GOAL"
    """
    # Check if ball is within goal frame at all
    if y_at_goal_m < 0.0:
        return "MISS_GROUND"
    if y_at_goal_m > GOAL_HEIGHT_M:
        return "MISS_OVER_BAR"
    if abs(z_at_goal_m) > GOAL_WIDTH_M / 2.0:
        return "MISS_WIDE"

    # Check each zone
    for zone_id, zone in GOAL_ZONES.items():
        z_min = zone["x_m"] - ZONE_WIDTH_M / 2.0
        z_max = zone["x_m"] + ZONE_WIDTH_M / 2.0
        y_min = zone["y_m"] - ZONE_HEIGHT_M / 2.0
        y_max = zone["y_m"] + ZONE_HEIGHT_M / 2.0

        if z_min <= z_at_goal_m <= z_max and y_min <= y_at_goal_m <= y_max:
            return zone_id

    return "MISS_BETWEEN_ZONES"


def check_zone_hit(
    target_zone_id: str,
    y_at_goal_m: float,
    z_at_goal_m: float
) -> ZoneHitResult:
    """
    Verify that the ball lands in the target zone and compute error metrics.

    Parameters
    ----------
    target_zone_id : str — intended target zone
    y_at_goal_m : float — ball height at goal line [m]
    z_at_goal_m : float — ball lateral position at goal line [m]

    Returns
    -------
    ZoneHitResult with all boundary and error information.
    """
    zone = GOAL_ZONES[target_zone_id]
    y_target = zone["y_m"]
    z_target = zone["x_m"]   # x_m in GOAL_ZONES is the lateral coordinate

    # Zone boundaries
    z_min = z_target - ZONE_WIDTH_M / 2.0
    z_max = z_target + ZONE_WIDTH_M / 2.0
    y_min = y_target - ZONE_HEIGHT_M / 2.0
    y_max = y_target + ZONE_HEIGHT_M / 2.0

    # Determine which zone was actually hit
    hit_zone = determine_zone_hit(y_at_goal_m, z_at_goal_m)
    verification_passed = (hit_zone == target_zone_id)

    # Error metrics
    y_error = abs(y_at_goal_m - y_target)
    z_error = abs(z_at_goal_m - z_target)

    # Safety checks
    crossbar_clearance = GOAL_HEIGHT_M - y_at_goal_m
    above_ground = y_at_goal_m > 0.0

    logger.info(
        f"Zone check: target={target_zone_id}, hit={hit_zone}, "
        f"y={y_at_goal_m:.3f}m (target={y_target}m, err={y_error:.3f}m), "
        f"z={z_at_goal_m:.3f}m (target={z_target}m, err={z_error:.3f}m), "
        f"crossbar_clearance={crossbar_clearance:.3f}m, "
        f"passed={verification_passed}"
    )

    return ZoneHitResult(
        zone_id=target_zone_id,
        hit_zone=hit_zone,
        verification_passed=verification_passed,
        y_at_goal_m=y_at_goal_m,
        z_at_goal_m=z_at_goal_m,
        y_error_m=y_error,
        z_error_m=z_error,
        y_target_m=y_target,
        z_target_m=z_target,
        y_zone_min_m=y_min,
        y_zone_max_m=y_max,
        z_zone_min_m=z_min,
        z_zone_max_m=z_max,
        crossbar_clearance_m=crossbar_clearance,
        above_ground=above_ground
    )


# ─── Module 3: Sensitivity Analysis ─────────────────────────────────────────

def run_sensitivity_perturbation(
    v0_ms: float,
    theta_v_rad: float,
    theta_h_rad: float,
    target_zone_id: str,
    perturbation_type: str,
    perturbation_value: float
) -> SensitivityResult:
    """
    Run a single perturbation test on the nominal launch parameters.

    Implements [SPEC §5.3]: "We perturb inputs to test stability."

    Perturbation types:
        "ANGLE_V"  : θv ± perturbation_value [radians]
        "ANGLE_H"  : θh ± perturbation_value [radians]
        "SPEED"    : v0 ± perturbation_value [m/s]

    Parameters
    ----------
    v0_ms : float — nominal ball speed [m/s]
    theta_v_rad : float — nominal vertical angle [radians]
    theta_h_rad : float — nominal horizontal angle [radians]
    target_zone_id : str — target zone
    perturbation_type : str — which parameter to perturb
    perturbation_value : float — perturbation magnitude (signed)

    Returns
    -------
    SensitivityResult
    """
    # Apply perturbation
    v0_p = v0_ms
    theta_v_p = theta_v_rad
    theta_h_p = theta_h_rad

    if perturbation_type == "ANGLE_V":
        theta_v_p = theta_v_rad + perturbation_value
    elif perturbation_type == "ANGLE_H":
        theta_h_p = theta_h_rad + perturbation_value
    elif perturbation_type == "SPEED":
        v0_p = v0_ms + perturbation_value
        v0_p = max(v0_p, 1.0)   # physical floor: v0 > 0
    else:
        raise ValueError(f"Unknown perturbation type: '{perturbation_type}'")

    # Forward simulate with perturbed parameters
    try:
        trajectory = simulate_trajectory(v0_p, theta_v_p, theta_h_p)
        y_goal, z_goal = interpolate_position_at_goal_line(trajectory)
        hit_zone = determine_zone_hit(y_goal, z_goal)
        passed = (hit_zone == target_zone_id)
    except ValueError:
        # Ball didn't reach goal line (very low v0 after negative perturbation)
        y_goal, z_goal = 0.0, 0.0
        hit_zone = "MISS_GROUND"
        passed = False

    return SensitivityResult(
        perturbation_type=perturbation_type,
        perturbation_value=perturbation_value,
        zone_hit=hit_zone,
        verification_passed=passed,
        y_at_goal_m=y_goal,
        z_at_goal_m=z_goal
    )


def run_full_sensitivity_suite(
    v0_ms: float,
    theta_v_rad: float,
    theta_h_rad: float,
    target_zone_id: str
) -> tuple[list[SensitivityResult], bool]:
    """
    Run all sensitivity perturbation tests as specified in [SPEC §5.3].

    Perturbation set [SPEC §5.3]:
        1. θv + ANGLE_PERTURBATION_DEG  (upward angle jitter)
        2. θv − ANGLE_PERTURBATION_DEG  (downward angle jitter)
        3. θh + ANGLE_PERTURBATION_DEG  (rightward angle jitter)
        4. θh − ANGLE_PERTURBATION_DEG  (leftward angle jitter)
        5. v0 + V0_PERTURBATION_MS      (faster kick)
        6. v0 − V0_PERTURBATION_MS      (slower kick)

    Robustness criterion [SPEC §5.3]:
        "If the zone prediction remains correct under these perturbations,
         the system is considered robust enough."
        → We require ≥ 4/6 tests to pass (allow 2 boundary cases to fail).

    Parameters
    ----------
    (same as run_sensitivity_perturbation)

    Returns
    -------
    results : list of SensitivityResult
    robust : bool — True if ≥ 4/6 perturbation tests verify correct zone
    """
    delta_angle = np.radians(ANGLE_PERTURBATION_DEG)
    delta_v0    = V0_PERTURBATION_MS

    perturbations = [
        ("ANGLE_V", +delta_angle),
        ("ANGLE_V", -delta_angle),
        ("ANGLE_H", +delta_angle),
        ("ANGLE_H", -delta_angle),
        ("SPEED",   +delta_v0),
        ("SPEED",   -delta_v0),
    ]

    results: list[SensitivityResult] = []
    n_passed = 0

    for ptype, pvalue in perturbations:
        result = run_sensitivity_perturbation(
            v0_ms, theta_v_rad, theta_h_rad,
            target_zone_id, ptype, pvalue
        )
        results.append(result)
        if result.verification_passed:
            n_passed += 1

        logger.debug(
            f"Sensitivity [{ptype} {'+' if pvalue>=0 else ''}"
            f"{np.degrees(pvalue):.2f}{'°' if ptype != 'SPEED' else 'm/s'}]: "
            f"hit={result.zone_hit}, passed={result.verification_passed}"
        )

    # Robustness criterion: ≥ 4 of 6 must pass [SPEC §5.3]
    ROBUSTNESS_THRESHOLD = 4
    robust = (n_passed >= ROBUSTNESS_THRESHOLD)

    logger.info(
        f"Sensitivity suite: {n_passed}/6 tests passed. "
        f"Robust: {robust}. Threshold: {ROBUSTNESS_THRESHOLD}/6."
    )

    return results, robust


# ─── Master Entry Point ───────────────────────────────────────────────────────

def run_digital_twin(
    v0_ms: float,
    theta_v_rad: float,
    theta_h_rad: float,
    target_zone_id: str
) -> DigitalTwinResult:
    """
    Orchestrate the full digital twin verification pipeline.

    Pipeline [SPEC §5.2]:
        1. Forward-simulate nominal trajectory.
        2. Interpolate ball position at goal line.
        3. Verify zone hit.
        4. Run sensitivity perturbation suite [SPEC §5.3].
        5. Assess overall robustness.

    Parameters
    ----------
    v0_ms : float — ball launch speed from physics engine [m/s]
    theta_v_rad : float — vertical launch angle [radians]
    theta_h_rad : float — horizontal deflection angle [radians]
    target_zone_id : str — selected goal zone

    Returns
    -------
    DigitalTwinResult — complete verification output
    """
    warnings: list[str] = []

    logger.info(
        f"Digital twin: zone={target_zone_id}, v0={v0_ms:.3f}m/s, "
        f"θv={np.degrees(theta_v_rad):.3f}°, θh={np.degrees(theta_h_rad):.3f}°"
    )

    # ── Step 1: Forward trajectory simulation ────────────────────────────────
    trajectory = simulate_trajectory(v0_ms, theta_v_rad, theta_h_rad)

    # ── Step 2: Interpolate position at goal line ─────────────────────────────
    try:
        y_goal, z_goal = interpolate_position_at_goal_line(trajectory)
    except ValueError as e:
        warnings.append(str(e))
        # Return failed result — ball didn't reach goal line
        failed_result = ZoneHitResult(
            zone_id=target_zone_id, hit_zone="MISS_NO_REACH",
            verification_passed=False,
            y_at_goal_m=0.0, z_at_goal_m=0.0,
            y_error_m=float("inf"), z_error_m=float("inf"),
            y_target_m=GOAL_ZONES[target_zone_id]["y_m"],
            z_target_m=GOAL_ZONES[target_zone_id]["x_m"],
            y_zone_min_m=0.0, y_zone_max_m=0.0,
            z_zone_min_m=0.0, z_zone_max_m=0.0,
            crossbar_clearance_m=float("inf"),
            above_ground=False
        )
        return DigitalTwinResult(
            nominal=failed_result, trajectory=trajectory,
            sensitivity_results=[], robust_under_perturbation=False,
            overall_verified=False, warnings=warnings
        )

    # ── Step 3: Zone hit verification ────────────────────────────────────────
    nominal = check_zone_hit(target_zone_id, y_goal, z_goal)

    if not nominal.verification_passed:
        warnings.append(
            f"Digital twin: Ball predicted to land in zone '{nominal.hit_zone}' "
            f"rather than target zone '{target_zone_id}'. "
            f"Error: Δy={nominal.y_error_m:.3f}m, Δz={nominal.z_error_m:.3f}m. "
            f"This may indicate IK convergence issues or ROM boundary clipping."
        )

    if not nominal.above_ground:
        warnings.append(
            f"Digital twin: Ball predicted below ground at goal line "
            f"(y={nominal.y_at_goal_m:.3f}m). Check v0 estimation."
        )

    if nominal.crossbar_clearance_m < CROSSBAR_SAFETY_MARGIN_M:
        warnings.append(
            f"Digital twin: Insufficient crossbar clearance "
            f"({nominal.crossbar_clearance_m:.3f}m < {CROSSBAR_SAFETY_MARGIN_M}m). "
            f"[SPEC §2.8] Aerodynamic drag may cause ball to clip the crossbar."
        )

    # ── Step 4: Sensitivity perturbation suite ────────────────────────────────
    sensitivity_results, robust = run_full_sensitivity_suite(
        v0_ms, theta_v_rad, theta_h_rad, target_zone_id
    )

    if not robust:
        warnings.append(
            f"Digital twin: Sensitivity analysis shows <4/6 perturbation "
            f"tests pass. The computed trajectory is sensitive to small "
            f"errors in angle estimation (±{ANGLE_PERTURBATION_DEG}°) or "
            f"speed estimation (±{V0_PERTURBATION_MS}m/s). "
            f"Consider targeting a zone with more clearance from boundaries."
        )

    # ── Step 5: Overall verification ─────────────────────────────────────────
    overall_verified = nominal.verification_passed and robust

    return DigitalTwinResult(
        nominal=nominal,
        trajectory=trajectory,
        sensitivity_results=sensitivity_results,
        robust_under_perturbation=robust,
        overall_verified=overall_verified,
        warnings=warnings
    )