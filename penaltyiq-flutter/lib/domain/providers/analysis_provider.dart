import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../core/errors/app_exception.dart';
import '../../data/models/analysis_response.dart';
import '../../data/repositories/penaltyiq_repository.dart';
import 'calibration_provider.dart';

/// Analysis state — sealed union type.
///
/// Using a sealed class pattern for exhaustive when() matching.
sealed class AnalysisState {
  const AnalysisState();
}

class AnalysisInitial extends AnalysisState {
  const AnalysisInitial();
}

class AnalysisLoading extends AnalysisState {
  const AnalysisLoading();
}

class AnalysisSuccess extends AnalysisState {
  const AnalysisSuccess(this.response);
  final AnalysisResponse response;
}

class AnalysisError extends AnalysisState {
  const AnalysisError(this.message);
  final String message;
}

extension AnalysisStateX on AnalysisState {
  /// Exhaustive pattern matching helper.
  T when<T>({
    required T Function() initial,
    required T Function() loading,
    required T Function(String message) error,
    required T Function(AnalysisResponse response) success,
  }) {
    return switch (this) {
      AnalysisInitial()         => initial(),
      AnalysisLoading()         => loading(),
      AnalysisError(:final message)     => error(message),
      AnalysisSuccess(:final response)  => success(response),
    };
  }
}

/// Analysis state notifier.
///
/// Enforces both hard gates before submitting to the backend:
///   1. Calibration gate: CalibrationStatus.locked [SPEC §1.6.1]
///   2. IMU gate: enforced at route level, checked here defensively.
class AnalysisNotifier extends StateNotifier<AnalysisState> {
  AnalysisNotifier(this._repository, this._ref)
      : super(const AnalysisInitial());

  final PenaltyIqRepository _repository;
  final Ref _ref;

  /// Submit analysis request.
  ///
  /// Pre-conditions (hard gates checked before HTTP call):
  ///   - Calibration must be locked. [SPEC §1.6.1]
  ///   - Frames must contain ≥ 4 ball detections. [SPEC §2.4]
  Future<void> submitAnalysis({
    required String goalZone,
    required List<Map<String, dynamic>> frames,
    double fps = 60.0,
  }) async {
    // ── Hard gate: calibration must be locked ────────────────────────────
    final calibState = _ref.read(calibrationProvider);
    if (!calibState.isLocked) {
      state = const AnalysisError(
        'Calibration gate not passed. '
        'Please complete the T-pose calibration before recording.',
      );
      return;
    }

    final segments = calibState.lockedSegments;
    final scale    = calibState.scaleMPerPx;

    if (segments == null || scale == null) {
      state = const AnalysisError(
        'Calibration data missing. Please re-calibrate.',
      );
      return;
    }

    // ── Validate ball detections ─────────────────────────────────────────
    final ballDetections = frames
        .where((f) => f['ball_center_px'] != null)
        .length;

    if (ballDetections < 4) {
      state = AnalysisError(
        'Insufficient ball detections ($ballDetections/4 required). '
        'Ensure the ball is clearly visible in the first frames after contact. '
        '[SPEC §2.4]',
      );
      return;
    }

    // ── Submit to backend ────────────────────────────────────────────────
    state = const AnalysisLoading();

    try {
      final calibrationPayload = {
        'scale_m_per_px': scale,
        'thigh_m': segments.thighM,
        'shank_m': segments.shankM,
        'trunk_m': segments.trunkM,
        'leg_m':   segments.legM,
      };

      final response = await _repository.analyze(
        sessionId:   calibState.sessionId,
        goalZone:    goalZone,
        calibration: calibrationPayload,
        frames:      frames,
        fps:         fps,
      );

      state = AnalysisSuccess(response);
    } on AppException catch (e) {
      state = AnalysisError(e.message);
    } catch (e) {
      state = AnalysisError('Unexpected error: ${e.toString()}');
    }
  }

  /// Submit analysis by chaining directly from /process-video output.
  ///
  /// This is the real-user flow:
  /// local video -> process-video -> analyze.
  Future<void> submitFromProcessedPayload({
    required Map<String, dynamic> processedPayload,
    required String goalZone,
  }) async {
    state = const AnalysisLoading();

    try {
      final sessionId = processedPayload['session_id'] as String?;
      final fps = (processedPayload['fps'] as num?)?.toDouble() ?? 60.0;

      final calibration =
          (processedPayload['calibration'] as Map<String, dynamic>?) ??
          const <String, dynamic>{};

      final gatePassed = calibration['gate_passed'] == true;
      final gatePassedWithFallback =
          calibration['gate_passed_with_fallback'] == true;
      final calibrationUsable = gatePassed || gatePassedWithFallback;
      final scale = (calibration['scale_m_per_px'] as num?)?.toDouble();
      final segments = calibration['segments_m'] as Map<String, dynamic>?;
      final calibrationError = calibration['error']?.toString();

      if (!calibrationUsable || scale == null || segments == null) {
        state = AnalysisError(
          calibrationError ??
              'Calibration did not produce usable segment data. '
                  'Please use a clearer side-view clip with the full body visible.',
        );
        return;
      }

      final framesDynamic = processedPayload['analysis_frames'];
      if (framesDynamic is! List) {
        state = const AnalysisError(
          'Process-video response did not include analysis frames.',
        );
        return;
      }

      final frames = framesDynamic.cast<Map<String, dynamic>>();
      if (frames.isEmpty) {
        state = const AnalysisError(
          'No analysis frames produced from uploaded video.',
        );
        return;
      }

      // Forward contact_frame_index so backend uses correct physics window
      final contactFrameIndex =
          (processedPayload['contact_frame_index'] as num?)?.toInt();

      final calibrationPayload = {
        'scale_m_per_px': scale,
        'thigh_m': (segments['thigh_m'] as num).toDouble(),
        'shank_m': (segments['shank_m'] as num).toDouble(),
        'trunk_m': (segments['trunk_m'] as num).toDouble(),
        'leg_m':   (segments['leg_m'] as num).toDouble(),
        // Additional fields required by AnalysisRequest calibration schema
        'gate_passed':               gatePassed,
        'gate_passed_with_fallback': gatePassedWithFallback,
        'fallback_reason':           calibration['fallback_reason'],
        'thigh_variation_m':         (segments['thigh_variation_m'] as num?)?.toDouble() ?? 0.0,
        'thigh_tolerance_m':         (segments['thigh_tolerance_m'] as num?)?.toDouble() ?? 0.01,
        'frames_used':               (segments['frames_used'] as num?)?.toInt() ?? 0,
      };

      final response = await _repository.analyze(
        sessionId:          sessionId ?? '',
        goalZone:           goalZone,
        calibration:        calibrationPayload,
        frames:             frames,
        fps:                fps,
        contactFrameIndex:  contactFrameIndex,
      );

      state = AnalysisSuccess(response);
    } on AppException catch (e) {
      state = AnalysisError(e.message);
    } catch (e) {
      state = AnalysisError('Unexpected error: ${e.toString()}');
    }
  }

  void reset() => state = const AnalysisInitial();
}

final analysisProvider =
    StateNotifierProvider<AnalysisNotifier, AnalysisState>((ref) {
  final repository = ref.watch(penaltyIqRepositoryProvider);
  return AnalysisNotifier(repository, ref);
});