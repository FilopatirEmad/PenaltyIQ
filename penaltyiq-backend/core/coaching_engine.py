"""
Coaching Engine — PenaltyIQ Backend
======================================
Generates biomechanically grounded coaching feedback by comparing
measured joint angles against IK-computed player-specific targets.

Angle conventions (v2 — aligned with angle_calculator v2)
---------------------------------------------------------
hip_flexion        Included shoulder–hip–knee angle [°].
                   180° = full extension. Values ~100–180°.
hip target         Is NEGATIVE (backswing). δ = measured − target.
                   δ > 0: measured less extended than target → need more backswing.
                   δ < 0: measured more extended than target → backswing too large.

knee_flexion       Positive included angle [°]. 180° = straight.
                   δ > 0: knee more open (less flexed) than target.
                   δ < 0: knee more closed (more flexed) than target.

support_knee       Same included angle convention as knee_flexion.

trunk_inclination  Signed from upward vertical [°]. 0° = upright.
                   + = forward lean. − = backward lean.
                   δ > 0: trunk more upright / backward than target.
                   δ < 0: trunk leaning further forward than target.
"""

import logging
from dataclasses import dataclass
from typing import Optional

from constants.ik_priors import IK_PRIORS

logger = logging.getLogger("penaltyiq.coaching_engine")


# ─── Status Thresholds [MODEL] ────────────────────────────────────────────────

THRESHOLD_OPTIMAL_DEG:    float = 3.0
THRESHOLD_ACCEPTABLE_DEG: float = 8.0
THRESHOLD_NEEDS_WORK_DEG: float = 15.0
# > THRESHOLD_NEEDS_WORK_DEG → CRITICAL


# ─── Scoring Weights [MODEL] ──────────────────────────────────────────────────
# بيحدد تأثير كل variable على الـ score النهائي
# المجموع = 1.0 دايمًا
# ball_velocity بتأثر بس لو v0_ms > 0، غير كده بيتوزع وزنها على الباقي

VARIABLE_WEIGHTS: dict[str, float] = {
    "trunk_inclination": 0.30,   # PRIMARY predictor of ball elevation [ARGUZ-2021]
    "support_knee":      0.25,   # stability base — affects all other variables
    "hip_flexion":       0.20,   # main power source (backswing)
    "knee_flexion":      0.15,   # elastic energy storage (quadriceps)
    "ball_velocity":     0.10,   # physical output — low weight (technique focus)
}


# ─── Data Structures ──────────────────────────────────────────────────────────

@dataclass
class CoachingItem:
    """
    Coaching feedback for a single kinematic variable.
    All angles in degrees.
    """
    variable: str
    label: str                    # Human-readable variable name
    measured_deg: float
    target_deg: float
    target_range_min_deg: float
    target_range_max_deg: float
    delta_deg: float              # measured − target (signed)
    status: str                   # OPTIMAL | ACCEPTABLE | NEEDS_WORK | CRITICAL
    cue: str                      # Plain-English instruction
    source: str                   # Literature source for the target range


# ─── Coaching Cue Library ─────────────────────────────────────────────────────

# Each entry: (variable_key, label, cue_if_positive_delta, cue_if_negative_delta)
# Positive delta = measured > target (too much of this angle).
# Negative delta = measured < target (too little of this angle).

COACHING_CUES: dict[str, dict] = {
    "hip_flexion": {
        "label": "Hip Extension (Backswing)",
        # New signed convention: hip targets are NEGATIVE (extension = backswing).
        # δ > 0: measured is LESS extended (closer to 0°) than target → insufficient backswing.
        # δ < 0: measured is MORE extended (more negative) than target → backswing too large.
        "cue_positive": (
            "Your hip backswing is insufficient. Drive your kicking thigh "
            "further back during the wind-up to generate more foot speed "
            "at contact. [ARGUZ-2021]"
        ),
        "cue_negative": (
            "Your hip backswing is too large. Reduce the backward swing "
            "of your kicking leg to improve accuracy and control. "
            "A shorter backswing transfers power more efficiently. [ARGUZ-2021]"
        ),
        "cue_optimal": (
            "Hip backswing is within the optimal range for this zone. "
            "Maintain this wind-up length. [ARGUZ-2021]"
        ),
        "source": "Arguz et al. (2021), Table 4.2; [SPEC Table 4.2]"
    },
    "knee_flexion": {
        "label": "Kicking Leg Knee Flexion (Backswing)",
        "cue_positive": (
            "Kicking leg knee is over-flexed in the backswing. "
            "A more extended knee during wind-up can reduce foot speed. "
            "Allow the knee to flex naturally — do not force it beyond "
            "your natural range. [WINTER-2009]"
        ),
        "cue_negative": (
            "Kicking leg knee flexion is insufficient in the backswing. "
            "Allow your knee to bend more during wind-up — this stores "
            "elastic energy in the quadriceps, increasing foot speed "
            "at contact. [WINTER-2009]"
        ),
        "cue_optimal": (
            "Kicking leg knee flexion is optimal for this zone. "
            "The elastic energy storage in your quadriceps is well-positioned. [WINTER-2009]"
        ),
        "source": "Arguz et al. (2021), Table 4.2; Winter (2009), Ch.3"
    },
    "support_knee": {
        "label": "Support Leg Knee Angle at Contact",
        "cue_positive": (
            "Support leg is too straight (over-extended) at contact. "
            "Bend your plant leg slightly more to lower your centre of mass, "
            "improving stability and enabling better trunk positioning "
            "for this zone. [ARGUZ-2021]"
        ),
        "cue_negative": (
            "Support leg is too bent (over-flexed) at contact. "
            "A more extended plant leg provides a stable base of support. "
            "Avoid excessive crouch — it reduces kicking power. [ARGUZ-2021]"
        ),
        "cue_optimal": (
            "Support leg angle at contact is optimal. "
            "Your base of support provides good stability for this zone. [ARGUZ-2021]"
        ),
        "source": "Arguz et al. (2021), Table 4.2"
    },
    "trunk_inclination": {
        "label": "Trunk Inclination at Contact",
        "cue_positive": (
            "Trunk is too upright (over-inclined) at contact for this zone. "
            "Lean your torso slightly more forward to lower the ball trajectory. "
            "Trunk inclination is the primary predictor of ball elevation. [ARGUZ-2021]"
        ),
        "cue_negative": (
            "Trunk is leaning too far forward at contact. "
            "A more upright posture at contact will increase ball elevation. "
            "Trunk inclination directly controls the vertical launch angle. [ARGUZ-2021]"
        ),
        "cue_optimal": (
            "Trunk inclination at contact is optimal for this zone. "
            "Your body lean is correctly positioned for the target height. [ARGUZ-2021]"
        ),
        "source": "Arguz et al. (2021), Table 4.2"
    },
}


# ─── Core Functions ───────────────────────────────────────────────────────────

def classify_status(delta_deg: float) -> str:
    """
    Classify the deviation magnitude into a coaching status.

    Status thresholds [MODEL]:
        OPTIMAL:    |δ| ≤ 3°
        ACCEPTABLE: 3° < |δ| ≤ 8°
        NEEDS_WORK: 8° < |δ| ≤ 15°
        CRITICAL:   |δ| > 15°
    """
    abs_delta = abs(delta_deg)
    if abs_delta <= THRESHOLD_OPTIMAL_DEG:
        return "OPTIMAL"
    elif abs_delta <= THRESHOLD_ACCEPTABLE_DEG:
        return "ACCEPTABLE"
    elif abs_delta <= THRESHOLD_NEEDS_WORK_DEG:
        return "NEEDS_WORK"
    else:
        return "CRITICAL"


def generate_coaching_item(
    variable_key: str,
    measured_deg: float,
    target_deg: float,
    target_range_min_deg: float,
    target_range_max_deg: float
) -> CoachingItem:
    """
    Generate a single coaching feedback item for one kinematic variable.

    Parameters
    ----------
    variable_key : str
        Key into COACHING_CUES dict (e.g., "hip_flexion").
    measured_deg : float
        Player's measured angle from pose estimation pipeline [degrees].
    target_deg : float
        Player-specific IK target angle [degrees].
    target_range_min_deg : float
        Lower bound of Arguz (2021) reference range [degrees].
    target_range_max_deg : float
        Upper bound of Arguz (2021) reference range [degrees].

    Returns
    -------
    CoachingItem
    """
    if variable_key not in COACHING_CUES:
        raise KeyError(
            f"No coaching cue defined for variable '{variable_key}'. "
            f"Available: {list(COACHING_CUES.keys())}."
        )

    cue_data = COACHING_CUES[variable_key]
    delta_deg = measured_deg - target_deg
    status = classify_status(delta_deg)

    # Select cue based on direction and severity
    if status == "OPTIMAL":
        cue = cue_data["cue_optimal"]
    elif delta_deg > 0:
        # Measured > target: too much of this angle
        if status == "CRITICAL":
            cue = (
                f"CRITICAL: {cue_data['cue_positive']} "
                f"(Deviation: +{delta_deg:.1f}°)"
            )
        else:
            cue = cue_data["cue_positive"]
    else:
        # Measured < target: too little of this angle
        if status == "CRITICAL":
            cue = (
                f"CRITICAL: {cue_data['cue_negative']} "
                f"(Deviation: {delta_deg:.1f}°)"
            )
        else:
            cue = cue_data["cue_negative"]

    return CoachingItem(
        variable=variable_key,
        label=cue_data["label"],
        measured_deg=round(measured_deg, 2),
        target_deg=round(target_deg, 2),
        target_range_min_deg=round(target_range_min_deg, 2),
        target_range_max_deg=round(target_range_max_deg, 2),
        delta_deg=round(delta_deg, 2),
        status=status,
        cue=cue,
        source=cue_data["source"]
    )


def generate_full_coaching_report(
    zone_id: str,
    measured_angles: dict[str, float],
    ik_targets: dict[str, float]
) -> list[CoachingItem]:
    """
    Generate coaching feedback for all tracked kinematic variables.

    Maps measured angles from the pose estimation pipeline against
    IK-computed player-specific targets and Arguz (2021) reference ranges.

    Parameters
    ----------
    zone_id : str
        Target goal zone ("T1"–"B4").
    measured_angles : dict
        {variable_key: measured_angle_deg} from joint angle extraction.
        Expected keys: "hip_flexion", "knee_flexion", "ankle_plantarflexion",
                       "support_knee", "trunk_inclination".
    ik_targets : dict
        {variable_key: target_angle_deg} from IK solver.
        Expected keys: same as measured_angles.

    Returns
    -------
    list of CoachingItem, ordered by severity (CRITICAL first).
    """
    prior = IK_PRIORS[zone_id]

    # Variable → (target_deg, range_min, range_max) mapping
    variable_mapping: dict[str, tuple[float, float, float]] = {
        "hip_flexion": (
            ik_targets.get("hip_flexion", prior["hip_backswing_mid_deg"]),
            prior["hip_range"][0],
            prior["hip_range"][1]
        ),
        "knee_flexion": (
            ik_targets.get("knee_flexion", prior["klk_backswing_mid_deg"]),
            prior["klk_range"][0],
            prior["klk_range"][1]
        ),
        "support_knee": (
            ik_targets.get("support_knee", prior["slk_contact_mid_deg"]),
            prior["slk_range"][0],
            prior["slk_range"][1]
        ),
        "trunk_inclination": (
            ik_targets.get("trunk_inclination", prior["trunk_contact_mid_deg"]),
            prior["trunk_range"][0],
            prior["trunk_range"][1]
        ),
    }

    # Ankle plantarflexion priors were removed from the 2D model. Keep this
    # conditional to preserve compatibility if ankle priors are reintroduced.
    if (
        "ankle_plantarflexion" in COACHING_CUES
        and "ankle_extension_mid_deg" in prior
        and "ankle_range" in prior
    ):
        variable_mapping["ankle_plantarflexion"] = (
            ik_targets.get("ankle_plantarflexion", prior["ankle_extension_mid_deg"]),
            prior["ankle_range"][0],
            prior["ankle_range"][1],
        )

    items: list[CoachingItem] = []

    for variable_key, (target, range_min, range_max) in variable_mapping.items():
        if variable_key not in measured_angles:
            logger.warning(
                f"Measured angle missing for '{variable_key}'. "
                f"Using target value as placeholder (delta = 0)."
            )
            measured = target
        else:
            measured = measured_angles[variable_key]

        item = generate_coaching_item(
            variable_key=variable_key,
            measured_deg=measured,
            target_deg=target,
            target_range_min_deg=range_min,
            target_range_max_deg=range_max
        )
        items.append(item)

    # Sort by severity: CRITICAL → NEEDS_WORK → ACCEPTABLE → OPTIMAL
    severity_order = {"CRITICAL": 0, "NEEDS_WORK": 1, "ACCEPTABLE": 2, "OPTIMAL": 3}
    items.sort(key=lambda x: severity_order[x.status])

    logger.info(
        f"Coaching report for zone {zone_id}: "
        f"{sum(1 for i in items if i.status == 'CRITICAL')} CRITICAL, "
        f"{sum(1 for i in items if i.status == 'NEEDS_WORK')} NEEDS_WORK, "
        f"{sum(1 for i in items if i.status == 'ACCEPTABLE')} ACCEPTABLE, "
        f"{sum(1 for i in items if i.status == 'OPTIMAL')} OPTIMAL."
    )

    return items


def compute_player_score(
    items: list[CoachingItem],
    v0_ms: float = 0.0
) -> dict:
    """
    Compute a 0-100 technique score from coaching items + optional ball velocity.

    Scoring weights [MODEL]:
        trunk_inclination  : 30%  — primary predictor of ball elevation [ARGUZ-2021]
        support_knee       : 25%  — stability base, affects all other variables
        hip_flexion        : 20%  — main power source (backswing)
        knee_flexion       : 15%  — elastic energy storage (quadriceps)
        ball_velocity      : 10%  — physical output, low weight (technique focus)

    Kinematic penalty scale:
        |δ| ≤ 5°            → score = 100  (tolerance band)
        5° < |δ| < 40°      → score = 100 × (1 − (|δ| − 5) / 35)  (linear decay)
        |δ| ≥ 40°           → score = 0

    Ball velocity normalisation:
        score = min(100, round(100 × v0_ms / 30))
        30 m/s = elite ceiling.
        If v0_ms = 0.0, velocity is excluded and its weight is redistributed.

    Parameters
    ----------
    items : list[CoachingItem]
        Output of generate_full_coaching_report().
    v0_ms : float
        Initial ball velocity [m/s]. Optional — contributes only 10% to score.
        Pass 0.0 to exclude velocity contribution entirely.

    Returns
    -------
    dict with keys:
        "score"     : int   — 0–100 overall technique score
        "level"     : str   — "Beginner" | "Good" | "Pro"
        "breakdown" : dict  — {variable: score_int} per kinematic variable
                              "ball_velocity" included only if v0_ms > 0
    """
    if not items:
        return {"score": 0, "level": "Beginner", "breakdown": {}}

    # ── Scoring constants ─────────────────────────────────────────────────────
    MAX_DEG:       float = 40.0   # deviation at which kinematic score → 0
    TOLERANCE_DEG: float = 5.0    # deviation within which score = 100
    MAX_VELOCITY:  float = 30.0   # m/s — elite ceiling for velocity normalisation

    # ── Kinematic scores ──────────────────────────────────────────────────────
    breakdown: dict[str, int] = {}

    for item in items:
        abs_delta = abs(item.delta_deg)

        if abs_delta <= TOLERANCE_DEG:
            score_int = 100
        else:
            raw = 100.0 * (
                1.0 - (abs_delta - TOLERANCE_DEG) / (MAX_DEG - TOLERANCE_DEG)
            )
            score_int = int(max(0, min(100, round(raw))))

        breakdown[item.variable] = score_int

    # ── Ball velocity score ───────────────────────────────────────────────────
    velocity_included = v0_ms > 0.0
    if velocity_included:
        velocity_score = int(min(100, round(100.0 * v0_ms / MAX_VELOCITY)))
        breakdown["ball_velocity"] = velocity_score

    # ── Weighted average ──────────────────────────────────────────────────────
    total_weight: float = 0.0
    weighted_sum: float = 0.0

    for variable, weight in VARIABLE_WEIGHTS.items():

        # Skip velocity if not provided
        if variable == "ball_velocity" and not velocity_included:
            continue

        score = breakdown.get(variable)

        if score is None:
            # Variable not in report → skip, log, don't penalise
            logger.warning(
                f"[scoring] Variable '{variable}' has weight "
                f"{weight:.0%} but was not found in coaching items. "
                f"Skipping."
            )
            continue

        weighted_sum += weight * score
        total_weight += weight

    # Normalise in case some variables were missing or velocity was excluded
    if total_weight == 0.0:
        overall_score = 0
    else:
        overall_score = int(round(weighted_sum / total_weight))

    # ── Level classification ──────────────────────────────────────────────────
    level = (
        "Pro"      if overall_score >= 80 else
        "Good"     if overall_score >= 50 else
        "Beginner"
    )

    logger.info(
        f"[scoring] overall={overall_score} ({level}) | "
        f"velocity_included={velocity_included} | "
        f"active_weight={total_weight:.2f} | "
        f"breakdown={breakdown}"
    )

    return {
        "score":     overall_score,
        "level":     level,
        "breakdown": breakdown,
    }