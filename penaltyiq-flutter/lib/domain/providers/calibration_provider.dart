import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:uuid/uuid.dart';

import '../../data/models/calibration_response.dart';
import '../../data/repositories/penaltyiq_repository.dart';

/// Calibration state machine.
///
/// States:
///   idle        → User has not started calibration
///   collecting  → Collecting T-pose frames
///   processing  → Waiting for backend response
///   locked      → Calibration gate passed (segments locked)
///   failed      → Stability criterion not met
///
/// [SPEC §1.6.1]: Hard gate — analysis is blocked unless state == locked.

enum CalibrationStatus {
  idle,
  collecting,
  processing,
  locked,
  failed,
}

class CalibrationState {
  const CalibrationState({
    required this.status,
    required this.sessionId,
    this.response,
    this.errorMessage,
    this.framesCollected = 0,
  });

  final CalibrationStatus status;
  final String sessionId;
  final CalibrationResponse? response;
  final String? errorMessage;
  final int framesCollected;

  /// Hard gate check. [SPEC §1.6.1]
  bool get isLocked => status == CalibrationStatus.locked;

  /// Segments locked by calibration gate.
  /// Returns null if gate has not passed (prevents downstream use).
  LockedSegments? get lockedSegments => response?.segmentsM;

  double? get scaleMPerPx => response?.scaleMPerPx;

  double get calibrationProgressFraction {
    if (framesCollected >= AppMinFrames.value) return 1.0;
    return framesCollected / AppMinFrames.value;
  }

  CalibrationState copyWith({
    CalibrationStatus? status,
    CalibrationResponse? response,
    String? errorMessage,
    int? framesCollected,
  }) {
    return CalibrationState(
      status: status ?? this.status,
      sessionId: sessionId,
      response: response ?? this.response,
      errorMessage: errorMessage ?? this.errorMessage,
      framesCollected: framesCollected ?? this.framesCollected,
    );
  }

  static const int minFramesRequired = 120; // [SPEC §1.6.1]
}

// Workaround for constant in copyWith
class AppMinFrames {
  static const int value = 120;
}

class CalibrationNotifier extends StateNotifier<CalibrationState> {
  CalibrationNotifier(this._repository)
      : super(CalibrationState(
          status: CalibrationStatus.idle,
          sessionId: const Uuid().v4(),
        ));

  final PenaltyIqRepository _repository;

  /// Start collecting T-pose frames.
  void startCollection() {
    state = state.copyWith(
      status: CalibrationStatus.collecting,
      framesCollected: 0,
    );
  }

  /// Update frame collection counter (called per processed frame).
  void incrementFrameCount() {
    if (state.status == CalibrationStatus.collecting) {
      state = state.copyWith(
        framesCollected: state.framesCollected + 1,
      );
    }
  }

  /// Submit collected frames to the backend calibration gate.
  ///
  /// The caller is responsible for building the frame payload.
  /// This method handles the async state transitions.
  Future<void> submitCalibration(List<Map<String, dynamic>> frames) async {
    state = state.copyWith(status: CalibrationStatus.processing);

    try {
      final response = await _repository.calibrate(
        sessionId: state.sessionId,
        frames: frames,
      );

      if (response.status == 'LOCKED') {
        state = state.copyWith(
          status: CalibrationStatus.locked,
          response: response,
          errorMessage: null,
        );
      } else {
        state = state.copyWith(
          status: CalibrationStatus.failed,
          response: response,
          errorMessage: response.error ??
              'Calibration failed. Please re-attempt the T-pose.',
        );
      }
    } catch (e) {
      state = state.copyWith(
        status: CalibrationStatus.failed,
        errorMessage: 'Network error: ${e.toString()}',
      );
    }
  }

  /// Reset to idle for re-calibration.
  void reset() {
    state = CalibrationState(
      status: CalibrationStatus.idle,
      sessionId: const Uuid().v4(),
    );
  }
}

final calibrationProvider =
    StateNotifierProvider<CalibrationNotifier, CalibrationState>((ref) {
  final repository = ref.watch(penaltyIqRepositoryProvider);
  return CalibrationNotifier(repository);
});