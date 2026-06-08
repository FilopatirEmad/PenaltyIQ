/// Application-wide constants.
/// All physical tolerances are documented with their scientific source.
library;

class AppConstants {
  AppConstants._(); // prevent instantiation

  // ── IMU Tilt Gate ──────────────────────────────────────────────────────────
  /// Maximum allowable phone tilt from vertical (sagittal plane) [degrees].
  /// [SPEC §1.7.1]: "Record button hidden/disabled unless phone is within
  /// ±2° tolerance of required upright orientation."
  static const double imuTiltToleranceDeg = 2.0;

  /// IMU polling interval [milliseconds].
  /// Accelerometer at 50Hz (20ms) provides smooth level indicator.
  static const int imuPollingIntervalMs = 20;

  // ── Calibration Gate ───────────────────────────────────────────────────────
  /// Duration of T-pose stability window [seconds].
  /// [SPEC §1.6.1]: "stable for at least 2 seconds."
  static const double calibrationWindowS = 2.0;

  /// Frames per second for calibration clip. [SPEC §1.1]
  static const int calibrationFps = 60;

  /// Minimum frames required = calibrationWindowS × calibrationFps.
  static const int calibrationMinFrames = 120;

  // ── Physics Constants (mirrored from backend for UI display) ───────────────
  /// FIFA goal width [m]. [FIFA-2024]
  static const double goalWidthM = 7.32;

  /// FIFA goal height [m]. [FIFA-2024]
  static const double goalHeightM = 2.44;

  /// Penalty distance [m]. [FIFA-2024]
  static const double penaltyDistanceM = 11.0;

  /// FIFA ball diameter [m]. [FIFA-2024]
  static const double ballDiameterM = 0.22;

  // ── API ────────────────────────────────────────────────────────────────────
  /// Default request timeout for short requests (health, calibrate) [seconds].
  static const int apiTimeoutS = 60;

  /// Extended timeout for video upload + processing [seconds].
  /// MediaPipe pose extraction on a 10-second clip can take 60–180 seconds.
  static const int videoProcessingTimeoutS = 300;

  // ── Coaching Status Colours (semantic, matches backend thresholds) ─────────
  /// OPTIMAL: |δ| ≤ 3°
  static const double coachingOptimalThresholdDeg  = 3.0;
  /// ACCEPTABLE: |δ| ≤ 8°
  static const double coachingAcceptableThresholdDeg = 8.0;
  /// NEEDS_WORK: |δ| ≤ 15°
  static const double coachingNeedsWorkThresholdDeg  = 15.0;
  /// CRITICAL: |δ| > 15°
}