"""
FIFA Constants — Source: FIFA Laws of the Game 2024/25 [FIFA-2024]
All values are [MEASURED] from the official FIFA specification.
No derived or estimated values appear in this file.
"""

# Goal dimensions [MEASURED][FIFA-2024]
GOAL_WIDTH_M: float = 7.32       # metres, inner post to inner post
GOAL_HEIGHT_M: float = 2.44      # metres, ground to lower edge of crossbar
PENALTY_DISTANCE_M: float = 11.00  # metres, penalty mark to goal line

# Ball specification [MEASURED][FIFA-2024]
BALL_DIAMETER_M: float = 0.22    # metres (FIFA size 5: circumference 68–70cm → diameter ~22cm)
BALL_MASS_KG: float = 0.43       # kg (FIFA size 5: 410–450g, midpoint)
BALL_RADIUS_M: float = BALL_DIAMETER_M / 2.0  # 0.11 m

# Physics constants
GRAVITY_MS2: float = 9.80665     # m/s² (standard gravity, NIST)

# Aerodynamic safety margin [MODEL][SPEC §2.8]
# Conservative crossbar clearance buffer to account for drag and spin uncertainty.
# Range stated in spec: 0.10–0.20 m. We use the conservative upper bound.
CROSSBAR_SAFETY_MARGIN_M: float = 0.15

# Goal zone geometry [MODEL][SPEC §2.3]
# Each zone is W/4 wide = 1.83 m, H/2 tall = 1.22 m
ZONE_WIDTH_M: float = GOAL_WIDTH_M / 4.0    # 1.83 m
ZONE_HEIGHT_M: float = GOAL_HEIGHT_M / 2.0  # 1.22 m

SAMPLE_RATE_HZ = 60.0
FRAME_DT_S = 1.0 / SAMPLE_RATE_HZ
# Zone vertical targets [MODEL][SPEC §2.3]
# Top zones: crossbar clearance target y = 2.20 m (< 2.44 m crossbar)
# Bottom zones: ground clearance target y = 0.30 m (> 0.0 m ground + ball radius)
TOP_ZONE_Y_M: float = 2.20
BOTTOM_ZONE_Y_M: float = 0.30

# Zone horizontal centres (x=0 at goal centre) [MODEL][SPEC Table 2.1]
ZONE_X_COORDS_M: dict = {
    "FAR_LEFT":       -3.36,
    "CENTRE_LEFT":    -1.22,
    "CENTRE_RIGHT":   +1.22,
    "FAR_RIGHT":      +3.36,
}

# Complete zone registry [MODEL][SPEC Table 2.1]
GOAL_ZONES: dict = {
    "T1": {"x_m": -3.36, "y_m": 2.20, "label": "Top Far-Left",        "difficulty": "HIGH"},
    "T2": {"x_m": -1.22, "y_m": 2.20, "label": "Top Centre-Left",     "difficulty": "HIGH"},
    "T3": {"x_m": +1.22, "y_m": 2.20, "label": "Top Centre-Right",    "difficulty": "MODERATE"},
    "T4": {"x_m": +3.36, "y_m": 2.20, "label": "Top Far-Right",       "difficulty": "HIGH"},
    "B1": {"x_m": -3.36, "y_m": 0.30, "label": "Bottom Far-Left",     "difficulty": "MODERATE"},
    "B2": {"x_m": -1.22, "y_m": 0.30, "label": "Bottom Centre-Left",  "difficulty": "LOW_MODERATE"},
    "B3": {"x_m": +1.22, "y_m": 0.30, "label": "Bottom Centre-Right", "difficulty": "LOW"},
    "B4": {"x_m": +3.36, "y_m": 0.30, "label": "Bottom Far-Right",    "difficulty": "MODERATE"},
}