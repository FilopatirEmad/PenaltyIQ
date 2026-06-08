// coverage:ignore-file
// GENERATED CODE - DO NOT MODIFY BY HAND
// ignore_for_file: type=lint
// ignore_for_file: unused_element, deprecated_member_use, deprecated_member_use_from_same_package, use_function_type_syntax_for_parameters, unnecessary_const, avoid_init_to_null, invalid_override_different_default_values_named, prefer_expression_function_bodies, annotate_overrides, invalid_annotation_target, unnecessary_question_mark

part of 'analysis_response.dart';

// **************************************************************************
// FreezedGenerator
// **************************************************************************

T _$identity<T>(T value) => value;

final _privateConstructorUsedError = UnsupportedError(
    'It seems like you constructed your class using `MyClass._()`. This constructor is only meant to be used by freezed and you are not supposed to need it nor use it.\nPlease check the documentation here for more information: https://github.com/rrousselGit/freezed#adding-getters-and-methods-to-our-models');

AnalysisResponse _$AnalysisResponseFromJson(Map<String, dynamic> json) {
  return _AnalysisResponse.fromJson(json);
}

/// @nodoc
mixin _$AnalysisResponse {
  @JsonKey(name: 'session_id')
  String get sessionId => throw _privateConstructorUsedError;
  @JsonKey(name: 'goal_zone')
  String get goalZone => throw _privateConstructorUsedError;
  PhysicsResult get physics => throw _privateConstructorUsedError;
  @JsonKey(name: 'ik_result')
  IkResult? get ikResult => throw _privateConstructorUsedError;
  @JsonKey(name: 'digital_twin')
  DigitalTwinResult? get digitalTwin => throw _privateConstructorUsedError;
  @JsonKey(name: 'player_score')
  PlayerScore? get playerScore => throw _privateConstructorUsedError;
  @JsonKey(name: 'coaching_feedback')
  List<CoachingFeedbackItem> get coachingFeedback =>
      throw _privateConstructorUsedError;
  @JsonKey(name: 'pipeline_warnings')
  List<String> get pipelineWarnings => throw _privateConstructorUsedError;

  /// Serializes this AnalysisResponse to a JSON map.
  Map<String, dynamic> toJson() => throw _privateConstructorUsedError;

  /// Create a copy of AnalysisResponse
  /// with the given fields replaced by the non-null parameter values.
  @JsonKey(includeFromJson: false, includeToJson: false)
  $AnalysisResponseCopyWith<AnalysisResponse> get copyWith =>
      throw _privateConstructorUsedError;
}

/// @nodoc
abstract class $AnalysisResponseCopyWith<$Res> {
  factory $AnalysisResponseCopyWith(
          AnalysisResponse value, $Res Function(AnalysisResponse) then) =
      _$AnalysisResponseCopyWithImpl<$Res, AnalysisResponse>;
  @useResult
  $Res call(
      {@JsonKey(name: 'session_id') String sessionId,
      @JsonKey(name: 'goal_zone') String goalZone,
      PhysicsResult physics,
      @JsonKey(name: 'ik_result') IkResult? ikResult,
      @JsonKey(name: 'digital_twin') DigitalTwinResult? digitalTwin,
      @JsonKey(name: 'player_score') PlayerScore? playerScore,
      @JsonKey(name: 'coaching_feedback')
      List<CoachingFeedbackItem> coachingFeedback,
      @JsonKey(name: 'pipeline_warnings') List<String> pipelineWarnings});

  $PhysicsResultCopyWith<$Res> get physics;
  $IkResultCopyWith<$Res>? get ikResult;
  $DigitalTwinResultCopyWith<$Res>? get digitalTwin;
  $PlayerScoreCopyWith<$Res>? get playerScore;
}

/// @nodoc
class _$AnalysisResponseCopyWithImpl<$Res, $Val extends AnalysisResponse>
    implements $AnalysisResponseCopyWith<$Res> {
  _$AnalysisResponseCopyWithImpl(this._value, this._then);

  // ignore: unused_field
  final $Val _value;
  // ignore: unused_field
  final $Res Function($Val) _then;

  /// Create a copy of AnalysisResponse
  /// with the given fields replaced by the non-null parameter values.
  @pragma('vm:prefer-inline')
  @override
  $Res call({
    Object? sessionId = null,
    Object? goalZone = null,
    Object? physics = null,
    Object? ikResult = freezed,
    Object? digitalTwin = freezed,
    Object? playerScore = freezed,
    Object? coachingFeedback = null,
    Object? pipelineWarnings = null,
  }) {
    return _then(_value.copyWith(
      sessionId: null == sessionId
          ? _value.sessionId
          : sessionId // ignore: cast_nullable_to_non_nullable
              as String,
      goalZone: null == goalZone
          ? _value.goalZone
          : goalZone // ignore: cast_nullable_to_non_nullable
              as String,
      physics: null == physics
          ? _value.physics
          : physics // ignore: cast_nullable_to_non_nullable
              as PhysicsResult,
      ikResult: freezed == ikResult
          ? _value.ikResult
          : ikResult // ignore: cast_nullable_to_non_nullable
              as IkResult?,
      digitalTwin: freezed == digitalTwin
          ? _value.digitalTwin
          : digitalTwin // ignore: cast_nullable_to_non_nullable
              as DigitalTwinResult?,
      playerScore: freezed == playerScore
          ? _value.playerScore
          : playerScore // ignore: cast_nullable_to_non_nullable
              as PlayerScore?,
      coachingFeedback: null == coachingFeedback
          ? _value.coachingFeedback
          : coachingFeedback // ignore: cast_nullable_to_non_nullable
              as List<CoachingFeedbackItem>,
      pipelineWarnings: null == pipelineWarnings
          ? _value.pipelineWarnings
          : pipelineWarnings // ignore: cast_nullable_to_non_nullable
              as List<String>,
    ) as $Val);
  }

  /// Create a copy of AnalysisResponse
  /// with the given fields replaced by the non-null parameter values.
  @override
  @pragma('vm:prefer-inline')
  $PhysicsResultCopyWith<$Res> get physics {
    return $PhysicsResultCopyWith<$Res>(_value.physics, (value) {
      return _then(_value.copyWith(physics: value) as $Val);
    });
  }

  /// Create a copy of AnalysisResponse
  /// with the given fields replaced by the non-null parameter values.
  @override
  @pragma('vm:prefer-inline')
  $IkResultCopyWith<$Res>? get ikResult {
    if (_value.ikResult == null) {
      return null;
    }

    return $IkResultCopyWith<$Res>(_value.ikResult!, (value) {
      return _then(_value.copyWith(ikResult: value) as $Val);
    });
  }

  /// Create a copy of AnalysisResponse
  /// with the given fields replaced by the non-null parameter values.
  @override
  @pragma('vm:prefer-inline')
  $DigitalTwinResultCopyWith<$Res>? get digitalTwin {
    if (_value.digitalTwin == null) {
      return null;
    }

    return $DigitalTwinResultCopyWith<$Res>(_value.digitalTwin!, (value) {
      return _then(_value.copyWith(digitalTwin: value) as $Val);
    });
  }

  /// Create a copy of AnalysisResponse
  /// with the given fields replaced by the non-null parameter values.
  @override
  @pragma('vm:prefer-inline')
  $PlayerScoreCopyWith<$Res>? get playerScore {
    if (_value.playerScore == null) {
      return null;
    }

    return $PlayerScoreCopyWith<$Res>(_value.playerScore!, (value) {
      return _then(_value.copyWith(playerScore: value) as $Val);
    });
  }
}

/// @nodoc
abstract class _$$AnalysisResponseImplCopyWith<$Res>
    implements $AnalysisResponseCopyWith<$Res> {
  factory _$$AnalysisResponseImplCopyWith(_$AnalysisResponseImpl value,
          $Res Function(_$AnalysisResponseImpl) then) =
      __$$AnalysisResponseImplCopyWithImpl<$Res>;
  @override
  @useResult
  $Res call(
      {@JsonKey(name: 'session_id') String sessionId,
      @JsonKey(name: 'goal_zone') String goalZone,
      PhysicsResult physics,
      @JsonKey(name: 'ik_result') IkResult? ikResult,
      @JsonKey(name: 'digital_twin') DigitalTwinResult? digitalTwin,
      @JsonKey(name: 'player_score') PlayerScore? playerScore,
      @JsonKey(name: 'coaching_feedback')
      List<CoachingFeedbackItem> coachingFeedback,
      @JsonKey(name: 'pipeline_warnings') List<String> pipelineWarnings});

  @override
  $PhysicsResultCopyWith<$Res> get physics;
  @override
  $IkResultCopyWith<$Res>? get ikResult;
  @override
  $DigitalTwinResultCopyWith<$Res>? get digitalTwin;
  @override
  $PlayerScoreCopyWith<$Res>? get playerScore;
}

/// @nodoc
class __$$AnalysisResponseImplCopyWithImpl<$Res>
    extends _$AnalysisResponseCopyWithImpl<$Res, _$AnalysisResponseImpl>
    implements _$$AnalysisResponseImplCopyWith<$Res> {
  __$$AnalysisResponseImplCopyWithImpl(_$AnalysisResponseImpl _value,
      $Res Function(_$AnalysisResponseImpl) _then)
      : super(_value, _then);

  /// Create a copy of AnalysisResponse
  /// with the given fields replaced by the non-null parameter values.
  @pragma('vm:prefer-inline')
  @override
  $Res call({
    Object? sessionId = null,
    Object? goalZone = null,
    Object? physics = null,
    Object? ikResult = freezed,
    Object? digitalTwin = freezed,
    Object? playerScore = freezed,
    Object? coachingFeedback = null,
    Object? pipelineWarnings = null,
  }) {
    return _then(_$AnalysisResponseImpl(
      sessionId: null == sessionId
          ? _value.sessionId
          : sessionId // ignore: cast_nullable_to_non_nullable
              as String,
      goalZone: null == goalZone
          ? _value.goalZone
          : goalZone // ignore: cast_nullable_to_non_nullable
              as String,
      physics: null == physics
          ? _value.physics
          : physics // ignore: cast_nullable_to_non_nullable
              as PhysicsResult,
      ikResult: freezed == ikResult
          ? _value.ikResult
          : ikResult // ignore: cast_nullable_to_non_nullable
              as IkResult?,
      digitalTwin: freezed == digitalTwin
          ? _value.digitalTwin
          : digitalTwin // ignore: cast_nullable_to_non_nullable
              as DigitalTwinResult?,
      playerScore: freezed == playerScore
          ? _value.playerScore
          : playerScore // ignore: cast_nullable_to_non_nullable
              as PlayerScore?,
      coachingFeedback: null == coachingFeedback
          ? _value._coachingFeedback
          : coachingFeedback // ignore: cast_nullable_to_non_nullable
              as List<CoachingFeedbackItem>,
      pipelineWarnings: null == pipelineWarnings
          ? _value._pipelineWarnings
          : pipelineWarnings // ignore: cast_nullable_to_non_nullable
              as List<String>,
    ));
  }
}

/// @nodoc
@JsonSerializable()
class _$AnalysisResponseImpl implements _AnalysisResponse {
  const _$AnalysisResponseImpl(
      {@JsonKey(name: 'session_id') required this.sessionId,
      @JsonKey(name: 'goal_zone') required this.goalZone,
      required this.physics,
      @JsonKey(name: 'ik_result') this.ikResult,
      @JsonKey(name: 'digital_twin') this.digitalTwin,
      @JsonKey(name: 'player_score') this.playerScore,
      @JsonKey(name: 'coaching_feedback')
      final List<CoachingFeedbackItem> coachingFeedback = const [],
      @JsonKey(name: 'pipeline_warnings')
      final List<String> pipelineWarnings = const []})
      : _coachingFeedback = coachingFeedback,
        _pipelineWarnings = pipelineWarnings;

  factory _$AnalysisResponseImpl.fromJson(Map<String, dynamic> json) =>
      _$$AnalysisResponseImplFromJson(json);

  @override
  @JsonKey(name: 'session_id')
  final String sessionId;
  @override
  @JsonKey(name: 'goal_zone')
  final String goalZone;
  @override
  final PhysicsResult physics;
  @override
  @JsonKey(name: 'ik_result')
  final IkResult? ikResult;
  @override
  @JsonKey(name: 'digital_twin')
  final DigitalTwinResult? digitalTwin;
  @override
  @JsonKey(name: 'player_score')
  final PlayerScore? playerScore;
  final List<CoachingFeedbackItem> _coachingFeedback;
  @override
  @JsonKey(name: 'coaching_feedback')
  List<CoachingFeedbackItem> get coachingFeedback {
    if (_coachingFeedback is EqualUnmodifiableListView)
      return _coachingFeedback;
    // ignore: implicit_dynamic_type
    return EqualUnmodifiableListView(_coachingFeedback);
  }

  final List<String> _pipelineWarnings;
  @override
  @JsonKey(name: 'pipeline_warnings')
  List<String> get pipelineWarnings {
    if (_pipelineWarnings is EqualUnmodifiableListView)
      return _pipelineWarnings;
    // ignore: implicit_dynamic_type
    return EqualUnmodifiableListView(_pipelineWarnings);
  }

  @override
  String toString() {
    return 'AnalysisResponse(sessionId: $sessionId, goalZone: $goalZone, physics: $physics, ikResult: $ikResult, digitalTwin: $digitalTwin, playerScore: $playerScore, coachingFeedback: $coachingFeedback, pipelineWarnings: $pipelineWarnings)';
  }

  @override
  bool operator ==(Object other) {
    return identical(this, other) ||
        (other.runtimeType == runtimeType &&
            other is _$AnalysisResponseImpl &&
            (identical(other.sessionId, sessionId) ||
                other.sessionId == sessionId) &&
            (identical(other.goalZone, goalZone) ||
                other.goalZone == goalZone) &&
            (identical(other.physics, physics) || other.physics == physics) &&
            (identical(other.ikResult, ikResult) ||
                other.ikResult == ikResult) &&
            (identical(other.digitalTwin, digitalTwin) ||
                other.digitalTwin == digitalTwin) &&
            (identical(other.playerScore, playerScore) ||
                other.playerScore == playerScore) &&
            const DeepCollectionEquality()
                .equals(other._coachingFeedback, _coachingFeedback) &&
            const DeepCollectionEquality()
                .equals(other._pipelineWarnings, _pipelineWarnings));
  }

  @JsonKey(includeFromJson: false, includeToJson: false)
  @override
  int get hashCode => Object.hash(
      runtimeType,
      sessionId,
      goalZone,
      physics,
      ikResult,
      digitalTwin,
      playerScore,
      const DeepCollectionEquality().hash(_coachingFeedback),
      const DeepCollectionEquality().hash(_pipelineWarnings));

  /// Create a copy of AnalysisResponse
  /// with the given fields replaced by the non-null parameter values.
  @JsonKey(includeFromJson: false, includeToJson: false)
  @override
  @pragma('vm:prefer-inline')
  _$$AnalysisResponseImplCopyWith<_$AnalysisResponseImpl> get copyWith =>
      __$$AnalysisResponseImplCopyWithImpl<_$AnalysisResponseImpl>(
          this, _$identity);

  @override
  Map<String, dynamic> toJson() {
    return _$$AnalysisResponseImplToJson(
      this,
    );
  }
}

abstract class _AnalysisResponse implements AnalysisResponse {
  const factory _AnalysisResponse(
      {@JsonKey(name: 'session_id') required final String sessionId,
      @JsonKey(name: 'goal_zone') required final String goalZone,
      required final PhysicsResult physics,
      @JsonKey(name: 'ik_result') final IkResult? ikResult,
      @JsonKey(name: 'digital_twin') final DigitalTwinResult? digitalTwin,
      @JsonKey(name: 'player_score') final PlayerScore? playerScore,
      @JsonKey(name: 'coaching_feedback')
      final List<CoachingFeedbackItem> coachingFeedback,
      @JsonKey(name: 'pipeline_warnings')
      final List<String> pipelineWarnings}) = _$AnalysisResponseImpl;

  factory _AnalysisResponse.fromJson(Map<String, dynamic> json) =
      _$AnalysisResponseImpl.fromJson;

  @override
  @JsonKey(name: 'session_id')
  String get sessionId;
  @override
  @JsonKey(name: 'goal_zone')
  String get goalZone;
  @override
  PhysicsResult get physics;
  @override
  @JsonKey(name: 'ik_result')
  IkResult? get ikResult;
  @override
  @JsonKey(name: 'digital_twin')
  DigitalTwinResult? get digitalTwin;
  @override
  @JsonKey(name: 'player_score')
  PlayerScore? get playerScore;
  @override
  @JsonKey(name: 'coaching_feedback')
  List<CoachingFeedbackItem> get coachingFeedback;
  @override
  @JsonKey(name: 'pipeline_warnings')
  List<String> get pipelineWarnings;

  /// Create a copy of AnalysisResponse
  /// with the given fields replaced by the non-null parameter values.
  @override
  @JsonKey(includeFromJson: false, includeToJson: false)
  _$$AnalysisResponseImplCopyWith<_$AnalysisResponseImpl> get copyWith =>
      throw _privateConstructorUsedError;
}

PlayerScore _$PlayerScoreFromJson(Map<String, dynamic> json) {
  return _PlayerScore.fromJson(json);
}

/// @nodoc
mixin _$PlayerScore {
  int get score => throw _privateConstructorUsedError;
  String get level => throw _privateConstructorUsedError;
  Map<String, int> get breakdown => throw _privateConstructorUsedError;

  /// Serializes this PlayerScore to a JSON map.
  Map<String, dynamic> toJson() => throw _privateConstructorUsedError;

  /// Create a copy of PlayerScore
  /// with the given fields replaced by the non-null parameter values.
  @JsonKey(includeFromJson: false, includeToJson: false)
  $PlayerScoreCopyWith<PlayerScore> get copyWith =>
      throw _privateConstructorUsedError;
}

/// @nodoc
abstract class $PlayerScoreCopyWith<$Res> {
  factory $PlayerScoreCopyWith(
          PlayerScore value, $Res Function(PlayerScore) then) =
      _$PlayerScoreCopyWithImpl<$Res, PlayerScore>;
  @useResult
  $Res call({int score, String level, Map<String, int> breakdown});
}

/// @nodoc
class _$PlayerScoreCopyWithImpl<$Res, $Val extends PlayerScore>
    implements $PlayerScoreCopyWith<$Res> {
  _$PlayerScoreCopyWithImpl(this._value, this._then);

  // ignore: unused_field
  final $Val _value;
  // ignore: unused_field
  final $Res Function($Val) _then;

  /// Create a copy of PlayerScore
  /// with the given fields replaced by the non-null parameter values.
  @pragma('vm:prefer-inline')
  @override
  $Res call({
    Object? score = null,
    Object? level = null,
    Object? breakdown = null,
  }) {
    return _then(_value.copyWith(
      score: null == score
          ? _value.score
          : score // ignore: cast_nullable_to_non_nullable
              as int,
      level: null == level
          ? _value.level
          : level // ignore: cast_nullable_to_non_nullable
              as String,
      breakdown: null == breakdown
          ? _value.breakdown
          : breakdown // ignore: cast_nullable_to_non_nullable
              as Map<String, int>,
    ) as $Val);
  }
}

/// @nodoc
abstract class _$$PlayerScoreImplCopyWith<$Res>
    implements $PlayerScoreCopyWith<$Res> {
  factory _$$PlayerScoreImplCopyWith(
          _$PlayerScoreImpl value, $Res Function(_$PlayerScoreImpl) then) =
      __$$PlayerScoreImplCopyWithImpl<$Res>;
  @override
  @useResult
  $Res call({int score, String level, Map<String, int> breakdown});
}

/// @nodoc
class __$$PlayerScoreImplCopyWithImpl<$Res>
    extends _$PlayerScoreCopyWithImpl<$Res, _$PlayerScoreImpl>
    implements _$$PlayerScoreImplCopyWith<$Res> {
  __$$PlayerScoreImplCopyWithImpl(
      _$PlayerScoreImpl _value, $Res Function(_$PlayerScoreImpl) _then)
      : super(_value, _then);

  /// Create a copy of PlayerScore
  /// with the given fields replaced by the non-null parameter values.
  @pragma('vm:prefer-inline')
  @override
  $Res call({
    Object? score = null,
    Object? level = null,
    Object? breakdown = null,
  }) {
    return _then(_$PlayerScoreImpl(
      score: null == score
          ? _value.score
          : score // ignore: cast_nullable_to_non_nullable
              as int,
      level: null == level
          ? _value.level
          : level // ignore: cast_nullable_to_non_nullable
              as String,
      breakdown: null == breakdown
          ? _value._breakdown
          : breakdown // ignore: cast_nullable_to_non_nullable
              as Map<String, int>,
    ));
  }
}

/// @nodoc
@JsonSerializable()
class _$PlayerScoreImpl implements _PlayerScore {
  const _$PlayerScoreImpl(
      {this.score = 0,
      this.level = 'Beginner',
      final Map<String, int> breakdown = const {}})
      : _breakdown = breakdown;

  factory _$PlayerScoreImpl.fromJson(Map<String, dynamic> json) =>
      _$$PlayerScoreImplFromJson(json);

  @override
  @JsonKey()
  final int score;
  @override
  @JsonKey()
  final String level;
  final Map<String, int> _breakdown;
  @override
  @JsonKey()
  Map<String, int> get breakdown {
    if (_breakdown is EqualUnmodifiableMapView) return _breakdown;
    // ignore: implicit_dynamic_type
    return EqualUnmodifiableMapView(_breakdown);
  }

  @override
  String toString() {
    return 'PlayerScore(score: $score, level: $level, breakdown: $breakdown)';
  }

  @override
  bool operator ==(Object other) {
    return identical(this, other) ||
        (other.runtimeType == runtimeType &&
            other is _$PlayerScoreImpl &&
            (identical(other.score, score) || other.score == score) &&
            (identical(other.level, level) || other.level == level) &&
            const DeepCollectionEquality()
                .equals(other._breakdown, _breakdown));
  }

  @JsonKey(includeFromJson: false, includeToJson: false)
  @override
  int get hashCode => Object.hash(runtimeType, score, level,
      const DeepCollectionEquality().hash(_breakdown));

  /// Create a copy of PlayerScore
  /// with the given fields replaced by the non-null parameter values.
  @JsonKey(includeFromJson: false, includeToJson: false)
  @override
  @pragma('vm:prefer-inline')
  _$$PlayerScoreImplCopyWith<_$PlayerScoreImpl> get copyWith =>
      __$$PlayerScoreImplCopyWithImpl<_$PlayerScoreImpl>(this, _$identity);

  @override
  Map<String, dynamic> toJson() {
    return _$$PlayerScoreImplToJson(
      this,
    );
  }
}

abstract class _PlayerScore implements PlayerScore {
  const factory _PlayerScore(
      {final int score,
      final String level,
      final Map<String, int> breakdown}) = _$PlayerScoreImpl;

  factory _PlayerScore.fromJson(Map<String, dynamic> json) =
      _$PlayerScoreImpl.fromJson;

  @override
  int get score;
  @override
  String get level;
  @override
  Map<String, int> get breakdown;

  /// Create a copy of PlayerScore
  /// with the given fields replaced by the non-null parameter values.
  @override
  @JsonKey(includeFromJson: false, includeToJson: false)
  _$$PlayerScoreImplCopyWith<_$PlayerScoreImpl> get copyWith =>
      throw _privateConstructorUsedError;
}

PhysicsResult _$PhysicsResultFromJson(Map<String, dynamic> json) {
  return _PhysicsResult.fromJson(json);
}

/// @nodoc
mixin _$PhysicsResult {
  @JsonKey(name: 'v0_measured_ms')
  double get v0MeasuredMs => throw _privateConstructorUsedError;
  @JsonKey(name: 'theta_v_deg')
  double get thetaVDeg => throw _privateConstructorUsedError;
  @JsonKey(name: 'theta_h_deg')
  double get thetaHDeg => throw _privateConstructorUsedError;
  @JsonKey(name: 'speed_regime')
  String get speedRegime => throw _privateConstructorUsedError;
  String get feasibility => throw _privateConstructorUsedError;
  @JsonKey(name: 'crossbar_clearance_m')
  double get crossbarClearanceM => throw _privateConstructorUsedError;
  @JsonKey(name: 'safety_margin_satisfied')
  bool get safetyMarginSatisfied => throw _privateConstructorUsedError;

  /// Serializes this PhysicsResult to a JSON map.
  Map<String, dynamic> toJson() => throw _privateConstructorUsedError;

  /// Create a copy of PhysicsResult
  /// with the given fields replaced by the non-null parameter values.
  @JsonKey(includeFromJson: false, includeToJson: false)
  $PhysicsResultCopyWith<PhysicsResult> get copyWith =>
      throw _privateConstructorUsedError;
}

/// @nodoc
abstract class $PhysicsResultCopyWith<$Res> {
  factory $PhysicsResultCopyWith(
          PhysicsResult value, $Res Function(PhysicsResult) then) =
      _$PhysicsResultCopyWithImpl<$Res, PhysicsResult>;
  @useResult
  $Res call(
      {@JsonKey(name: 'v0_measured_ms') double v0MeasuredMs,
      @JsonKey(name: 'theta_v_deg') double thetaVDeg,
      @JsonKey(name: 'theta_h_deg') double thetaHDeg,
      @JsonKey(name: 'speed_regime') String speedRegime,
      String feasibility,
      @JsonKey(name: 'crossbar_clearance_m') double crossbarClearanceM,
      @JsonKey(name: 'safety_margin_satisfied') bool safetyMarginSatisfied});
}

/// @nodoc
class _$PhysicsResultCopyWithImpl<$Res, $Val extends PhysicsResult>
    implements $PhysicsResultCopyWith<$Res> {
  _$PhysicsResultCopyWithImpl(this._value, this._then);

  // ignore: unused_field
  final $Val _value;
  // ignore: unused_field
  final $Res Function($Val) _then;

  /// Create a copy of PhysicsResult
  /// with the given fields replaced by the non-null parameter values.
  @pragma('vm:prefer-inline')
  @override
  $Res call({
    Object? v0MeasuredMs = null,
    Object? thetaVDeg = null,
    Object? thetaHDeg = null,
    Object? speedRegime = null,
    Object? feasibility = null,
    Object? crossbarClearanceM = null,
    Object? safetyMarginSatisfied = null,
  }) {
    return _then(_value.copyWith(
      v0MeasuredMs: null == v0MeasuredMs
          ? _value.v0MeasuredMs
          : v0MeasuredMs // ignore: cast_nullable_to_non_nullable
              as double,
      thetaVDeg: null == thetaVDeg
          ? _value.thetaVDeg
          : thetaVDeg // ignore: cast_nullable_to_non_nullable
              as double,
      thetaHDeg: null == thetaHDeg
          ? _value.thetaHDeg
          : thetaHDeg // ignore: cast_nullable_to_non_nullable
              as double,
      speedRegime: null == speedRegime
          ? _value.speedRegime
          : speedRegime // ignore: cast_nullable_to_non_nullable
              as String,
      feasibility: null == feasibility
          ? _value.feasibility
          : feasibility // ignore: cast_nullable_to_non_nullable
              as String,
      crossbarClearanceM: null == crossbarClearanceM
          ? _value.crossbarClearanceM
          : crossbarClearanceM // ignore: cast_nullable_to_non_nullable
              as double,
      safetyMarginSatisfied: null == safetyMarginSatisfied
          ? _value.safetyMarginSatisfied
          : safetyMarginSatisfied // ignore: cast_nullable_to_non_nullable
              as bool,
    ) as $Val);
  }
}

/// @nodoc
abstract class _$$PhysicsResultImplCopyWith<$Res>
    implements $PhysicsResultCopyWith<$Res> {
  factory _$$PhysicsResultImplCopyWith(
          _$PhysicsResultImpl value, $Res Function(_$PhysicsResultImpl) then) =
      __$$PhysicsResultImplCopyWithImpl<$Res>;
  @override
  @useResult
  $Res call(
      {@JsonKey(name: 'v0_measured_ms') double v0MeasuredMs,
      @JsonKey(name: 'theta_v_deg') double thetaVDeg,
      @JsonKey(name: 'theta_h_deg') double thetaHDeg,
      @JsonKey(name: 'speed_regime') String speedRegime,
      String feasibility,
      @JsonKey(name: 'crossbar_clearance_m') double crossbarClearanceM,
      @JsonKey(name: 'safety_margin_satisfied') bool safetyMarginSatisfied});
}

/// @nodoc
class __$$PhysicsResultImplCopyWithImpl<$Res>
    extends _$PhysicsResultCopyWithImpl<$Res, _$PhysicsResultImpl>
    implements _$$PhysicsResultImplCopyWith<$Res> {
  __$$PhysicsResultImplCopyWithImpl(
      _$PhysicsResultImpl _value, $Res Function(_$PhysicsResultImpl) _then)
      : super(_value, _then);

  /// Create a copy of PhysicsResult
  /// with the given fields replaced by the non-null parameter values.
  @pragma('vm:prefer-inline')
  @override
  $Res call({
    Object? v0MeasuredMs = null,
    Object? thetaVDeg = null,
    Object? thetaHDeg = null,
    Object? speedRegime = null,
    Object? feasibility = null,
    Object? crossbarClearanceM = null,
    Object? safetyMarginSatisfied = null,
  }) {
    return _then(_$PhysicsResultImpl(
      v0MeasuredMs: null == v0MeasuredMs
          ? _value.v0MeasuredMs
          : v0MeasuredMs // ignore: cast_nullable_to_non_nullable
              as double,
      thetaVDeg: null == thetaVDeg
          ? _value.thetaVDeg
          : thetaVDeg // ignore: cast_nullable_to_non_nullable
              as double,
      thetaHDeg: null == thetaHDeg
          ? _value.thetaHDeg
          : thetaHDeg // ignore: cast_nullable_to_non_nullable
              as double,
      speedRegime: null == speedRegime
          ? _value.speedRegime
          : speedRegime // ignore: cast_nullable_to_non_nullable
              as String,
      feasibility: null == feasibility
          ? _value.feasibility
          : feasibility // ignore: cast_nullable_to_non_nullable
              as String,
      crossbarClearanceM: null == crossbarClearanceM
          ? _value.crossbarClearanceM
          : crossbarClearanceM // ignore: cast_nullable_to_non_nullable
              as double,
      safetyMarginSatisfied: null == safetyMarginSatisfied
          ? _value.safetyMarginSatisfied
          : safetyMarginSatisfied // ignore: cast_nullable_to_non_nullable
              as bool,
    ));
  }
}

/// @nodoc
@JsonSerializable()
class _$PhysicsResultImpl implements _PhysicsResult {
  const _$PhysicsResultImpl(
      {@JsonKey(name: 'v0_measured_ms') required this.v0MeasuredMs,
      @JsonKey(name: 'theta_v_deg') required this.thetaVDeg,
      @JsonKey(name: 'theta_h_deg') required this.thetaHDeg,
      @JsonKey(name: 'speed_regime') required this.speedRegime,
      required this.feasibility,
      @JsonKey(name: 'crossbar_clearance_m') required this.crossbarClearanceM,
      @JsonKey(name: 'safety_margin_satisfied')
      required this.safetyMarginSatisfied});

  factory _$PhysicsResultImpl.fromJson(Map<String, dynamic> json) =>
      _$$PhysicsResultImplFromJson(json);

  @override
  @JsonKey(name: 'v0_measured_ms')
  final double v0MeasuredMs;
  @override
  @JsonKey(name: 'theta_v_deg')
  final double thetaVDeg;
  @override
  @JsonKey(name: 'theta_h_deg')
  final double thetaHDeg;
  @override
  @JsonKey(name: 'speed_regime')
  final String speedRegime;
  @override
  final String feasibility;
  @override
  @JsonKey(name: 'crossbar_clearance_m')
  final double crossbarClearanceM;
  @override
  @JsonKey(name: 'safety_margin_satisfied')
  final bool safetyMarginSatisfied;

  @override
  String toString() {
    return 'PhysicsResult(v0MeasuredMs: $v0MeasuredMs, thetaVDeg: $thetaVDeg, thetaHDeg: $thetaHDeg, speedRegime: $speedRegime, feasibility: $feasibility, crossbarClearanceM: $crossbarClearanceM, safetyMarginSatisfied: $safetyMarginSatisfied)';
  }

  @override
  bool operator ==(Object other) {
    return identical(this, other) ||
        (other.runtimeType == runtimeType &&
            other is _$PhysicsResultImpl &&
            (identical(other.v0MeasuredMs, v0MeasuredMs) ||
                other.v0MeasuredMs == v0MeasuredMs) &&
            (identical(other.thetaVDeg, thetaVDeg) ||
                other.thetaVDeg == thetaVDeg) &&
            (identical(other.thetaHDeg, thetaHDeg) ||
                other.thetaHDeg == thetaHDeg) &&
            (identical(other.speedRegime, speedRegime) ||
                other.speedRegime == speedRegime) &&
            (identical(other.feasibility, feasibility) ||
                other.feasibility == feasibility) &&
            (identical(other.crossbarClearanceM, crossbarClearanceM) ||
                other.crossbarClearanceM == crossbarClearanceM) &&
            (identical(other.safetyMarginSatisfied, safetyMarginSatisfied) ||
                other.safetyMarginSatisfied == safetyMarginSatisfied));
  }

  @JsonKey(includeFromJson: false, includeToJson: false)
  @override
  int get hashCode => Object.hash(
      runtimeType,
      v0MeasuredMs,
      thetaVDeg,
      thetaHDeg,
      speedRegime,
      feasibility,
      crossbarClearanceM,
      safetyMarginSatisfied);

  /// Create a copy of PhysicsResult
  /// with the given fields replaced by the non-null parameter values.
  @JsonKey(includeFromJson: false, includeToJson: false)
  @override
  @pragma('vm:prefer-inline')
  _$$PhysicsResultImplCopyWith<_$PhysicsResultImpl> get copyWith =>
      __$$PhysicsResultImplCopyWithImpl<_$PhysicsResultImpl>(this, _$identity);

  @override
  Map<String, dynamic> toJson() {
    return _$$PhysicsResultImplToJson(
      this,
    );
  }
}

abstract class _PhysicsResult implements PhysicsResult {
  const factory _PhysicsResult(
      {@JsonKey(name: 'v0_measured_ms') required final double v0MeasuredMs,
      @JsonKey(name: 'theta_v_deg') required final double thetaVDeg,
      @JsonKey(name: 'theta_h_deg') required final double thetaHDeg,
      @JsonKey(name: 'speed_regime') required final String speedRegime,
      required final String feasibility,
      @JsonKey(name: 'crossbar_clearance_m')
      required final double crossbarClearanceM,
      @JsonKey(name: 'safety_margin_satisfied')
      required final bool safetyMarginSatisfied}) = _$PhysicsResultImpl;

  factory _PhysicsResult.fromJson(Map<String, dynamic> json) =
      _$PhysicsResultImpl.fromJson;

  @override
  @JsonKey(name: 'v0_measured_ms')
  double get v0MeasuredMs;
  @override
  @JsonKey(name: 'theta_v_deg')
  double get thetaVDeg;
  @override
  @JsonKey(name: 'theta_h_deg')
  double get thetaHDeg;
  @override
  @JsonKey(name: 'speed_regime')
  String get speedRegime;
  @override
  String get feasibility;
  @override
  @JsonKey(name: 'crossbar_clearance_m')
  double get crossbarClearanceM;
  @override
  @JsonKey(name: 'safety_margin_satisfied')
  bool get safetyMarginSatisfied;

  /// Create a copy of PhysicsResult
  /// with the given fields replaced by the non-null parameter values.
  @override
  @JsonKey(includeFromJson: false, includeToJson: false)
  _$$PhysicsResultImplCopyWith<_$PhysicsResultImpl> get copyWith =>
      throw _privateConstructorUsedError;
}

IkResult _$IkResultFromJson(Map<String, dynamic> json) {
  return _IkResult.fromJson(json);
}

/// @nodoc
mixin _$IkResult {
  @JsonKey(name: 'hip_flexion_deg')
  double get hipFlexionDeg => throw _privateConstructorUsedError;
  @JsonKey(name: 'knee_angle_deg')
  double get kneeAngleDeg => throw _privateConstructorUsedError;
  @JsonKey(name: 'ankle_plantarflexion_deg')
  double get anklePlantarflexionDeg => throw _privateConstructorUsedError;
  @JsonKey(name: 'support_leg_knee_deg')
  double get supportLegKneeDeg => throw _privateConstructorUsedError;
  @JsonKey(name: 'trunk_inclination_deg')
  double get trunkInclinationDeg => throw _privateConstructorUsedError;
  @JsonKey(name: 'solver_converged')
  bool get solverConverged => throw _privateConstructorUsedError;
  double get residual => throw _privateConstructorUsedError;

  /// Serializes this IkResult to a JSON map.
  Map<String, dynamic> toJson() => throw _privateConstructorUsedError;

  /// Create a copy of IkResult
  /// with the given fields replaced by the non-null parameter values.
  @JsonKey(includeFromJson: false, includeToJson: false)
  $IkResultCopyWith<IkResult> get copyWith =>
      throw _privateConstructorUsedError;
}

/// @nodoc
abstract class $IkResultCopyWith<$Res> {
  factory $IkResultCopyWith(IkResult value, $Res Function(IkResult) then) =
      _$IkResultCopyWithImpl<$Res, IkResult>;
  @useResult
  $Res call(
      {@JsonKey(name: 'hip_flexion_deg') double hipFlexionDeg,
      @JsonKey(name: 'knee_angle_deg') double kneeAngleDeg,
      @JsonKey(name: 'ankle_plantarflexion_deg') double anklePlantarflexionDeg,
      @JsonKey(name: 'support_leg_knee_deg') double supportLegKneeDeg,
      @JsonKey(name: 'trunk_inclination_deg') double trunkInclinationDeg,
      @JsonKey(name: 'solver_converged') bool solverConverged,
      double residual});
}

/// @nodoc
class _$IkResultCopyWithImpl<$Res, $Val extends IkResult>
    implements $IkResultCopyWith<$Res> {
  _$IkResultCopyWithImpl(this._value, this._then);

  // ignore: unused_field
  final $Val _value;
  // ignore: unused_field
  final $Res Function($Val) _then;

  /// Create a copy of IkResult
  /// with the given fields replaced by the non-null parameter values.
  @pragma('vm:prefer-inline')
  @override
  $Res call({
    Object? hipFlexionDeg = null,
    Object? kneeAngleDeg = null,
    Object? anklePlantarflexionDeg = null,
    Object? supportLegKneeDeg = null,
    Object? trunkInclinationDeg = null,
    Object? solverConverged = null,
    Object? residual = null,
  }) {
    return _then(_value.copyWith(
      hipFlexionDeg: null == hipFlexionDeg
          ? _value.hipFlexionDeg
          : hipFlexionDeg // ignore: cast_nullable_to_non_nullable
              as double,
      kneeAngleDeg: null == kneeAngleDeg
          ? _value.kneeAngleDeg
          : kneeAngleDeg // ignore: cast_nullable_to_non_nullable
              as double,
      anklePlantarflexionDeg: null == anklePlantarflexionDeg
          ? _value.anklePlantarflexionDeg
          : anklePlantarflexionDeg // ignore: cast_nullable_to_non_nullable
              as double,
      supportLegKneeDeg: null == supportLegKneeDeg
          ? _value.supportLegKneeDeg
          : supportLegKneeDeg // ignore: cast_nullable_to_non_nullable
              as double,
      trunkInclinationDeg: null == trunkInclinationDeg
          ? _value.trunkInclinationDeg
          : trunkInclinationDeg // ignore: cast_nullable_to_non_nullable
              as double,
      solverConverged: null == solverConverged
          ? _value.solverConverged
          : solverConverged // ignore: cast_nullable_to_non_nullable
              as bool,
      residual: null == residual
          ? _value.residual
          : residual // ignore: cast_nullable_to_non_nullable
              as double,
    ) as $Val);
  }
}

/// @nodoc
abstract class _$$IkResultImplCopyWith<$Res>
    implements $IkResultCopyWith<$Res> {
  factory _$$IkResultImplCopyWith(
          _$IkResultImpl value, $Res Function(_$IkResultImpl) then) =
      __$$IkResultImplCopyWithImpl<$Res>;
  @override
  @useResult
  $Res call(
      {@JsonKey(name: 'hip_flexion_deg') double hipFlexionDeg,
      @JsonKey(name: 'knee_angle_deg') double kneeAngleDeg,
      @JsonKey(name: 'ankle_plantarflexion_deg') double anklePlantarflexionDeg,
      @JsonKey(name: 'support_leg_knee_deg') double supportLegKneeDeg,
      @JsonKey(name: 'trunk_inclination_deg') double trunkInclinationDeg,
      @JsonKey(name: 'solver_converged') bool solverConverged,
      double residual});
}

/// @nodoc
class __$$IkResultImplCopyWithImpl<$Res>
    extends _$IkResultCopyWithImpl<$Res, _$IkResultImpl>
    implements _$$IkResultImplCopyWith<$Res> {
  __$$IkResultImplCopyWithImpl(
      _$IkResultImpl _value, $Res Function(_$IkResultImpl) _then)
      : super(_value, _then);

  /// Create a copy of IkResult
  /// with the given fields replaced by the non-null parameter values.
  @pragma('vm:prefer-inline')
  @override
  $Res call({
    Object? hipFlexionDeg = null,
    Object? kneeAngleDeg = null,
    Object? anklePlantarflexionDeg = null,
    Object? supportLegKneeDeg = null,
    Object? trunkInclinationDeg = null,
    Object? solverConverged = null,
    Object? residual = null,
  }) {
    return _then(_$IkResultImpl(
      hipFlexionDeg: null == hipFlexionDeg
          ? _value.hipFlexionDeg
          : hipFlexionDeg // ignore: cast_nullable_to_non_nullable
              as double,
      kneeAngleDeg: null == kneeAngleDeg
          ? _value.kneeAngleDeg
          : kneeAngleDeg // ignore: cast_nullable_to_non_nullable
              as double,
      anklePlantarflexionDeg: null == anklePlantarflexionDeg
          ? _value.anklePlantarflexionDeg
          : anklePlantarflexionDeg // ignore: cast_nullable_to_non_nullable
              as double,
      supportLegKneeDeg: null == supportLegKneeDeg
          ? _value.supportLegKneeDeg
          : supportLegKneeDeg // ignore: cast_nullable_to_non_nullable
              as double,
      trunkInclinationDeg: null == trunkInclinationDeg
          ? _value.trunkInclinationDeg
          : trunkInclinationDeg // ignore: cast_nullable_to_non_nullable
              as double,
      solverConverged: null == solverConverged
          ? _value.solverConverged
          : solverConverged // ignore: cast_nullable_to_non_nullable
              as bool,
      residual: null == residual
          ? _value.residual
          : residual // ignore: cast_nullable_to_non_nullable
              as double,
    ));
  }
}

/// @nodoc
@JsonSerializable()
class _$IkResultImpl implements _IkResult {
  const _$IkResultImpl(
      {@JsonKey(name: 'hip_flexion_deg') required this.hipFlexionDeg,
      @JsonKey(name: 'knee_angle_deg') required this.kneeAngleDeg,
      @JsonKey(name: 'ankle_plantarflexion_deg')
      required this.anklePlantarflexionDeg,
      @JsonKey(name: 'support_leg_knee_deg') required this.supportLegKneeDeg,
      @JsonKey(name: 'trunk_inclination_deg') required this.trunkInclinationDeg,
      @JsonKey(name: 'solver_converged') required this.solverConverged,
      required this.residual});

  factory _$IkResultImpl.fromJson(Map<String, dynamic> json) =>
      _$$IkResultImplFromJson(json);

  @override
  @JsonKey(name: 'hip_flexion_deg')
  final double hipFlexionDeg;
  @override
  @JsonKey(name: 'knee_angle_deg')
  final double kneeAngleDeg;
  @override
  @JsonKey(name: 'ankle_plantarflexion_deg')
  final double anklePlantarflexionDeg;
  @override
  @JsonKey(name: 'support_leg_knee_deg')
  final double supportLegKneeDeg;
  @override
  @JsonKey(name: 'trunk_inclination_deg')
  final double trunkInclinationDeg;
  @override
  @JsonKey(name: 'solver_converged')
  final bool solverConverged;
  @override
  final double residual;

  @override
  String toString() {
    return 'IkResult(hipFlexionDeg: $hipFlexionDeg, kneeAngleDeg: $kneeAngleDeg, anklePlantarflexionDeg: $anklePlantarflexionDeg, supportLegKneeDeg: $supportLegKneeDeg, trunkInclinationDeg: $trunkInclinationDeg, solverConverged: $solverConverged, residual: $residual)';
  }

  @override
  bool operator ==(Object other) {
    return identical(this, other) ||
        (other.runtimeType == runtimeType &&
            other is _$IkResultImpl &&
            (identical(other.hipFlexionDeg, hipFlexionDeg) ||
                other.hipFlexionDeg == hipFlexionDeg) &&
            (identical(other.kneeAngleDeg, kneeAngleDeg) ||
                other.kneeAngleDeg == kneeAngleDeg) &&
            (identical(other.anklePlantarflexionDeg, anklePlantarflexionDeg) ||
                other.anklePlantarflexionDeg == anklePlantarflexionDeg) &&
            (identical(other.supportLegKneeDeg, supportLegKneeDeg) ||
                other.supportLegKneeDeg == supportLegKneeDeg) &&
            (identical(other.trunkInclinationDeg, trunkInclinationDeg) ||
                other.trunkInclinationDeg == trunkInclinationDeg) &&
            (identical(other.solverConverged, solverConverged) ||
                other.solverConverged == solverConverged) &&
            (identical(other.residual, residual) ||
                other.residual == residual));
  }

  @JsonKey(includeFromJson: false, includeToJson: false)
  @override
  int get hashCode => Object.hash(
      runtimeType,
      hipFlexionDeg,
      kneeAngleDeg,
      anklePlantarflexionDeg,
      supportLegKneeDeg,
      trunkInclinationDeg,
      solverConverged,
      residual);

  /// Create a copy of IkResult
  /// with the given fields replaced by the non-null parameter values.
  @JsonKey(includeFromJson: false, includeToJson: false)
  @override
  @pragma('vm:prefer-inline')
  _$$IkResultImplCopyWith<_$IkResultImpl> get copyWith =>
      __$$IkResultImplCopyWithImpl<_$IkResultImpl>(this, _$identity);

  @override
  Map<String, dynamic> toJson() {
    return _$$IkResultImplToJson(
      this,
    );
  }
}

abstract class _IkResult implements IkResult {
  const factory _IkResult(
      {@JsonKey(name: 'hip_flexion_deg') required final double hipFlexionDeg,
      @JsonKey(name: 'knee_angle_deg') required final double kneeAngleDeg,
      @JsonKey(name: 'ankle_plantarflexion_deg')
      required final double anklePlantarflexionDeg,
      @JsonKey(name: 'support_leg_knee_deg')
      required final double supportLegKneeDeg,
      @JsonKey(name: 'trunk_inclination_deg')
      required final double trunkInclinationDeg,
      @JsonKey(name: 'solver_converged') required final bool solverConverged,
      required final double residual}) = _$IkResultImpl;

  factory _IkResult.fromJson(Map<String, dynamic> json) =
      _$IkResultImpl.fromJson;

  @override
  @JsonKey(name: 'hip_flexion_deg')
  double get hipFlexionDeg;
  @override
  @JsonKey(name: 'knee_angle_deg')
  double get kneeAngleDeg;
  @override
  @JsonKey(name: 'ankle_plantarflexion_deg')
  double get anklePlantarflexionDeg;
  @override
  @JsonKey(name: 'support_leg_knee_deg')
  double get supportLegKneeDeg;
  @override
  @JsonKey(name: 'trunk_inclination_deg')
  double get trunkInclinationDeg;
  @override
  @JsonKey(name: 'solver_converged')
  bool get solverConverged;
  @override
  double get residual;

  /// Create a copy of IkResult
  /// with the given fields replaced by the non-null parameter values.
  @override
  @JsonKey(includeFromJson: false, includeToJson: false)
  _$$IkResultImplCopyWith<_$IkResultImpl> get copyWith =>
      throw _privateConstructorUsedError;
}

DigitalTwinResult _$DigitalTwinResultFromJson(Map<String, dynamic> json) {
  return _DigitalTwinResult.fromJson(json);
}

/// @nodoc
mixin _$DigitalTwinResult {
  @JsonKey(name: 'predicted_x_m')
  double get predictedXM => throw _privateConstructorUsedError;
  @JsonKey(name: 'predicted_y_m')
  double get predictedYM => throw _privateConstructorUsedError;
  @JsonKey(name: 'zone_hit')
  String get zoneHit => throw _privateConstructorUsedError;
  @JsonKey(name: 'verification_passed')
  bool get verificationPassed => throw _privateConstructorUsedError;
  @JsonKey(name: 'x_error_m')
  double get xErrorM => throw _privateConstructorUsedError;
  @JsonKey(name: 'y_error_m')
  double get yErrorM => throw _privateConstructorUsedError;

  /// Serializes this DigitalTwinResult to a JSON map.
  Map<String, dynamic> toJson() => throw _privateConstructorUsedError;

  /// Create a copy of DigitalTwinResult
  /// with the given fields replaced by the non-null parameter values.
  @JsonKey(includeFromJson: false, includeToJson: false)
  $DigitalTwinResultCopyWith<DigitalTwinResult> get copyWith =>
      throw _privateConstructorUsedError;
}

/// @nodoc
abstract class $DigitalTwinResultCopyWith<$Res> {
  factory $DigitalTwinResultCopyWith(
          DigitalTwinResult value, $Res Function(DigitalTwinResult) then) =
      _$DigitalTwinResultCopyWithImpl<$Res, DigitalTwinResult>;
  @useResult
  $Res call(
      {@JsonKey(name: 'predicted_x_m') double predictedXM,
      @JsonKey(name: 'predicted_y_m') double predictedYM,
      @JsonKey(name: 'zone_hit') String zoneHit,
      @JsonKey(name: 'verification_passed') bool verificationPassed,
      @JsonKey(name: 'x_error_m') double xErrorM,
      @JsonKey(name: 'y_error_m') double yErrorM});
}

/// @nodoc
class _$DigitalTwinResultCopyWithImpl<$Res, $Val extends DigitalTwinResult>
    implements $DigitalTwinResultCopyWith<$Res> {
  _$DigitalTwinResultCopyWithImpl(this._value, this._then);

  // ignore: unused_field
  final $Val _value;
  // ignore: unused_field
  final $Res Function($Val) _then;

  /// Create a copy of DigitalTwinResult
  /// with the given fields replaced by the non-null parameter values.
  @pragma('vm:prefer-inline')
  @override
  $Res call({
    Object? predictedXM = null,
    Object? predictedYM = null,
    Object? zoneHit = null,
    Object? verificationPassed = null,
    Object? xErrorM = null,
    Object? yErrorM = null,
  }) {
    return _then(_value.copyWith(
      predictedXM: null == predictedXM
          ? _value.predictedXM
          : predictedXM // ignore: cast_nullable_to_non_nullable
              as double,
      predictedYM: null == predictedYM
          ? _value.predictedYM
          : predictedYM // ignore: cast_nullable_to_non_nullable
              as double,
      zoneHit: null == zoneHit
          ? _value.zoneHit
          : zoneHit // ignore: cast_nullable_to_non_nullable
              as String,
      verificationPassed: null == verificationPassed
          ? _value.verificationPassed
          : verificationPassed // ignore: cast_nullable_to_non_nullable
              as bool,
      xErrorM: null == xErrorM
          ? _value.xErrorM
          : xErrorM // ignore: cast_nullable_to_non_nullable
              as double,
      yErrorM: null == yErrorM
          ? _value.yErrorM
          : yErrorM // ignore: cast_nullable_to_non_nullable
              as double,
    ) as $Val);
  }
}

/// @nodoc
abstract class _$$DigitalTwinResultImplCopyWith<$Res>
    implements $DigitalTwinResultCopyWith<$Res> {
  factory _$$DigitalTwinResultImplCopyWith(_$DigitalTwinResultImpl value,
          $Res Function(_$DigitalTwinResultImpl) then) =
      __$$DigitalTwinResultImplCopyWithImpl<$Res>;
  @override
  @useResult
  $Res call(
      {@JsonKey(name: 'predicted_x_m') double predictedXM,
      @JsonKey(name: 'predicted_y_m') double predictedYM,
      @JsonKey(name: 'zone_hit') String zoneHit,
      @JsonKey(name: 'verification_passed') bool verificationPassed,
      @JsonKey(name: 'x_error_m') double xErrorM,
      @JsonKey(name: 'y_error_m') double yErrorM});
}

/// @nodoc
class __$$DigitalTwinResultImplCopyWithImpl<$Res>
    extends _$DigitalTwinResultCopyWithImpl<$Res, _$DigitalTwinResultImpl>
    implements _$$DigitalTwinResultImplCopyWith<$Res> {
  __$$DigitalTwinResultImplCopyWithImpl(_$DigitalTwinResultImpl _value,
      $Res Function(_$DigitalTwinResultImpl) _then)
      : super(_value, _then);

  /// Create a copy of DigitalTwinResult
  /// with the given fields replaced by the non-null parameter values.
  @pragma('vm:prefer-inline')
  @override
  $Res call({
    Object? predictedXM = null,
    Object? predictedYM = null,
    Object? zoneHit = null,
    Object? verificationPassed = null,
    Object? xErrorM = null,
    Object? yErrorM = null,
  }) {
    return _then(_$DigitalTwinResultImpl(
      predictedXM: null == predictedXM
          ? _value.predictedXM
          : predictedXM // ignore: cast_nullable_to_non_nullable
              as double,
      predictedYM: null == predictedYM
          ? _value.predictedYM
          : predictedYM // ignore: cast_nullable_to_non_nullable
              as double,
      zoneHit: null == zoneHit
          ? _value.zoneHit
          : zoneHit // ignore: cast_nullable_to_non_nullable
              as String,
      verificationPassed: null == verificationPassed
          ? _value.verificationPassed
          : verificationPassed // ignore: cast_nullable_to_non_nullable
              as bool,
      xErrorM: null == xErrorM
          ? _value.xErrorM
          : xErrorM // ignore: cast_nullable_to_non_nullable
              as double,
      yErrorM: null == yErrorM
          ? _value.yErrorM
          : yErrorM // ignore: cast_nullable_to_non_nullable
              as double,
    ));
  }
}

/// @nodoc
@JsonSerializable()
class _$DigitalTwinResultImpl implements _DigitalTwinResult {
  const _$DigitalTwinResultImpl(
      {@JsonKey(name: 'predicted_x_m') required this.predictedXM,
      @JsonKey(name: 'predicted_y_m') required this.predictedYM,
      @JsonKey(name: 'zone_hit') required this.zoneHit,
      @JsonKey(name: 'verification_passed') required this.verificationPassed,
      @JsonKey(name: 'x_error_m') required this.xErrorM,
      @JsonKey(name: 'y_error_m') required this.yErrorM});

  factory _$DigitalTwinResultImpl.fromJson(Map<String, dynamic> json) =>
      _$$DigitalTwinResultImplFromJson(json);

  @override
  @JsonKey(name: 'predicted_x_m')
  final double predictedXM;
  @override
  @JsonKey(name: 'predicted_y_m')
  final double predictedYM;
  @override
  @JsonKey(name: 'zone_hit')
  final String zoneHit;
  @override
  @JsonKey(name: 'verification_passed')
  final bool verificationPassed;
  @override
  @JsonKey(name: 'x_error_m')
  final double xErrorM;
  @override
  @JsonKey(name: 'y_error_m')
  final double yErrorM;

  @override
  String toString() {
    return 'DigitalTwinResult(predictedXM: $predictedXM, predictedYM: $predictedYM, zoneHit: $zoneHit, verificationPassed: $verificationPassed, xErrorM: $xErrorM, yErrorM: $yErrorM)';
  }

  @override
  bool operator ==(Object other) {
    return identical(this, other) ||
        (other.runtimeType == runtimeType &&
            other is _$DigitalTwinResultImpl &&
            (identical(other.predictedXM, predictedXM) ||
                other.predictedXM == predictedXM) &&
            (identical(other.predictedYM, predictedYM) ||
                other.predictedYM == predictedYM) &&
            (identical(other.zoneHit, zoneHit) || other.zoneHit == zoneHit) &&
            (identical(other.verificationPassed, verificationPassed) ||
                other.verificationPassed == verificationPassed) &&
            (identical(other.xErrorM, xErrorM) || other.xErrorM == xErrorM) &&
            (identical(other.yErrorM, yErrorM) || other.yErrorM == yErrorM));
  }

  @JsonKey(includeFromJson: false, includeToJson: false)
  @override
  int get hashCode => Object.hash(runtimeType, predictedXM, predictedYM,
      zoneHit, verificationPassed, xErrorM, yErrorM);

  /// Create a copy of DigitalTwinResult
  /// with the given fields replaced by the non-null parameter values.
  @JsonKey(includeFromJson: false, includeToJson: false)
  @override
  @pragma('vm:prefer-inline')
  _$$DigitalTwinResultImplCopyWith<_$DigitalTwinResultImpl> get copyWith =>
      __$$DigitalTwinResultImplCopyWithImpl<_$DigitalTwinResultImpl>(
          this, _$identity);

  @override
  Map<String, dynamic> toJson() {
    return _$$DigitalTwinResultImplToJson(
      this,
    );
  }
}

abstract class _DigitalTwinResult implements DigitalTwinResult {
  const factory _DigitalTwinResult(
          {@JsonKey(name: 'predicted_x_m') required final double predictedXM,
          @JsonKey(name: 'predicted_y_m') required final double predictedYM,
          @JsonKey(name: 'zone_hit') required final String zoneHit,
          @JsonKey(name: 'verification_passed')
          required final bool verificationPassed,
          @JsonKey(name: 'x_error_m') required final double xErrorM,
          @JsonKey(name: 'y_error_m') required final double yErrorM}) =
      _$DigitalTwinResultImpl;

  factory _DigitalTwinResult.fromJson(Map<String, dynamic> json) =
      _$DigitalTwinResultImpl.fromJson;

  @override
  @JsonKey(name: 'predicted_x_m')
  double get predictedXM;
  @override
  @JsonKey(name: 'predicted_y_m')
  double get predictedYM;
  @override
  @JsonKey(name: 'zone_hit')
  String get zoneHit;
  @override
  @JsonKey(name: 'verification_passed')
  bool get verificationPassed;
  @override
  @JsonKey(name: 'x_error_m')
  double get xErrorM;
  @override
  @JsonKey(name: 'y_error_m')
  double get yErrorM;

  /// Create a copy of DigitalTwinResult
  /// with the given fields replaced by the non-null parameter values.
  @override
  @JsonKey(includeFromJson: false, includeToJson: false)
  _$$DigitalTwinResultImplCopyWith<_$DigitalTwinResultImpl> get copyWith =>
      throw _privateConstructorUsedError;
}

CoachingFeedbackItem _$CoachingFeedbackItemFromJson(Map<String, dynamic> json) {
  return _CoachingFeedbackItem.fromJson(json);
}

/// @nodoc
mixin _$CoachingFeedbackItem {
  String get variable => throw _privateConstructorUsedError;
  String get label => throw _privateConstructorUsedError;
  @JsonKey(name: 'measured_deg')
  double get measuredDeg => throw _privateConstructorUsedError;
  @JsonKey(name: 'target_deg')
  double get targetDeg => throw _privateConstructorUsedError;
  @JsonKey(name: 'target_range_min_deg')
  double get targetRangeMinDeg => throw _privateConstructorUsedError;
  @JsonKey(name: 'target_range_max_deg')
  double get targetRangeMaxDeg => throw _privateConstructorUsedError;
  @JsonKey(name: 'delta_deg')
  double get deltaDeg => throw _privateConstructorUsedError;
  String get status => throw _privateConstructorUsedError;
  String get cue => throw _privateConstructorUsedError;
  String get source => throw _privateConstructorUsedError;

  /// Serializes this CoachingFeedbackItem to a JSON map.
  Map<String, dynamic> toJson() => throw _privateConstructorUsedError;

  /// Create a copy of CoachingFeedbackItem
  /// with the given fields replaced by the non-null parameter values.
  @JsonKey(includeFromJson: false, includeToJson: false)
  $CoachingFeedbackItemCopyWith<CoachingFeedbackItem> get copyWith =>
      throw _privateConstructorUsedError;
}

/// @nodoc
abstract class $CoachingFeedbackItemCopyWith<$Res> {
  factory $CoachingFeedbackItemCopyWith(CoachingFeedbackItem value,
          $Res Function(CoachingFeedbackItem) then) =
      _$CoachingFeedbackItemCopyWithImpl<$Res, CoachingFeedbackItem>;
  @useResult
  $Res call(
      {String variable,
      String label,
      @JsonKey(name: 'measured_deg') double measuredDeg,
      @JsonKey(name: 'target_deg') double targetDeg,
      @JsonKey(name: 'target_range_min_deg') double targetRangeMinDeg,
      @JsonKey(name: 'target_range_max_deg') double targetRangeMaxDeg,
      @JsonKey(name: 'delta_deg') double deltaDeg,
      String status,
      String cue,
      String source});
}

/// @nodoc
class _$CoachingFeedbackItemCopyWithImpl<$Res,
        $Val extends CoachingFeedbackItem>
    implements $CoachingFeedbackItemCopyWith<$Res> {
  _$CoachingFeedbackItemCopyWithImpl(this._value, this._then);

  // ignore: unused_field
  final $Val _value;
  // ignore: unused_field
  final $Res Function($Val) _then;

  /// Create a copy of CoachingFeedbackItem
  /// with the given fields replaced by the non-null parameter values.
  @pragma('vm:prefer-inline')
  @override
  $Res call({
    Object? variable = null,
    Object? label = null,
    Object? measuredDeg = null,
    Object? targetDeg = null,
    Object? targetRangeMinDeg = null,
    Object? targetRangeMaxDeg = null,
    Object? deltaDeg = null,
    Object? status = null,
    Object? cue = null,
    Object? source = null,
  }) {
    return _then(_value.copyWith(
      variable: null == variable
          ? _value.variable
          : variable // ignore: cast_nullable_to_non_nullable
              as String,
      label: null == label
          ? _value.label
          : label // ignore: cast_nullable_to_non_nullable
              as String,
      measuredDeg: null == measuredDeg
          ? _value.measuredDeg
          : measuredDeg // ignore: cast_nullable_to_non_nullable
              as double,
      targetDeg: null == targetDeg
          ? _value.targetDeg
          : targetDeg // ignore: cast_nullable_to_non_nullable
              as double,
      targetRangeMinDeg: null == targetRangeMinDeg
          ? _value.targetRangeMinDeg
          : targetRangeMinDeg // ignore: cast_nullable_to_non_nullable
              as double,
      targetRangeMaxDeg: null == targetRangeMaxDeg
          ? _value.targetRangeMaxDeg
          : targetRangeMaxDeg // ignore: cast_nullable_to_non_nullable
              as double,
      deltaDeg: null == deltaDeg
          ? _value.deltaDeg
          : deltaDeg // ignore: cast_nullable_to_non_nullable
              as double,
      status: null == status
          ? _value.status
          : status // ignore: cast_nullable_to_non_nullable
              as String,
      cue: null == cue
          ? _value.cue
          : cue // ignore: cast_nullable_to_non_nullable
              as String,
      source: null == source
          ? _value.source
          : source // ignore: cast_nullable_to_non_nullable
              as String,
    ) as $Val);
  }
}

/// @nodoc
abstract class _$$CoachingFeedbackItemImplCopyWith<$Res>
    implements $CoachingFeedbackItemCopyWith<$Res> {
  factory _$$CoachingFeedbackItemImplCopyWith(_$CoachingFeedbackItemImpl value,
          $Res Function(_$CoachingFeedbackItemImpl) then) =
      __$$CoachingFeedbackItemImplCopyWithImpl<$Res>;
  @override
  @useResult
  $Res call(
      {String variable,
      String label,
      @JsonKey(name: 'measured_deg') double measuredDeg,
      @JsonKey(name: 'target_deg') double targetDeg,
      @JsonKey(name: 'target_range_min_deg') double targetRangeMinDeg,
      @JsonKey(name: 'target_range_max_deg') double targetRangeMaxDeg,
      @JsonKey(name: 'delta_deg') double deltaDeg,
      String status,
      String cue,
      String source});
}

/// @nodoc
class __$$CoachingFeedbackItemImplCopyWithImpl<$Res>
    extends _$CoachingFeedbackItemCopyWithImpl<$Res, _$CoachingFeedbackItemImpl>
    implements _$$CoachingFeedbackItemImplCopyWith<$Res> {
  __$$CoachingFeedbackItemImplCopyWithImpl(_$CoachingFeedbackItemImpl _value,
      $Res Function(_$CoachingFeedbackItemImpl) _then)
      : super(_value, _then);

  /// Create a copy of CoachingFeedbackItem
  /// with the given fields replaced by the non-null parameter values.
  @pragma('vm:prefer-inline')
  @override
  $Res call({
    Object? variable = null,
    Object? label = null,
    Object? measuredDeg = null,
    Object? targetDeg = null,
    Object? targetRangeMinDeg = null,
    Object? targetRangeMaxDeg = null,
    Object? deltaDeg = null,
    Object? status = null,
    Object? cue = null,
    Object? source = null,
  }) {
    return _then(_$CoachingFeedbackItemImpl(
      variable: null == variable
          ? _value.variable
          : variable // ignore: cast_nullable_to_non_nullable
              as String,
      label: null == label
          ? _value.label
          : label // ignore: cast_nullable_to_non_nullable
              as String,
      measuredDeg: null == measuredDeg
          ? _value.measuredDeg
          : measuredDeg // ignore: cast_nullable_to_non_nullable
              as double,
      targetDeg: null == targetDeg
          ? _value.targetDeg
          : targetDeg // ignore: cast_nullable_to_non_nullable
              as double,
      targetRangeMinDeg: null == targetRangeMinDeg
          ? _value.targetRangeMinDeg
          : targetRangeMinDeg // ignore: cast_nullable_to_non_nullable
              as double,
      targetRangeMaxDeg: null == targetRangeMaxDeg
          ? _value.targetRangeMaxDeg
          : targetRangeMaxDeg // ignore: cast_nullable_to_non_nullable
              as double,
      deltaDeg: null == deltaDeg
          ? _value.deltaDeg
          : deltaDeg // ignore: cast_nullable_to_non_nullable
              as double,
      status: null == status
          ? _value.status
          : status // ignore: cast_nullable_to_non_nullable
              as String,
      cue: null == cue
          ? _value.cue
          : cue // ignore: cast_nullable_to_non_nullable
              as String,
      source: null == source
          ? _value.source
          : source // ignore: cast_nullable_to_non_nullable
              as String,
    ));
  }
}

/// @nodoc
@JsonSerializable()
class _$CoachingFeedbackItemImpl implements _CoachingFeedbackItem {
  const _$CoachingFeedbackItemImpl(
      {required this.variable,
      this.label = '',
      @JsonKey(name: 'measured_deg') required this.measuredDeg,
      @JsonKey(name: 'target_deg') required this.targetDeg,
      @JsonKey(name: 'target_range_min_deg') required this.targetRangeMinDeg,
      @JsonKey(name: 'target_range_max_deg') required this.targetRangeMaxDeg,
      @JsonKey(name: 'delta_deg') required this.deltaDeg,
      required this.status,
      required this.cue,
      this.source = ''});

  factory _$CoachingFeedbackItemImpl.fromJson(Map<String, dynamic> json) =>
      _$$CoachingFeedbackItemImplFromJson(json);

  @override
  final String variable;
  @override
  @JsonKey()
  final String label;
  @override
  @JsonKey(name: 'measured_deg')
  final double measuredDeg;
  @override
  @JsonKey(name: 'target_deg')
  final double targetDeg;
  @override
  @JsonKey(name: 'target_range_min_deg')
  final double targetRangeMinDeg;
  @override
  @JsonKey(name: 'target_range_max_deg')
  final double targetRangeMaxDeg;
  @override
  @JsonKey(name: 'delta_deg')
  final double deltaDeg;
  @override
  final String status;
  @override
  final String cue;
  @override
  @JsonKey()
  final String source;

  @override
  String toString() {
    return 'CoachingFeedbackItem(variable: $variable, label: $label, measuredDeg: $measuredDeg, targetDeg: $targetDeg, targetRangeMinDeg: $targetRangeMinDeg, targetRangeMaxDeg: $targetRangeMaxDeg, deltaDeg: $deltaDeg, status: $status, cue: $cue, source: $source)';
  }

  @override
  bool operator ==(Object other) {
    return identical(this, other) ||
        (other.runtimeType == runtimeType &&
            other is _$CoachingFeedbackItemImpl &&
            (identical(other.variable, variable) ||
                other.variable == variable) &&
            (identical(other.label, label) || other.label == label) &&
            (identical(other.measuredDeg, measuredDeg) ||
                other.measuredDeg == measuredDeg) &&
            (identical(other.targetDeg, targetDeg) ||
                other.targetDeg == targetDeg) &&
            (identical(other.targetRangeMinDeg, targetRangeMinDeg) ||
                other.targetRangeMinDeg == targetRangeMinDeg) &&
            (identical(other.targetRangeMaxDeg, targetRangeMaxDeg) ||
                other.targetRangeMaxDeg == targetRangeMaxDeg) &&
            (identical(other.deltaDeg, deltaDeg) ||
                other.deltaDeg == deltaDeg) &&
            (identical(other.status, status) || other.status == status) &&
            (identical(other.cue, cue) || other.cue == cue) &&
            (identical(other.source, source) || other.source == source));
  }

  @JsonKey(includeFromJson: false, includeToJson: false)
  @override
  int get hashCode => Object.hash(
      runtimeType,
      variable,
      label,
      measuredDeg,
      targetDeg,
      targetRangeMinDeg,
      targetRangeMaxDeg,
      deltaDeg,
      status,
      cue,
      source);

  /// Create a copy of CoachingFeedbackItem
  /// with the given fields replaced by the non-null parameter values.
  @JsonKey(includeFromJson: false, includeToJson: false)
  @override
  @pragma('vm:prefer-inline')
  _$$CoachingFeedbackItemImplCopyWith<_$CoachingFeedbackItemImpl>
      get copyWith =>
          __$$CoachingFeedbackItemImplCopyWithImpl<_$CoachingFeedbackItemImpl>(
              this, _$identity);

  @override
  Map<String, dynamic> toJson() {
    return _$$CoachingFeedbackItemImplToJson(
      this,
    );
  }
}

abstract class _CoachingFeedbackItem implements CoachingFeedbackItem {
  const factory _CoachingFeedbackItem(
      {required final String variable,
      final String label,
      @JsonKey(name: 'measured_deg') required final double measuredDeg,
      @JsonKey(name: 'target_deg') required final double targetDeg,
      @JsonKey(name: 'target_range_min_deg')
      required final double targetRangeMinDeg,
      @JsonKey(name: 'target_range_max_deg')
      required final double targetRangeMaxDeg,
      @JsonKey(name: 'delta_deg') required final double deltaDeg,
      required final String status,
      required final String cue,
      final String source}) = _$CoachingFeedbackItemImpl;

  factory _CoachingFeedbackItem.fromJson(Map<String, dynamic> json) =
      _$CoachingFeedbackItemImpl.fromJson;

  @override
  String get variable;
  @override
  String get label;
  @override
  @JsonKey(name: 'measured_deg')
  double get measuredDeg;
  @override
  @JsonKey(name: 'target_deg')
  double get targetDeg;
  @override
  @JsonKey(name: 'target_range_min_deg')
  double get targetRangeMinDeg;
  @override
  @JsonKey(name: 'target_range_max_deg')
  double get targetRangeMaxDeg;
  @override
  @JsonKey(name: 'delta_deg')
  double get deltaDeg;
  @override
  String get status;
  @override
  String get cue;
  @override
  String get source;

  /// Create a copy of CoachingFeedbackItem
  /// with the given fields replaced by the non-null parameter values.
  @override
  @JsonKey(includeFromJson: false, includeToJson: false)
  _$$CoachingFeedbackItemImplCopyWith<_$CoachingFeedbackItemImpl>
      get copyWith => throw _privateConstructorUsedError;
}
