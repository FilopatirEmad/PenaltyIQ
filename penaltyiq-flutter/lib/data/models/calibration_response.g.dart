// GENERATED CODE - DO NOT MODIFY BY HAND

part of 'calibration_response.dart';

// **************************************************************************
// JsonSerializableGenerator
// **************************************************************************

_$CalibrationResponseImpl _$$CalibrationResponseImplFromJson(
        Map<String, dynamic> json) =>
    _$CalibrationResponseImpl(
      sessionId: json['session_id'] as String,
      status: json['status'] as String,
      scaleMPerPx: (json['scale_m_per_px'] as num?)?.toDouble(),
      segmentsM: json['segments_m'] == null
          ? null
          : LockedSegments.fromJson(json['segments_m'] as Map<String, dynamic>),
      stabilityCheck: StabilityCheckResult.fromJson(
          json['stability_check'] as Map<String, dynamic>),
      framesUsed: (json['frames_used'] as num).toInt(),
      error: json['error'] as String?,
    );

Map<String, dynamic> _$$CalibrationResponseImplToJson(
        _$CalibrationResponseImpl instance) =>
    <String, dynamic>{
      'session_id': instance.sessionId,
      'status': instance.status,
      'scale_m_per_px': instance.scaleMPerPx,
      'segments_m': instance.segmentsM,
      'stability_check': instance.stabilityCheck,
      'frames_used': instance.framesUsed,
      'error': instance.error,
    };

_$LockedSegmentsImpl _$$LockedSegmentsImplFromJson(Map<String, dynamic> json) =>
    _$LockedSegmentsImpl(
      thighM: (json['thigh_m'] as num).toDouble(),
      shankM: (json['shank_m'] as num).toDouble(),
      trunkM: (json['trunk_m'] as num).toDouble(),
      legM: (json['leg_m'] as num).toDouble(),
    );

Map<String, dynamic> _$$LockedSegmentsImplToJson(
        _$LockedSegmentsImpl instance) =>
    <String, dynamic>{
      'thigh_m': instance.thighM,
      'shank_m': instance.shankM,
      'trunk_m': instance.trunkM,
      'leg_m': instance.legM,
    };

_$StabilityCheckResultImpl _$$StabilityCheckResultImplFromJson(
        Map<String, dynamic> json) =>
    _$StabilityCheckResultImpl(
      thighVariationM: (json['thigh_variation_m'] as num).toDouble(),
      shankVariationM: (json['shank_variation_m'] as num).toDouble(),
      trunkVariationM: (json['trunk_variation_m'] as num).toDouble(),
      thighToleranceM: (json['thigh_tolerance_m'] as num).toDouble(),
      shankToleranceM: (json['shank_tolerance_m'] as num).toDouble(),
      trunkToleranceM: (json['trunk_tolerance_m'] as num).toDouble(),
      windowDurationS: (json['window_duration_s'] as num).toDouble(),
      thighPassed: json['thigh_passed'] as bool,
      shankPassed: json['shank_passed'] as bool,
      trunkPassed: json['trunk_passed'] as bool,
      overallPassed: json['overall_passed'] as bool,
    );

Map<String, dynamic> _$$StabilityCheckResultImplToJson(
        _$StabilityCheckResultImpl instance) =>
    <String, dynamic>{
      'thigh_variation_m': instance.thighVariationM,
      'shank_variation_m': instance.shankVariationM,
      'trunk_variation_m': instance.trunkVariationM,
      'thigh_tolerance_m': instance.thighToleranceM,
      'shank_tolerance_m': instance.shankToleranceM,
      'trunk_tolerance_m': instance.trunkToleranceM,
      'window_duration_s': instance.windowDurationS,
      'thigh_passed': instance.thighPassed,
      'shank_passed': instance.shankPassed,
      'trunk_passed': instance.trunkPassed,
      'overall_passed': instance.overallPassed,
    };
