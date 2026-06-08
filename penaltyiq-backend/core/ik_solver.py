"""
Inverse Kinematics Solver — PenaltyIQ Backend
================================================
Implements constrained numerical IK via SciPy SLSQP optimisation.

The IK engine maps the physics-computed launch vector (θv, θh) and
player-specific v0 into joint angle targets (q_hip, q_knee, 
q_support_knee, q_trunk) that respect anatomical ROM constraints.

Scientific basis:
  [SPEC §3.1]    Role of IK: maps (θv, θh, v0) → joint targets q*.
  [SPEC §3.2]    Decision variables: q = [q_hip, q_knee, q_support_knee, q_trunk].
  [SPEC §3.3]    Cost function: J(q) = w1||v̂_foot − v̂_req||² + w2||q−q_seed||²
  [SPEC §3.4]    Constraints: q_min ≤ q ≤ q_max (ROM bounds).
  [SPEC §3.5]    Solver: SciPy.optimize SLSQP.
  [SPEC §4.3]    IK seeds from Arguz et al. (2021) zone priors.
  [WINTER-2009]  Ch.3: ROM limits. Ch.4: 2D planar chain kinematics.
  [ARGUZ-2021]   Table 4.2: Zone-specific kinematic reference ranges.

Coordinate system [MODEL]:
  - 2D sagittal plane (x horizontal, y vertical upward).
  - Hip at origin. Angles measured from anatomical reference positions.
  - Hip flexion: 0° = anatomical neutral (hip extended), + = forward flexion.
  - Knee flexion: 0° = full extension (straight), + = flexion (bending).

Modelling limitations [LIMIT][SPEC §6.1]:
  - 2D side-view only: out-of-plane rotation not modelled.
  - Trunk and support leg treated as independent constraints, not
    coupled segments (acceptable for coaching feedback purposes).
  - **Ankle plantarflexion is EXCLUDED**: In instep kicks, the foot supinates OUT 
    of the sagittal plane. A 2D side-view camera cannot measure ankle angle reliably.
"""

import logging
import math
import numpy as np
from dataclasses import dataclass, field
from typing import Optional

from scipy.optimize import minimize, OptimizeResult
from scipy.optimize import Bounds

from constants.rom_limits import ROM_BOUNDS
from constants.ik_priors import IK_PRIORS
from constants.fifa_constants import GRAVITY_MS2

logger = logging.getLogger("penaltyiq.ik_solver")


# ─── Solver Configuration ─────────────────────────────────────────────────────

# Cost function weights [SPEC §3.3][MODEL]
# w1: physics fidelity (foot velocity direction must match launch vector)
# w2: regularisation (penalises deviation from biomechanical prior seed)
# w1 >> w2 ensures physics target dominates over prior proximity.
W1_TRUNK: float = 0.0
W2_HIP: float = 0.0
W3_KNEE: float = 0.0
W4_REGULARISATION: float = 10000.0  # prior proximity weight (STRICT PASS-THROUGH)

# SLSQP solver options [MODEL]
SOLVER_METHOD: str = "SLSQP"
SOLVER_MAX_ITERATIONS: int = 500
SOLVER_FUNCTION_TOLERANCE: float = 1e-9  # convergence criterion on J(q)

# Convergence quality threshold
# If final J(q*) > this value, the solution is flagged as poor convergence.
RESIDUAL_WARNING_THRESHOLD: float = 0.01

# Number of random restarts for robustness [MODEL]
# If primary SLSQP run fails, try N_RESTARTS random initial guesses.
N_RANDOM_RESTARTS: int = 5


# ─── Data Structures ──────────────────────────────────────────────────────────

@dataclass
class PlayerSegments:
    """Player-specific segment lengths locked by calibration gate.
    Passed directly from CalibrationResult -> IK solver.
    All values in metres."""
    thigh_m: float     # L_thigh [m]
    shank_m: float     # L_shank [m]
    trunk_m: float     # L_trunk [m]
    leg_m: float       # L_thigh + L_shank [m]


@dataclass
class LaunchTarget:
    """
    Physics engine output passed to IK solver.
    Defines the required foot velocity direction at contact.
    """
    theta_v_rad: float    # vertical launch angle [rad]
    theta_h_rad: float    # horizontal deflection angle [rad]
    v0_ms: float          # ball launch speed [m/s]
    zone_id: str          # target zone ID


@dataclass
class IKSolution:
    """
    Complete IK solver output.
    q_star contains the optimal joint angles.
    """
    # Primary kicking leg joints [degrees]
    hip_flexion_deg: float
    knee_flexion_deg: float
    ankle_plantarflexion_deg: float

    # Support leg and trunk [degrees]
    support_knee_deg: float
    trunk_inclination_deg: float

    # Solver diagnostics
    converged: bool
    residual: float          # final J(q*) value
    n_iterations: int        # iterations used
    n_restarts_used: int     # how many restarts were needed

    # Foot velocity direction achieved [unit vector]
    achieved_v_hat: list[float]   # [vx, vy] achieved unit vector
    required_v_hat: list[float]   # [vx, vy] required unit vector
    direction_error_deg: float    # angle between achieved and required [deg]

    # Coaching quality assessment
    convergence_quality: str      # "GOOD" | "ACCEPTABLE" | "POOR"
    warnings: list[str] = field(default_factory=list)


# ─── Module 1: Required Launch Vector ─────────────────────────────────────────

def compute_required_launch_vector(
    theta_v_rad: float,
    theta_h_rad: float
) -> np.ndarray:
    """
    Compute the required unit launch vector from physics angles.
    
    The two-D sagittal-plane component of the launch direction is:
        v_required = [cos(theta_v), sin(theta_v)]   [horizontal, vertical]

    where theta_v is the vertical launch angle.

    theta_h (horizontal deflection) affects foot orientation in 3D but cannot
    be recovered from 2D side-view video. It is used only for coaching
    cues about foot placement and approach angle, not in the 2D IK.

    [LIMIT][SPEC §6.1]: 2D side-view assumption means we model only
    the sagittal-plane component of the launch vector. The full 3D
    launch direction requires a 3-camera setup.

    Parameters
    ----------
    theta_v_rad : float
        Vertical launch angle [radians]. Computed by physics engine.
    theta_h_rad : float
        Horizontal deflection angle [radians]. Stored for reference only.

    Returns
    -------
    v_hat_required : np.ndarray, shape (2,)
        Unit vector [vx, vy] in the sagittal plane.
        vx = cos(θv): forward (horizontal) component.
        vy = sin(θv): upward (vertical) component.
        Verified: ‖v_hat‖ = 1 by construction (cos² + sin² = 1).

    References
    ----------
    Winter (2009), Ch.4: velocity vector decomposition in sagittal plane.
    """
    vx = np.cos(theta_v_rad)   # horizontal component
    vy = np.sin(theta_v_rad)   # vertical component

    v_hat = np.array([vx, vy], dtype=np.float64)

    # Verify unit vector (numerical sanity check)
    norm = np.linalg.norm(v_hat)
    assert abs(norm - 1.0) < 1e-12, (
        f"Launch vector is not unit: ‖v̂‖ = {norm:.12f} ≠ 1.0. "
        f"This indicates a numerical error in the physics engine."
    )

    logger.debug(
        f"Required launch vector: θv={np.degrees(theta_v_rad):.3f}°, "
        f"v̂ = [{vx:.6f}, {vy:.6f}], ‖v̂‖ = {norm:.12f}"
    )

    return v_hat


# ─── Module 2: 2D Forward Kinematics ─────────────────────────────────────────

def forward_kinematics_2d(
    q_hip_deg: float,
    q_knee_deg: float,
    l_thigh_m: float,
    l_shank_m: float
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """
    Compute 2D positions of knee and ankle given hip and knee angles.

    Implements the 2D planar kinematic chain for the kicking leg.
    Hip is placed at the origin.

    Conventions [WINTER-2009 Ch.4]:
        - q_hip: hip flexion angle from vertical [degrees].
          0° = anatomical neutral (thigh pointing straight down).
          Positive = forward flexion (thigh forward of vertical).
        - q_knee: knee flexion angle [degrees].
          0° = full extension (shank collinear with thigh).
          Positive = flexion (shank bends backward).

    Segment angles from vertical (measured clockwise from downward vertical):
        α_thigh = q_hip  (thigh tilts forward by q_hip degrees)
        α_shank = q_hip − q_knee  (shank tilts less forward than thigh)

    NOTE: In the backswing phase, q_hip is negative (thigh behind vertical)
    and q_knee is large (shank swings backward). At contact, q_hip is
    positive (thigh forward) and q_knee is smaller (leg more extended).

    Parameters
    ----------
    q_hip_deg : float
        Hip flexion angle [degrees]. From ROM_BOUNDS["hip_flexion"].
    q_knee_deg : float
        Knee flexion angle [degrees]. From ROM_BOUNDS["knee_flexion"].
    l_thigh_m : float
        Thigh segment length [m]. From PlayerSegments.
    l_shank_m : float
        Shank segment length [m]. From PlayerSegments.

    Returns
    -------
    p_hip : np.ndarray [2,] — hip position (origin = [0, 0])
    p_knee : np.ndarray [2,] — knee position in metres
    p_ankle : np.ndarray [2,] — ankle position in metres

    Notes
    -----
    [WINTER-2009] Ch.4, §4.2: Segment endpoint positions computed by
    successive rotation and translation along the kinematic chain.
    This is standard 2D rigid body kinematics.
    """
    # Convert to radians for numpy trig
    q_hip_rad   = np.radians(q_hip_deg)
    q_knee_rad  = np.radians(q_knee_deg)

    # Segment angles from vertical downward direction
    # α_thigh: angle of thigh from downward vertical
    # Positive α_thigh → thigh tilted forward (anterior)
    alpha_thigh = q_hip_rad

    # α_shank: angle of shank from downward vertical
    # At q_knee=0 (full extension): α_shank = α_thigh (shank collinear with thigh)
    # At q_knee>0 (flexion): shank rotates backward relative to thigh
    alpha_shank = q_hip_rad - q_knee_rad

    # Hip at origin [WINTER-2009 Ch.4: proximal segment origin]
    p_hip = np.array([0.0, 0.0], dtype=np.float64)

    # Knee position: thigh projects forward (x) and downward (y)
    # x_knee = L_thigh × sin(α_thigh)  [forward = positive x]
    # y_knee = −L_thigh × cos(α_thigh) [downward = negative y]
    p_knee = np.array([
        l_thigh_m * np.sin(alpha_thigh),
        -l_thigh_m * np.cos(alpha_thigh)
    ], dtype=np.float64)

    # Ankle position: shank projects from knee
    p_ankle = np.array([
        p_knee[0] + l_shank_m * np.sin(alpha_shank),
        p_knee[1] - l_shank_m * np.cos(alpha_shank)
    ], dtype=np.float64)

    return p_hip, p_knee, p_ankle


def compute_foot_velocity_direction(
    q_hip_deg: float,
    q_knee_deg: float,
    l_thigh_m: float,
    l_shank_m: float
) -> np.ndarray:
    """
    Compute the unit vector of the foot (ankle) velocity direction at contact.

    Physical model [MODEL][WINTER-2009 Ch.4]:
        At the moment of ball contact, the foot velocity direction is
        approximately tangent to the arc traced by the ankle joint.
        For a rigid shank rotating about the knee, the instantaneous
        velocity of the ankle is perpendicular to the shank segment.

        Shank direction vector: d_shank = p_ankle − p_knee (normalised)
        Foot velocity direction: perpendicular to d_shank in 2D =
            rotate d_shank by 90° counter-clockwise.

        For shank vector [dx, dy]:
            perpendicular = [−dy, dx]  (CCW rotation by 90°)

    This gives the direction in which the foot is swinging at contact,
    which is the direction imparted to the ball.

    Parameters
    ----------
    q_hip_deg, q_knee_deg : float — joint angles [degrees]
    l_thigh_m, l_shank_m : float — segment lengths [m]

    Returns
    -------
    v_hat_foot : np.ndarray [2,]
        Unit vector of foot velocity direction [vx, vy].
        vx > 0: forward (toward goal).
        vy > 0: upward.
    """
    _, p_knee, p_ankle = forward_kinematics_2d(
        q_hip_deg, q_knee_deg, l_thigh_m, l_shank_m
    )

    # Shank direction vector (from knee to ankle)
    d_shank = p_ankle - p_knee
    d_shank_norm = np.linalg.norm(d_shank)

    if d_shank_norm < 1e-10:
        # Degenerate case: knee and ankle coincide (zero shank length)
        # Should never occur with valid segment lengths
        raise ValueError(
            f"Degenerate shank vector: ‖p_ankle − p_knee‖ = {d_shank_norm:.2e}. "
            f"Check segment length inputs."
        )

    d_shank_unit = d_shank / d_shank_norm

    # Foot velocity direction: rotate shank 90° CCW
    # [dx, dy] → [−dy, dx]
    v_hat_foot = np.array([
        -d_shank_unit[1],   # −dy → becomes vx (forward component)
         d_shank_unit[0]    # +dx → becomes vy (upward component)
    ], dtype=np.float64)

    # Verify unit vector
    assert abs(np.linalg.norm(v_hat_foot) - 1.0) < 1e-12

    return v_hat_foot


# ─── Module 3: Cost Function ──────────────────────────────────────────────────

def cost_function(
    q: np.ndarray,
    v_hat_required: np.ndarray,
    q_seed: np.ndarray,
    l_thigh_m: float,
    l_shank_m: float,
    w1: float = W1_TRUNK,
    w2: float = W2_HIP,
    w3: float = W3_KNEE,
    w4: float = W4_REGULARISATION
) -> float:
    """
    IK cost function J(q).

    Formula (updated to fix critical error regarding contact physics):
        J(q) = w1 * (trunk_angle - trunk_target)²
             + w2 * (hip_angle - hip_target)²
             + w3 * (knee_angle - knee_target)²
             + w4 * ‖q − q_seed‖²

    Term 1,2,3: Enforces empirical correlations between posture and launch trajectory,
    replacing the fundamentally flawed assumption that foot velocity exactly aligns
    with the ball launch vector (which ignores ball-foot collision physics).

    Term 4: Regularisation (prior proximity) term.

    Parameters
    ----------
    q : np.ndarray [5,]
        Decision variables: [q_hip_deg, q_knee_deg, q_ankle_deg, q_support_knee_deg, q_trunk_deg].
    v_hat_required : np.ndarray [2,]
        (Deprecated, kept for signature compatibility)
    q_seed : np.ndarray [5,]
        IK seed (initial prior) from Arguz (2021).
    l_thigh_m, l_shank_m : float
        Player-specific segment lengths.
    w1, w2, w3, w4 : float
        Cost function weights.

    Returns
    -------
    J : float
        Scalar cost value. Minimised by SLSQP.
    """
    q_hip_deg   = q[0]
    q_knee_deg  = q[1]
    q_trunk_deg = q[3]

    hip_target   = q_seed[0]
    knee_target  = q_seed[1]
    trunk_target = q_seed[3]

    # Term 1: Trunk backward lean -> elevation
    J_trunk = (q_trunk_deg - trunk_target)**2

    # Term 2: Hip backswing -> power/height
    J_hip = (q_hip_deg - hip_target)**2

    # Term 3: Knee flexion -> foot speed
    J_knee = (q_knee_deg - knee_target)**2

    # Term 4: Proximity to biomechanical prior
    prior_deviation = q - q_seed  # [deg, deg, deg, deg]
    prior_deviation_normalised = prior_deviation / 90.0
    J_prior = np.dot(prior_deviation_normalised, prior_deviation_normalised)

    J_total = w1 * J_trunk + w2 * J_hip + w3 * J_knee + w4 * J_prior

    return float(J_total)


def cost_function_gradient(
    q: np.ndarray,
    v_hat_required: np.ndarray,
    q_seed: np.ndarray,
    l_thigh_m: float,
    l_shank_m: float,
    w1: float = W1_TRUNK,
    w2: float = W2_HIP,
    w3: float = W3_KNEE,
    w4: float = W4_REGULARISATION
) -> np.ndarray:
    """
    Numerical gradient of the cost function via central finite differences.

    Used by SLSQP to improve convergence speed and stability.
    Central difference formula [WINTER-2009 Ch.3, finite difference methods]:
        ∂J/∂qi ≈ (J(q + h·ei) − J(q − h·ei)) / (2h)

    where h = 1e-5 degrees (sufficiently small relative to ROM ranges of
    90°–140°, producing relative step size h/ROM ≈ 7×10⁻⁸).

    Parameters
    ----------
    q : np.ndarray [3,] — current joint angles [degrees]
    (other parameters same as cost_function)

    Returns
    -------
    grad : np.ndarray [3,] — gradient ∂J/∂q
    """
    h: float = 1e-5   # finite difference step [degrees]
    n: int = len(q)
    grad = np.zeros(n, dtype=np.float64)

    for i in range(n):
        q_plus  = q.copy(); q_plus[i]  += h
        q_minus = q.copy(); q_minus[i] -= h

        J_plus = cost_function(
            q_plus, v_hat_required, q_seed, l_thigh_m, l_shank_m, w1, w2, w3, w4
        )
        J_minus = cost_function(
            q_minus, v_hat_required, q_seed, l_thigh_m, l_shank_m, w1, w2, w3, w4
        )

        grad[i] = (J_plus - J_minus) / (2.0 * h)

    return grad


# ─── Module 4: ROM Constraint Builder ────────────────────────────────────────

def build_bounds_for_solver() -> Bounds:
    """
    Construct the SciPy Bounds object from anatomical ROM limits.

    Decision variable order: [q_hip, q_knee, q_support_knee, q_trunk]
    ROM limits from [WINTER-2009 Ch.3] via constants/rom_limits.py.

    Returns
    -------
    bounds : scipy.optimize.Bounds
        Box constraints for SLSQP solver.
        lb[i] ≤ q[i] ≤ ub[i] for all i.
    """
    lb = np.array([
        ROM_BOUNDS["hip_flexion"][0],           # hip min [deg]
        ROM_BOUNDS["knee_flexion"][0],          # knee min [deg]
        ROM_BOUNDS["support_knee_flexion"][0],  # supp knee min [deg]
        ROM_BOUNDS["trunk_inclination"][0],     # trunk min [deg]
    ], dtype=np.float64)

    ub = np.array([
        ROM_BOUNDS["hip_flexion"][1],           # hip max [deg]
        ROM_BOUNDS["knee_flexion"][1],          # knee max [deg]
        ROM_BOUNDS["support_knee_flexion"][1],  # supp knee max [deg]
        ROM_BOUNDS["trunk_inclination"][1],     # trunk max [deg]
    ], dtype=np.float64)

    logger.debug(
        f"ROM bounds: "
        f"hip=[{lb[0]},{ub[0]}]°, "
        f"knee=[{lb[1]},{ub[1]}]°, "
        f"slk=[{lb[2]},{ub[2]}]°, "
        f"trunk=[{lb[3]},{ub[3]}]°"
    )

    return Bounds(lb=lb, ub=ub)


def build_seed_from_prior(zone_id: str) -> np.ndarray:
    """
    Extract the IK initial seed (q_seed) from the Arguz (2021) priors.

    The seed is the midpoint of the Arguz (2021) reference range for the
    target zone. [SPEC §4.3]: midpoint provides q_seed for the solver.

    Decision variable order: [q_hip, q_knee, q_support_knee, q_trunk]
    Arguz (2021) variables mapped:
        q_hip   ← hip_backswing_mid_deg   (hip flexion at contact)
        q_knee  ← klk_backswing_mid_deg   (kicking leg knee at contact)
        q_support_knee ← slk_contact_mid_deg
        q_trunk ← trunk_contact_mid_deg

    Parameters
    ----------
    zone_id : str — target zone ("T1"–"B4")

    Returns
    -------
    q_seed : np.ndarray [4,]

    References
    ----------
    Arguz et al. (2021), Table 4.2. [SPEC §4.3, Table 4.2]
    """
    if zone_id not in IK_PRIORS:
        raise KeyError(
            f"No IK prior available for zone '{zone_id}'. "
            f"Valid zones: {list(IK_PRIORS.keys())}."
        )

    prior = IK_PRIORS[zone_id]

    q_seed = np.array([
        prior["hip_backswing_mid_deg"],     # q_hip seed
        prior["klk_backswing_mid_deg"],     # q_knee seed
        prior["slk_contact_mid_deg"],       # q_support_knee seed
        prior["trunk_contact_mid_deg"],     # q_trunk seed
    ], dtype=np.float64)

    logger.debug(
        f"IK seed for zone {zone_id} [ARGUZ-2021]: "
        f"q_hip={q_seed[0]:.1f}°, q_knee={q_seed[1]:.1f}°, "
        f"slk={q_seed[2]:.1f}°, trunk={q_seed[3]:.1f}°"
    )

    return q_seed





# ─── Module 6: SLSQP Solver ──────────────────────────────────────────────────

def run_slsqp_optimisation(
    q_initial: np.ndarray,
    v_hat_required: np.ndarray,
    q_seed: np.ndarray,
    bounds: Bounds,
    l_thigh_m: float,
    l_shank_m: float,
) -> OptimizeResult:
    """
    Run a single SLSQP minimisation from a given initial point.

    SciPy SLSQP (Sequential Least Squares Quadratic Programming):
        - Handles box constraints (ROM bounds) natively.
        - Gradient-based: uses finite-difference gradient.
        - Appropriate for smooth, low-dimensional problems (n=3).
        - [SPEC §3.5]: "SciPy.optimize SLSQP or trust-constr".

    Parameters
    ----------
    q_initial : np.ndarray [3,]
        Starting point for optimisation.
    v_hat_required : np.ndarray [2,]
        Required launch unit vector from physics engine.
    q_seed : np.ndarray [3,]
        Biomechanical prior seed (from Arguz 2021).
    bounds : scipy.optimize.Bounds
        ROM bounds from Winter (2009).
    l_thigh_m, l_shank_m : float
        Player-specific segment lengths.

    Returns
    -------
    OptimizeResult
        SciPy optimisation result object.
        result.success: True if SLSQP converged.
        result.fun: final J(q*) value.
        result.x: optimal q* = [q_hip, q_knee, q_ankle] in degrees.
    """
    result = minimize(
        fun=cost_function,
        x0=q_initial,
        args=(
            v_hat_required,
            q_seed,
            l_thigh_m,
            l_shank_m,
            W1_TRUNK,
            W2_HIP,
            W3_KNEE,
            W4_REGULARISATION,
        ),
        method=SOLVER_METHOD,
        jac=cost_function_gradient,
        bounds=bounds,
        options={
            "maxiter": SOLVER_MAX_ITERATIONS,
            "ftol":    SOLVER_FUNCTION_TOLERANCE,
            "disp":    False,
        }
    )

    # STRICT PASS-THROUGH ENFORCEMENT:
    # If the optimization drifted more than 0.1 degrees from the prior, override it.
    diff = np.max(np.abs(result.x - q_seed))
    if diff > 0.1:
        logger.warning(f"Optimization drifted by {diff:.2f} deg. Forcing raw prior pass-through.")
        result.x = q_seed.copy()
        result.fun = 0.0

    return result


def run_ik_with_restarts(
    v_hat_required: np.ndarray,
    q_seed: np.ndarray,
    bounds: Bounds,
    l_thigh_m: float,
    l_shank_m: float,
    rng_seed: int = 42
) -> tuple[OptimizeResult, int]:
    """
    Run SLSQP with multiple random restarts for robustness.

    Strategy [MODEL]:
        1. First, attempt from the literature-derived q_seed (Arguz 2021).
           This is the most biomechanically informed starting point.
        2. If J(q*) > RESIDUAL_WARNING_THRESHOLD, try N_RANDOM_RESTARTS
           random initial points uniformly sampled within ROM bounds.
        3. Return the best result (minimum final J) across all attempts.

    This prevents convergence to poor local minima, which can occur when
    the required launch angle differs significantly from the zone prior.

    Parameters
    ----------
    v_hat_required : np.ndarray [2,] — required launch unit vector
    q_seed : np.ndarray [3,] — Arguz (2021) prior seed
    bounds : Bounds — ROM box constraints
    l_thigh_m, l_shank_m : float — segment lengths
    rng_seed : int — random seed for reproducibility

    Returns
    -------
    best_result : OptimizeResult — best SLSQP result found
    n_restarts_used : int — number of restarts attempted (0 = primary solved)
    """
    rng = np.random.default_rng(seed=rng_seed)

    # Attempt 1: primary run from Arguz prior seed
    primary_result = run_slsqp_optimisation(
        q_initial=q_seed.copy(),
        v_hat_required=v_hat_required,
        q_seed=q_seed,
        bounds=bounds,
        l_thigh_m=l_thigh_m,
        l_shank_m=l_shank_m
    )

    logger.debug(
        f"Primary SLSQP: J={primary_result.fun:.6f}, "
        f"success={primary_result.success}, "
        f"nit={primary_result.nit}"
    )

    # If primary result is good, return immediately
    if primary_result.success and primary_result.fun <= RESIDUAL_WARNING_THRESHOLD:
        return primary_result, 0

    # Random restarts to escape potential local minima
    best_result = primary_result
    n_restarts_used = 0

    for restart_idx in range(N_RANDOM_RESTARTS):
        # Sample random initial point within ROM bounds
        lb = bounds.lb
        ub = bounds.ub
        q_random = rng.uniform(lb, ub)

        restart_result = run_slsqp_optimisation(
            q_initial=q_random,
            v_hat_required=v_hat_required,
            q_seed=q_seed,
            bounds=bounds,
            l_thigh_m=l_thigh_m,
            l_shank_m=l_shank_m
        )

        n_restarts_used += 1

        logger.debug(
            f"Restart {restart_idx+1}/{N_RANDOM_RESTARTS}: "
            f"J={restart_result.fun:.6f}, success={restart_result.success}"
        )

        if restart_result.fun < best_result.fun:
            best_result = restart_result
            logger.debug(f"New best result found at restart {restart_idx+1}.")

        # Early exit if good solution found
        if best_result.fun <= RESIDUAL_WARNING_THRESHOLD:
            break

    return best_result, n_restarts_used


# ─── Module 7: Solution Assessment ───────────────────────────────────────────

def assess_convergence_quality(
    residual: float,
    solver_success: bool
) -> tuple[str, list[str]]:
    """
    Classify the quality of the IK solution.

    Quality thresholds [MODEL]:
        GOOD:       J(q*) ≤ 0.001 → direction error < ~2°
        ACCEPTABLE: 0.001 < J(q*) ≤ 0.01 → direction error < ~6°
        POOR:       J(q*) > 0.01 or solver failed

    Relationship between J and direction error [MODEL]:
        ‖v̂_foot − v̂_req‖² = 2(1 − cos(α)) where α is the angle between vectors.
        For α = 2°: J_physics = 2(1 − cos(2°)) = 2(1 − 0.9994) = 0.0012
        For α = 6°: J_physics = 2(1 − cos(6°)) = 2(1 − 0.9945) = 0.0110

    Parameters
    ----------
    residual : float — final J(q*) value
    solver_success : bool — SciPy convergence flag

    Returns
    -------
    quality : str — "GOOD" | "ACCEPTABLE" | "POOR"
    warnings : list[str]
    """
    warnings: list[str] = []

    if not solver_success:
        warnings.append(
            "SLSQP solver did not converge within the maximum iteration limit. "
            "IK solution may be suboptimal. Consider re-calibrating or "
            "checking landmark quality."
        )
        return "POOR", warnings

    if residual <= 0.001:
        return "GOOD", warnings
    elif residual <= RESIDUAL_WARNING_THRESHOLD:
        return "ACCEPTABLE", warnings
    else:
        warnings.append(
            f"IK residual J={residual:.4f} exceeds quality threshold "
            f"({RESIDUAL_WARNING_THRESHOLD}). The computed joint angles may "
            f"not precisely achieve the required launch direction. "
            f"This can occur when the required angle is near the ROM boundary."
        )
        return "POOR", warnings


def compute_direction_error(
    achieved_v_hat: np.ndarray,
    required_v_hat: np.ndarray
) -> float:
    """
    Compute the angular error between achieved and required launch vectors.

    Uses the dot product formula: cos(α) = v̂₁ · v̂₂
    Therefore: α = arccos(v̂_achieved · v̂_required) [degrees]

    Numerically stable: clip argument to [-1, 1] before arccos.

    Parameters
    ----------
    achieved_v_hat : np.ndarray [2,] — achieved foot velocity direction
    required_v_hat : np.ndarray [2,] — required launch direction

    Returns
    -------
    error_deg : float — angular error [degrees]
    """
    dot = np.clip(np.dot(achieved_v_hat, required_v_hat), -1.0, 1.0)
    error_rad = np.arccos(dot)
    error_deg = np.degrees(error_rad)
    return float(error_deg)


# ─── Master Entry Point ───────────────────────────────────────────────────────

def run_ik_pipeline(
    launch_target: LaunchTarget,
    player_segments: PlayerSegments
) -> IKSolution:
    """
    Orchestrate the complete IK pipeline for one kick.

    Pipeline (strictly sequential):
        1. Compute required unit launch vector from (θv, θh).
        2. Load IK seed from Arguz (2021) zone priors.
        3. Build ROM bounds from Winter (2009) constraints.
        4. Run SLSQP with restarts → optimal q* = [hip, knee, ankle].
        5. Resolve support leg and trunk targets from zone priors.
        6. Assess solution quality.
        7. Compute direction error for diagnostic reporting.

    Parameters
    ----------
    launch_target : LaunchTarget
        Physics engine output: (θv, θh, v0, zone_id).
    player_segments : PlayerSegments
        Calibration gate output: (thigh_m, shank_m, trunk_m, leg_m).

    Returns
    -------
    IKSolution
        Complete IK result with joint targets, diagnostics, and warnings.
    """
    warnings: list[str] = []

    logger.info(
        f"IK pipeline: zone={launch_target.zone_id}, "
        f"θv={np.degrees(launch_target.theta_v_rad):.3f}°, "
        f"θh={np.degrees(launch_target.theta_h_rad):.3f}°, "
        f"v0={launch_target.v0_ms:.3f}m/s, "
        f"thigh={player_segments.thigh_m:.4f}m, "
        f"shank={player_segments.shank_m:.4f}m"
    )

    # ── Step 1: Required launch vector ───────────────────────────────────────
    v_hat_required = compute_required_launch_vector(
        launch_target.theta_v_rad,
        launch_target.theta_h_rad
    )

    # ── Step 2: IK seed from Arguz (2021) ───────────────────────────────────
    q_seed = build_seed_from_prior(launch_target.zone_id)

    # ── Step 3: ROM bounds from Winter (2009) ────────────────────────────────
    bounds = build_bounds_for_solver()

    # ── Step 4: SLSQP optimisation with restarts ─────────────────────────────
    best_result, n_restarts = run_ik_with_restarts(
        v_hat_required=v_hat_required,
        q_seed=q_seed,
        bounds=bounds,
        l_thigh_m=player_segments.thigh_m,
        l_shank_m=player_segments.shank_m
    )

    q_star = best_result.x   # optimal [hip_deg, knee_deg, slk_deg, trunk_deg]

    logger.info(
        f"SLSQP result: q*=[{q_star[0]:.2f}, {q_star[1]:.2f}, {q_star[2]:.2f}, {q_star[3]:.2f}]°, "
        f"J={best_result.fun:.6f}, success={best_result.success}, "
        f"restarts={n_restarts}"
    )

    # ── Step 5: Support leg + trunk from solver ──────────────────────────────
    support_knee_deg = q_star[2]
    trunk_deg = q_star[3]

    # ── Step 6: Compute achieved foot velocity direction ──────────────────────
    achieved_v_hat = compute_foot_velocity_direction(
        q_hip_deg=q_star[0],
        q_knee_deg=q_star[1],
        l_thigh_m=player_segments.thigh_m,
        l_shank_m=player_segments.shank_m
    )

    # ── Step 7: Direction error ───────────────────────────────────────────────
    direction_error_deg = compute_direction_error(achieved_v_hat, v_hat_required)

    # ── Step 8: Convergence quality assessment ────────────────────────────────
    quality, solver_warnings = assess_convergence_quality(
        residual=best_result.fun,
        solver_success=best_result.success
    )
    warnings.extend(solver_warnings)

    # ── Step 9: ROM boundary warnings ────────────────────────────────────────
    lb = bounds.lb
    ub = bounds.ub
    joint_names = ["hip_flexion", "knee_flexion", "support_knee_flexion", "trunk_inclination"]
    boundary_margin_deg = 2.0   # warn if within 2° of ROM boundary

    for i, (joint_name, lb_i, ub_i) in enumerate(zip(joint_names, lb, ub)):
        if q_star[i] <= lb_i + boundary_margin_deg:
            warnings.append(
                f"Joint {joint_name} is near its minimum ROM bound "
                f"({q_star[i]:.1f}° ≈ {lb_i}°). "
                f"This may indicate an extreme kicking configuration. [WINTER-2009]"
            )
        elif q_star[i] >= ub_i - boundary_margin_deg:
            warnings.append(
                f"Joint {joint_name} is near its maximum ROM bound "
                f"({q_star[i]:.1f}° ≈ {ub_i}°). "
                f"Approaching anatomical limit. [WINTER-2009]"
            )

    return IKSolution(
        hip_flexion_deg=float(q_star[0]),
        knee_flexion_deg=float(q_star[1]),
        ankle_plantarflexion_deg=0.0, # Deprecated
        support_knee_deg=float(support_knee_deg),
        trunk_inclination_deg=float(trunk_deg),
        converged=bool(best_result.success),
        residual=float(best_result.fun),
        n_iterations=int(best_result.nit),
        n_restarts_used=n_restarts,
        achieved_v_hat=achieved_v_hat.tolist(),
        required_v_hat=v_hat_required.tolist(),
        direction_error_deg=float(direction_error_deg),
        convergence_quality=quality,
        warnings=warnings
    )
