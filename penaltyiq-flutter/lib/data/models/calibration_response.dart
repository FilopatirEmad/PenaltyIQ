import 'package:freezed_annotation/freezed_annotation.dart';

part 'calibration_response.freezed.dart';
part 'calibration_response.g.dart';

/// Mirrors CalibrationResponse Pydantic schema from backend.
/// All fields documented with their scientific source.

@freezed
class CalibrationResponse with _$CalibrationResponse {
  const factory CalibrationResponse({
    @JsonKey(name: 'session_id') required String sessionId,

    /// "LOCKED" | "FAILED" | "INSUFFICIENT_DATA"
    required String status,

    /// S = 0.22 / d_ball_px [m/pixel]. [FIFA-2024, SPEC §1.2.1]
    @JsonKey(name: 'scale_m_per_px') double? scaleMPerPx,

    @JsonKey(name: 'segments_m') LockedSegments? segmentsM,

    @JsonKey(name: 'stability_check')
    required StabilityCheckResult stabilityCheck,

    @JsonKey(name: 'frames_used') required int framesUsed,

    String? error,
  }) = _CalibrationResponse;

  factory CalibrationResponse.fromJson(Map<String, dynamic> json) =>
      _$CalibrationResponseFromJson(json);
}

@freezed
class LockedSegments with _$LockedSegments {
  const factory LockedSegments({
    /// Thigh length: hip → knee [m]. [WINTER-2009 Ch.3]
    @JsonKey(name: 'thigh_m') required double thighM,

    /// Shank length: knee → ankle [m]. [WINTER-2009 Ch.3]
    @JsonKey(name: 'shank_m') required double shankM,

    /// Trunk length: hip → shoulder [m]. [WINTER-2009 Ch.3]
    @JsonKey(name: 'trunk_m') required double trunkM,

    /// L_thigh + L_shank [m]. [SPEC §1.3.4]
    @JsonKey(name: 'leg_m') required double legM,
  }) = _LockedSegments;

  factory LockedSegments.fromJson(Map<String, dynamic> json) =>
      _$LockedSegmentsFromJson(json);
}

@freezed
class StabilityCheckResult with _$StabilityCheckResult {
  const factory StabilityCheckResult({
    @JsonKey(name: 'thigh_variation_m')  required double thighVariationM,
    @JsonKey(name: 'shank_variation_m')  required double shankVariationM,
    @JsonKey(name: 'trunk_variation_m')  required double trunkVariationM,
    @JsonKey(name: 'thigh_tolerance_m')  required double thighToleranceM,
    @JsonKey(name: 'shank_tolerance_m')  required double shankToleranceM,
    @JsonKey(name: 'trunk_tolerance_m')  required double trunkToleranceM,
    @JsonKey(name: 'window_duration_s')  required double windowDurationS,
    @JsonKey(name: 'thigh_passed')       required bool thighPassed,
    @JsonKey(name: 'shank_passed')       required bool shankPassed,
    @JsonKey(name: 'trunk_passed')       required bool trunkPassed,
    @JsonKey(name: 'overall_passed')     required bool overallPassed,
  }) = _StabilityCheckResult;

  factory StabilityCheckResult.fromJson(Map<String, dynamic> json) =>
      _$StabilityCheckResultFromJson(json);
}