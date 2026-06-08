# Biomechanical AI Pipeline

The scientific core of PenaltyIQ translates raw video pixels into actionable, clinical-grade kinematic feedback. This document details the 4-step pipeline located in the `core/` backend directory.

## 1. Vision Extraction (MediaPipe & OpenCV)
- **Frame Slicing:** OpenCV (`cv2.VideoCapture`) parses the uploaded video file, converting the `BGR` color space to `RGB` for model compatibility.
- **Pose Estimation:** Google's **MediaPipe Pose** processes each frame, mapping 33 skeletal landmarks. 
- **2D Dimensionality:** PenaltyIQ is optimized for 2D sagittal-plane (side-view) recording. The $Z$-axis (depth) is discarded to reduce computational overhead, operating entirely in pixel space ($x, y$).

## 2. Kinematic Feature Math (NumPy & SciPy)
Once landmarks are extracted, the system calculates critical angles using **Dot-product Arccos** mathematics:

$$ \theta = \arccos\left(\frac{\vec{u} \cdot \vec{v}}{|\vec{u}| |\vec{v}|}\right) $$

For example, `hip_flexion` (the backswing angle) is calculated as the included angle between the shoulder-hip vector and the hip-knee vector.

**Signal Smoothing:**
Due to the high velocity of a penalty kick, standard 60fps smartphone cameras often produce motion blur, resulting in tracking noise or missing landmarks (`NaN` values). The pipeline uses a **Savitzky-Golay Filter** (`scipy.signal.savgol_filter`) to interpolate and smooth the angle time-series without destroying the true kinematic peaks of the movement.

## 3. Automated Event Detection
To score a player, the system must identify the exact frames where biomechanical events occur:
- **Backswing Frame:** Detected algorithmically as the global maximum of the `kick_knee` angle in the latter half of the signal.
- **Contact Frame:** Detected as the first local minimum of the `kick_knee` angle immediately following the backswing.

## 4. Coaching Engine & Scoring (IK Logic)
The scoring engine is a sophisticated **Rule-Based System** grounded in biomechanical literature (specifically Arguz et al., 2021). 

Measured angles at the *Contact Frame* are compared against an Inverse Kinematics (IK) ideal target. 
The absolute deviation ($\Delta$) determines the score penalty based on a weighted linear decay model:

- Trunk Inclination: 30% weight
- Support Knee Angle: 25% weight
- Hip Flexion: 20% weight
- Knee Flexion: 15% weight
- Ball Velocity: 10% weight

A $\Delta \le 5^\circ$ yields a perfect 100% feature score. If $\Delta > 40^\circ$, the feature scores 0%. The final aggregated score dictates the player's technique level (Pro, Good, or Beginner) and generates specific text-based corrective cues.
