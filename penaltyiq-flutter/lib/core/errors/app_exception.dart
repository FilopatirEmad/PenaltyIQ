/// Typed exception hierarchy for PenaltyIQ.
///
/// All exceptions carry a user-readable [message] suitable for
/// display in the UI error states.
abstract class AppException implements Exception {
  const AppException(this.message);
  final String message;

  @override
  String toString() => '${runtimeType}: $message';
}

// ── Network layer ──────────────────────────────────────────────────────────

class NetworkTimeoutException extends AppException {
  const NetworkTimeoutException(super.message);
}

class NetworkConnectionException extends AppException {
  const NetworkConnectionException(super.message);
}

class RequestCancelledException extends AppException {
  const RequestCancelledException(super.message);
}

// ── API layer ──────────────────────────────────────────────────────────────

class ApiValidationException extends AppException {
  const ApiValidationException(super.message);
}

class ApiServerException extends AppException {
  const ApiServerException(super.message);
}

// ── Domain layer ───────────────────────────────────────────────────────────

/// Thrown when the calibration gate has not been passed and
/// a downstream operation requires locked segments.
/// [SPEC §1.6.1]: Hard gate enforcement in the client.
class CalibrationNotLockedException extends AppException {
  const CalibrationNotLockedException()
      : super(
          'Calibration gate has not been passed. '
          'Complete the T-pose calibration before recording a kick.',
        );
}

/// Thrown when IMU gate condition is not satisfied.
/// [SPEC §1.7.1]: Hard gate enforcement in the client.
class ImuGateNotPassedException extends AppException {
  const ImuGateNotPassedException()
      : super(
          'Phone is not level. '
          'Ensure the phone is within ±2° of vertical before recording.',
        );
}

/// Thrown when insufficient ball detections are available
/// for v0 estimation. [SPEC §2.4]
class InsufficientBallDetectionsException extends AppException {
  const InsufficientBallDetectionsException(int found, int required)
      : super(
          'Insufficient ball detections: $found found, $required required. '
          'Ensure the ball is clearly visible in at least $required '
          'consecutive frames after contact.',
        );
}