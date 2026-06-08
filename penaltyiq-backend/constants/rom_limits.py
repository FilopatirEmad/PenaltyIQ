"""
Anatomical Range of Motion (ROM) Limits
Source: Winter (2009), Biomechanics and Motor Control of Human Movement, 4th ed.
        Chapter 3: Kinematic Data Collection and Processing.

Convention
----------
knee / support_knee:
    INCLUDED ANGLE. 180° = full extension (straight leg). Decreasing = flexion.
hip_flexion (UPDATED v2):
    SIGNED THIGH-FROM-VERTICAL. 0° = anatomical neutral (thigh straight down).
    Negative = hip extension / backswing. Positive = hip flexion (thigh forward).
trunk_inclination:
    SIGNED FROM UPWARD VERTICAL. 0° = upright. + = forward lean. − = backward.
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class JointROM:
    """Immutable ROM descriptor for a single joint degree of freedom."""
    joint: str
    dof: str
    min_deg: float
    max_deg: float
    source: str


# ─── Kicking Leg ROM ────────────────────────────────────────────────────────

HIP_FLEXION_ROM = JointROM(
    joint="hip",
    dof="flexion_extension_signed",
    # Signed thigh-from-vertical convention (v2).
    # 0° = anatomical neutral (thigh straight down).
    # Negative = hip extension / backswing phase (thigh behind body).
    # Positive = hip flexion (thigh forward of body).
    # Bounds: backswing rarely exceeds −45°; contact flexion rarely exceeds 60°.
    min_deg=-45.0,   # ~45° of hip extension at max backswing
    max_deg=60.0,    # ~60° of hip flexion at contact for power kicks
    source="Winter (2009), Ch.3; Arguz et al. (2021), Table 4.2"
)

KNEE_FLEXION_ROM = JointROM(
    joint="knee",
    dof="flexion_extension",
    min_deg=0.0,    # full extension
    max_deg=140.0,  # [MEASURED] Winter (2009): knee flexion during kicking backswing
    source="Winter (2009), Ch.3"
)

ANKLE_PLANTARFLEXION_ROM = JointROM(
    joint="ankle",
    dof="plantarflexion_dorsiflexion",
    min_deg=0.0,    # neutral (90° foot-shank)
    max_deg=50.0,   # [MEASURED] Winter (2009): plantarflexion range ~50°
    source="Winter (2009), Ch.3"
)

# ─── Support Leg ROM ─────────────────────────────────────────────────────────

SUPPORT_KNEE_ROM = JointROM(
    joint="support_knee",
    dof="flexion_extension",
    # [MODEL] During instep kick the support knee is semi-flexed.
    # Arguz (2021) reports SLK contact range 109°–131° across zones.
    # We use [100°, 140°] as the safe solver bound with 5° tolerance on each side.
    min_deg=100.0,
    max_deg=140.0,
    source="Arguz et al. (2021), Table 4.2; Winter (2009), Ch.3"
)

TRUNK_INCLINATION_ROM = JointROM(
    joint="trunk",
    dof="inclination",
    # [MODEL] Trunk inclination (angle of trunk segment to vertical).
    # Arguz (2021) reports 103°–123° for penalty kicks across zones.
    # We allow [90°, 135°] as the biomechanically safe solver bound.
    min_deg=90.0,
    max_deg=135.0,
    source="Arguz et al. (2021), Table 4.2; Winter (2009), Ch.6"
)

# ─── Compiled ROM Dictionary for IK Solver ───────────────────────────────────

ROM_BOUNDS: dict = {
    "hip_flexion":              (HIP_FLEXION_ROM.min_deg,           HIP_FLEXION_ROM.max_deg),
    "knee_flexion":             (KNEE_FLEXION_ROM.min_deg,          KNEE_FLEXION_ROM.max_deg),
    "ankle_plantarflexion":     (ANKLE_PLANTARFLEXION_ROM.min_deg,  ANKLE_PLANTARFLEXION_ROM.max_deg),
    "support_knee_flexion":     (SUPPORT_KNEE_ROM.min_deg,          SUPPORT_KNEE_ROM.max_deg),
    "trunk_inclination":        (TRUNK_INCLINATION_ROM.min_deg,     TRUNK_INCLINATION_ROM.max_deg),
}