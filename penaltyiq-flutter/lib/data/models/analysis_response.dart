import 'package:freezed_annotation/freezed_annotation.dart';

part 'analysis_response.freezed.dart';
part 'analysis_response.g.dart';

@freezed
class AnalysisResponse with _$AnalysisResponse {
  const factory AnalysisResponse({
    @JsonKey(name: 'session_id')  required String sessionId,
    @JsonKey(name: 'goal_zone')   required String goalZone,
    required PhysicsResult physics,
    @JsonKey(name: 'ik_result')   IkResult? ikResult,
    @JsonKey(name: 'digital_twin') DigitalTwinResult? digitalTwin,
    @JsonKey(name: 'player_score') PlayerScore? playerScore,
    @JsonKey(name: 'coaching_feedback')
    @Default([]) List<CoachingFeedbackItem> coachingFeedback,
    @JsonKey(name: 'pipeline_warnings')
    @Default([]) List<String> pipelineWarnings,
  }) = _AnalysisResponse;

  factory AnalysisResponse.fromJson(Map<String, dynamic> json) =>
      _$AnalysisResponseFromJson(json);
}

@freezed
class PlayerScore with _$PlayerScore {
  const factory PlayerScore({
    @Default(0) int score,
    @Default('Beginner') String level,
    @Default({}) Map<String, int> breakdown,
  }) = _PlayerScore;

  factory PlayerScore.fromJson(Map<String, dynamic> json) =>
      _$PlayerScoreFromJson(json);
}

@freezed
class PhysicsResult with _$PhysicsResult {
  const factory PhysicsResult({
    @JsonKey(name: 'v0_measured_ms')      required double v0MeasuredMs,
    @JsonKey(name: 'theta_v_deg')         required double thetaVDeg,
    @JsonKey(name: 'theta_h_deg')         required double thetaHDeg,
    @JsonKey(name: 'speed_regime')        required String speedRegime,
    required String feasibility,
    @JsonKey(name: 'crossbar_clearance_m') required double crossbarClearanceM,
    @JsonKey(name: 'safety_margin_satisfied') required bool safetyMarginSatisfied,
  }) = _PhysicsResult;

  factory PhysicsResult.fromJson(Map<String, dynamic> json) =>
      _$PhysicsResultFromJson(json);
}

@freezed
class IkResult with _$IkResult {
  const factory IkResult({
    @JsonKey(name: 'hip_flexion_deg')           required double hipFlexionDeg,
    @JsonKey(name: 'knee_angle_deg')            required double kneeAngleDeg,
    @JsonKey(name: 'ankle_plantarflexion_deg')  required double anklePlantarflexionDeg,
    @JsonKey(name: 'support_leg_knee_deg')      required double supportLegKneeDeg,
    @JsonKey(name: 'trunk_inclination_deg')     required double trunkInclinationDeg,
    @JsonKey(name: 'solver_converged')          required bool solverConverged,
    required double residual,
  }) = _IkResult;

  factory IkResult.fromJson(Map<String, dynamic> json) =>
      _$IkResultFromJson(json);
}

@freezed
class DigitalTwinResult with _$DigitalTwinResult {
  const factory DigitalTwinResult({
    @JsonKey(name: 'predicted_x_m')       required double predictedXM,
    @JsonKey(name: 'predicted_y_m')       required double predictedYM,
    @JsonKey(name: 'zone_hit')            required String zoneHit,
    @JsonKey(name: 'verification_passed') required bool verificationPassed,
    @JsonKey(name: 'x_error_m')           required double xErrorM,
    @JsonKey(name: 'y_error_m')           required double yErrorM,
  }) = _DigitalTwinResult;

  factory DigitalTwinResult.fromJson(Map<String, dynamic> json) =>
      _$DigitalTwinResultFromJson(json);
}

@freezed
class CoachingFeedbackItem with _$CoachingFeedbackItem {
  const factory CoachingFeedbackItem({
    required String variable,
    @Default('') String label,
    @JsonKey(name: 'measured_deg')          required double measuredDeg,
    @JsonKey(name: 'target_deg')            required double targetDeg,
    @JsonKey(name: 'target_range_min_deg')  required double targetRangeMinDeg,
    @JsonKey(name: 'target_range_max_deg')  required double targetRangeMaxDeg,
    @JsonKey(name: 'delta_deg')             required double deltaDeg,
    required String status,
    required String cue,
    @Default('') String source,
  }) = _CoachingFeedbackItem;

  factory CoachingFeedbackItem.fromJson(Map<String, dynamic> json) =>
      _$CoachingFeedbackItemFromJson(json);
}