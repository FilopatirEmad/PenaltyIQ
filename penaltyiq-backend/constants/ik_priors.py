"""
IK Initial Seeds (Prior / Starting Points) for the Constrained Optimiser
Source: Final_Kinematics.xlsx — Stats_Per_Zone sheet [SPEC §4.3]

These are NOT final coaching targets. They serve as:
  1. Initial seeds (q_seed) for the SciPy SLSQP solver — prevents local minima.
  2. Soft safe-band reference for coaching feedback display.
  3. Fallback values when video quality flags indicate low confidence.

[MEASURED] from Final_Kinematics.xlsx Stats_Per_Zone (mean ± SD per zone).
Convention: mid = mean; range = (mean − SD, mean + SD).

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
ANGLE CONVENTIONS  (updated v2 — aligned with angle_calculator v2)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
slk_contact_mid_deg   Support-leg knee at contact — INCLUDED ANGLE [°]
                      180° = full extension (straight leg).
                      Values ~150–170° = semi-flexed support knee. ✓ as-is.

klk_backswing_mid_deg Kicking-leg knee at backswing — INCLUDED ANGLE [°]
                      180° = full extension.
                      Values ~95–130° = moderately bent. ✓ as-is.

hip_backswing_mid_deg Kicking-leg hip at backswing — hip_flex_backswing [°]
                      Included angle (shoulder–hip–knee convention from Sports2D).
                      Higher = more extension. ✓ taken directly from xlsx.

trunk_contact_mid_deg Trunk inclination at contact — SIGNED FROM UPWARD VERTICAL [°]
                      0° = perfectly upright.
                      POSITIVE = forward lean.  NEGATIVE = backward lean. ✓ as-is.

Reliability note (Coefficient of Variation):
  slk   ✓ reliable     (CV < 15 % in most zones)
  hip   ✓ reliable     (CV < 15 % in most zones)
  klk   ~ moderate     (CV 15–25 % in most zones — especially B1/B4)
  trunk ✗ high scatter (trunk oscillates ± so CV is misleading — use with caution)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Zone mapping (from ZoneKey sheet):
  T1 = Top-Left          (شمال فوق)         zone 7 — Corner
  T2 = Centre-Left-Top   (نص شمال فوق)      zone 5 — Centre
  T3 = Centre-Right-Top  (نص يمين فوق)      zone 3 — Centre
  T4 = Top-Right         (يمين فوق)         zone 1 — Corner
  B1 = Bottom-Left       (شمال تحت)         zone 8 — Corner
  B2 = Centre-Left-Bot   (نص شمال تحت)      zone 6 — Centre
  B3 = Centre-Right-Bot  (نص يمين تحت)      zone 4 — Centre
  B4 = Bottom-Right      (يمين تحت)         zone 2 — Corner
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""

from typing import TypedDict


class ZonePrior(TypedDict):
    slk_contact_mid_deg: float    # Support-leg knee at contact   [included angle, °]
    trunk_contact_mid_deg: float  # Trunk inclination at contact  [signed from vertical, °]
    hip_backswing_mid_deg: float  # Kicking-leg hip at backswing  [hip_flex_backswing, °]
    klk_backswing_mid_deg: float  # Kicking-leg knee at backswing [included angle, °]
    # Range bounds for coaching soft-band display  (mean − SD, mean + SD)
    slk_range: tuple
    trunk_range: tuple
    hip_range: tuple
    klk_range: tuple


IK_PRIORS: dict[str, ZonePrior] = {

    # ──────────────────────────────────────────────────────────────────────
    # T1 · Top-Left  (شمال فوق) · zone 7 · Corner
    # Source: Final_Kinematics.xlsx → Stats_Per_Zone, column "Top-Left"
    # ──────────────────────────────────────────────────────────────────────
    "T1": ZonePrior(
        slk_contact_mid_deg   = 164.55,   # sup_knee_contact     mean
        trunk_contact_mid_deg =   2.25,   # trunk_contact        mean
        hip_backswing_mid_deg = 149.93,   # hip_flex_backswing   mean
        klk_backswing_mid_deg = 122.31,   # kick_knee_backswing  mean
        slk_range  = (142.94, 186.17),    # mean ± SD  (164.55 ± 21.61)
        trunk_range= ( -6.16,  10.66),    # mean ± SD  (  2.25 ±  8.41)
        hip_range  = (127.00, 172.87),    # mean ± SD  (149.93 ± 22.94)
        klk_range  = ( 91.30, 153.31),    # mean ± SD  (122.31 ± 31.00)
    ),

    # ──────────────────────────────────────────────────────────────────────
    # T2 · Centre-Left-Top  (نص شمال فوق) · zone 5 · Centre
    # Source: Final_Kinematics.xlsx → Stats_Per_Zone, column "Centre-Left-Top"
    # ──────────────────────────────────────────────────────────────────────
    "T2": ZonePrior(
        slk_contact_mid_deg   = 156.28,   # sup_knee_contact     mean
        trunk_contact_mid_deg =  -2.78,   # trunk_contact        mean
        hip_backswing_mid_deg = 166.62,   # hip_flex_backswing   mean
        klk_backswing_mid_deg = 108.50,   # kick_knee_backswing  mean
        slk_range  = (135.55, 177.00),    # mean ± SD  (156.28 ± 20.73)
        trunk_range= (-12.81,   7.25),    # mean ± SD  ( -2.78 ± 10.03)
        hip_range  = (153.12, 180.11),    # mean ± SD  (166.62 ± 13.49)
        klk_range  = ( 82.60, 134.41),    # mean ± SD  (108.50 ± 25.91)
    ),

    # ──────────────────────────────────────────────────────────────────────
    # T3 · Centre-Right-Top  (نص يمين فوق) · zone 3 · Centre
    # Source: Final_Kinematics.xlsx → Stats_Per_Zone, column "Centre-Right-Top"
    # ──────────────────────────────────────────────────────────────────────
    "T3": ZonePrior(
        slk_contact_mid_deg   = 160.47,   # sup_knee_contact     mean
        trunk_contact_mid_deg =  -0.75,   # trunk_contact        mean
        hip_backswing_mid_deg = 156.97,   # hip_flex_backswing   mean
        klk_backswing_mid_deg = 103.35,   # kick_knee_backswing  mean
        slk_range  = (150.50, 170.43),    # mean ± SD  (160.47 ±  9.97)
        trunk_range= (-15.57,  14.07),    # mean ± SD  ( -0.75 ± 14.82)
        hip_range  = (143.46, 170.48),    # mean ± SD  (156.97 ± 13.51)
        klk_range  = ( 85.11, 121.58),    # mean ± SD  (103.35 ± 18.23)
    ),

    # ──────────────────────────────────────────────────────────────────────
    # T4 · Top-Right  (يمين فوق) · zone 1 · Corner
    # Source: Final_Kinematics.xlsx → Stats_Per_Zone, column "Top-Right"
    # ──────────────────────────────────────────────────────────────────────
    "T4": ZonePrior(
        slk_contact_mid_deg   = 168.97,   # sup_knee_contact     mean
        trunk_contact_mid_deg =  -0.30,   # trunk_contact        mean
        hip_backswing_mid_deg = 172.04,   # hip_flex_backswing   mean
        klk_backswing_mid_deg = 127.38,   # kick_knee_backswing  mean
        slk_range  = (168.36, 169.58),    # mean ± SD  (168.97 ±  0.61)
        trunk_range= ( -4.05,   3.44),    # mean ± SD  ( -0.30 ±  3.75)
        hip_range  = (168.71, 175.38),    # mean ± SD  (172.04 ±  3.33)
        klk_range  = (127.12, 127.63),    # mean ± SD  (127.38 ±  0.25)
    ),

    # ──────────────────────────────────────────────────────────────────────
    # B1 · Bottom-Left  (شمال تحت) · zone 8 · Corner
    # Source: Final_Kinematics.xlsx → Stats_Per_Zone, column "Bottom-Left"
    # ──────────────────────────────────────────────────────────────────────
    "B1": ZonePrior(
        slk_contact_mid_deg   = 153.11,   # sup_knee_contact     mean
        trunk_contact_mid_deg =   5.07,   # trunk_contact        mean
        hip_backswing_mid_deg = 160.77,   # hip_flex_backswing   mean
        klk_backswing_mid_deg = 115.07,   # kick_knee_backswing  mean
        slk_range  = (132.84, 173.37),    # mean ± SD  (153.11 ± 20.26)
        trunk_range= ( -3.10,  13.25),    # mean ± SD  (  5.07 ±  8.17)
        hip_range  = (148.89, 172.66),    # mean ± SD  (160.77 ± 11.89)
        klk_range  = ( 60.99, 169.15),    # mean ± SD  (115.07 ± 54.08)  ← high CV; use with caution
    ),

    # ──────────────────────────────────────────────────────────────────────
    # B2 · Centre-Left-Bot  (نص شمال تحت) · zone 6 · Centre
    # Source: Final_Kinematics.xlsx → Stats_Per_Zone, column "Centre-Left-Bot"
    # ──────────────────────────────────────────────────────────────────────
    "B2": ZonePrior(
        slk_contact_mid_deg   = 161.41,   # sup_knee_contact     mean
        trunk_contact_mid_deg =  11.57,   # trunk_contact        mean
        hip_backswing_mid_deg = 146.17,   # hip_flex_backswing   mean
        klk_backswing_mid_deg = 109.98,   # kick_knee_backswing  mean
        slk_range  = (143.23, 179.59),    # mean ± SD  (161.41 ± 18.18)
        trunk_range= (  3.40,  19.74),    # mean ± SD  ( 11.57 ±  8.17)
        hip_range  = (132.27, 160.06),    # mean ± SD  (146.17 ± 13.90)
        klk_range  = ( 90.34, 129.62),    # mean ± SD  (109.98 ± 19.64)
    ),

    # ──────────────────────────────────────────────────────────────────────
    # B3 · Centre-Right-Bot  (نص يمين تحت) · zone 4 · Centre
    # Source: Final_Kinematics.xlsx → Stats_Per_Zone, column "Centre-Right-Bot"
    # ──────────────────────────────────────────────────────────────────────
    "B3": ZonePrior(
        slk_contact_mid_deg   = 161.07,   # sup_knee_contact     mean
        trunk_contact_mid_deg =  -1.12,   # trunk_contact        mean
        hip_backswing_mid_deg = 157.32,   # hip_flex_backswing   mean
        klk_backswing_mid_deg = 109.99,   # kick_knee_backswing  mean
        slk_range  = (147.00, 175.14),    # mean ± SD  (161.07 ± 14.07)
        trunk_range= ( -9.10,   6.86),    # mean ± SD  ( -1.12 ±  7.98)
        hip_range  = (139.14, 175.51),    # mean ± SD  (157.32 ± 18.18)
        klk_range  = ( 92.97, 127.00),    # mean ± SD  (109.99 ± 17.02)
    ),

    # ──────────────────────────────────────────────────────────────────────
    # B4 · Bottom-Right  (يمين تحت) · zone 2 · Corner
    # Source: Final_Kinematics.xlsx → Stats_Per_Zone, column "Bottom-Right"
    # ──────────────────────────────────────────────────────────────────────
    "B4": ZonePrior(
        slk_contact_mid_deg   = 151.94,   # sup_knee_contact     mean
        trunk_contact_mid_deg =   2.68,   # trunk_contact        mean
        hip_backswing_mid_deg = 156.93,   # hip_flex_backswing   mean
        klk_backswing_mid_deg =  94.58,   # kick_knee_backswing  mean
        slk_range  = (128.56, 175.32),    # mean ± SD  (151.94 ± 23.38)
        trunk_range= (-12.11,  17.47),    # mean ± SD  (  2.68 ± 14.79)
        hip_range  = (147.35, 166.51),    # mean ± SD  (156.93 ±  9.58)
        klk_range  = ( 77.12, 112.05),    # mean ± SD  ( 94.58 ± 17.47)
    ),
}