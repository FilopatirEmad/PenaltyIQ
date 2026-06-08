// GENERATED CODE - DO NOT MODIFY BY HAND

part of 'analysis_response.dart';

// **************************************************************************
// JsonSerializableGenerator
// **************************************************************************

_$AnalysisResponseImpl _$$AnalysisResponseImplFromJson(
        Map<String, dynamic> json) =>
    _$AnalysisResponseImpl(
      sessionId: json['session_id'] as String,
      goalZone: json['goal_zone'] as String,
      physics: PhysicsResult.fromJson(json['physics'] as Map<String, dynamic>),
      ikResult: json['ik_result'] == null
          ? null
          : IkResult.fromJson(json['ik_result'] as Map<String, dynamic>),
      digitalTwin: json['digital_twin'] == null
          ? null
          : DigitalTwinResult.fromJson(
              json['digital_twin'] as Map<String, dynamic>),
      playerScore: json['player_score'] == null
          ? null
          : PlayerScore.fromJson(json['player_score'] as Map<String, dynamic>),
      coachingFeedback: (json['coaching_feedback'] as List<dynamic>?)
              ?.map((e) =>
                  CoachingFeedbackItem.fromJson(e as Map<String, dynamic>))
              .toList() ??
          const [],
      pipelineWarnings: (json['pipeline_warnings'] as List<dynamic>?)
              ?.map((e) => e as String)
              .toList() ??
          const [],
    );

Map<String, dynamic> _$$AnalysisResponseImplToJson(
        _$AnalysisResponseImpl instance) =>
    <String, dynamic>{
      'session_id': instance.sessionId,
      'goal_zone': instance.goalZone,
      'physics': instance.physics,
      'ik_result': instance.ikResult,
      'digital_twin': instance.digitalTwin,
      'player_score': instance.playerScore,
      'coaching_feedback': instance.coachingFeedback,
      'pipeline_warnings': instance.pipelineWarnings,
    };

_$PlayerScoreImpl _$$PlayerScoreImplFromJson(Map<String, dynamic> json) =>
    _$PlayerScoreImpl(
      score: (json['score'] as num?)?.toInt() ?? 0,
      level: json['level'] as String? ?? 'Beginner',
      breakdown: (json['breakdown'] as Map<String, dynamic>?)?.map(
            (k, e) => MapEntry(k, (e as num).toInt()),
          ) ??
          const {},
    );

Map<String, dynamic> _$$PlayerScoreImplToJson(_$PlayerScoreImpl instance) =>
    <String, dynamic>{
      'score': instance.score,
      'level': instance.level,
      'breakdown': instance.breakdown,
    };

_$PhysicsResultImpl _$$PhysicsResultImplFromJson(Map<String, dynamic> json) =>
    _$PhysicsResultImpl(
      v0MeasuredMs: (json['v0_measured_ms'] as num).toDouble(),
      thetaVDeg: (json['theta_v_deg'] as num).toDouble(),
      thetaHDeg: (json['theta_h_deg'] as num).toDouble(),
      speedRegime: json['speed_regime'] as String,
      feasibility: json['feasibility'] as String,
      crossbarClearanceM: (json['crossbar_clearance_m'] as num).toDouble(),
      safetyMarginSatisfied: json['safety_margin_satisfied'] as bool,
    );

Map<String, dynamic> _$$PhysicsResultImplToJson(_$PhysicsResultImpl instance) =>
    <String, dynamic>{
      'v0_measured_ms': instance.v0MeasuredMs,
      'theta_v_deg': instance.thetaVDeg,
      'theta_h_deg': instance.thetaHDeg,
      'speed_regime': instance.speedRegime,
      'feasibility': instance.feasibility,
      'crossbar_clearance_m': instance.crossbarClearanceM,
      'safety_margin_satisfied': instance.safetyMarginSatisfied,
    };

_$IkResultImpl _$$IkResultImplFromJson(Map<String, dynamic> json) =>
    _$IkResultImpl(
      hipFlexionDeg: (json['hip_flexion_deg'] as num).toDouble(),
      kneeAngleDeg: (json['knee_angle_deg'] as num).toDouble(),
      anklePlantarflexionDeg:
          (json['ankle_plantarflexion_deg'] as num).toDouble(),
      supportLegKneeDeg: (json['support_leg_knee_deg'] as num).toDouble(),
      trunkInclinationDeg: (json['trunk_inclination_deg'] as num).toDouble(),
      solverConverged: json['solver_converged'] as bool,
      residual: (json['residual'] as num).toDouble(),
    );

Map<String, dynamic> _$$IkResultImplToJson(_$IkResultImpl instance) =>
    <String, dynamic>{
      'hip_flexion_deg': instance.hipFlexionDeg,
      'knee_angle_deg': instance.kneeAngleDeg,
      'ankle_plantarflexion_deg': instance.anklePlantarflexionDeg,
      'support_leg_knee_deg': instance.supportLegKneeDeg,
      'trunk_inclination_deg': instance.trunkInclinationDeg,
      'solver_converged': instance.solverConverged,
      'residual': instance.residual,
    };

_$DigitalTwinResultImpl _$$DigitalTwinResultImplFromJson(
        Map<String, dynamic> json) =>
    _$DigitalTwinResultImpl(
      predictedXM: (json['predicted_x_m'] as num).toDouble(),
      predictedYM: (json['predicted_y_m'] as num).toDouble(),
      zoneHit: json['zone_hit'] as String,
      verificationPassed: json['verification_passed'] as bool,
      xErrorM: (json['x_error_m'] as num).toDouble(),
      yErrorM: (json['y_error_m'] as num).toDouble(),
    );

Map<String, dynamic> _$$DigitalTwinResultImplToJson(
        _$DigitalTwinResultImpl instance) =>
    <String, dynamic>{
      'predicted_x_m': instance.predictedXM,
      'predicted_y_m': instance.predictedYM,
      'zone_hit': instance.zoneHit,
      'verification_passed': instance.verificationPassed,
      'x_error_m': instance.xErrorM,
      'y_error_m': instance.yErrorM,
    };

_$CoachingFeedbackItemImpl _$$CoachingFeedbackItemImplFromJson(
        Map<String, dynamic> json) =>
    _$CoachingFeedbackItemImpl(
      variable: json['variable'] as String,
      label: json['label'] as String? ?? '',
      measuredDeg: (json['measured_deg'] as num).toDouble(),
      targetDeg: (json['target_deg'] as num).toDouble(),
      targetRangeMinDeg: (json['target_range_min_deg'] as num).toDouble(),
      targetRangeMaxDeg: (json['target_range_max_deg'] as num).toDouble(),
      deltaDeg: (json['delta_deg'] as num).toDouble(),
      status: json['status'] as String,
      cue: json['cue'] as String,
      source: json['source'] as String? ?? '',
    );

Map<String, dynamic> _$$CoachingFeedbackItemImplToJson(
        _$CoachingFeedbackItemImpl instance) =>
    <String, dynamic>{
      'variable': instance.variable,
      'label': instance.label,
      'measured_deg': instance.measuredDeg,
      'target_deg': instance.targetDeg,
      'target_range_min_deg': instance.targetRangeMinDeg,
      'target_range_max_deg': instance.targetRangeMaxDeg,
      'delta_deg': instance.deltaDeg,
      'status': instance.status,
      'cue': instance.cue,
      'source': instance.source,
    };
