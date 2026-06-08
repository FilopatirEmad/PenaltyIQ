// coverage:ignore-file
// GENERATED CODE - DO NOT MODIFY BY HAND
// ignore_for_file: type=lint
// ignore_for_file: unused_element, deprecated_member_use, deprecated_member_use_from_same_package, use_function_type_syntax_for_parameters, unnecessary_const, avoid_init_to_null, invalid_override_different_default_values_named, prefer_expression_function_bodies, annotate_overrides, invalid_annotation_target, unnecessary_question_mark

part of 'calibration_response.dart';

// **************************************************************************
// FreezedGenerator
// **************************************************************************

T _$identity<T>(T value) => value;

final _privateConstructorUsedError = UnsupportedError(
    'It seems like you constructed your class using `MyClass._()`. This constructor is only meant to be used by freezed and you are not supposed to need it nor use it.\nPlease check the documentation here for more information: https://github.com/rrousselGit/freezed#adding-getters-and-methods-to-our-models');

CalibrationResponse _$CalibrationResponseFromJson(Map<String, dynamic> json) {
  return _CalibrationResponse.fromJson(json);
}

/// @nodoc
mixin _$CalibrationResponse {
  @JsonKey(name: 'session_id')
  String get sessionId => throw _privateConstructorUsedError;

  /// "LOCKED" | "FAILED" | "INSUFFICIENT_DATA"
  String get status => throw _privateConstructorUsedError;

  /// S = 0.22 / d_ball_px [m/pixel]. [FIFA-2024, SPEC §1.2.1]
  @JsonKey(name: 'scale_m_per_px')
  double? get scaleMPerPx => throw _privateConstructorUsedError;
  @JsonKey(name: 'segments_m')
  LockedSegments? get segmentsM => throw _privateConstructorUsedError;
  @JsonKey(name: 'stability_check')
  StabilityCheckResult get stabilityCheck => throw _privateConstructorUsedError;
  @JsonKey(name: 'frames_used')
  int get framesUsed => throw _privateConstructorUsedError;
  String? get error => throw _privateConstructorUsedError;

  /// Serializes this CalibrationResponse to a JSON map.
  Map<String, dynamic> toJson() => throw _privateConstructorUsedError;

  /// Create a copy of CalibrationResponse
  /// with the given fields replaced by the non-null parameter values.
  @JsonKey(includeFromJson: false, includeToJson: false)
  $CalibrationResponseCopyWith<CalibrationResponse> get copyWith =>
      throw _privateConstructorUsedError;
}

/// @nodoc
abstract class $CalibrationResponseCopyWith<$Res> {
  factory $CalibrationResponseCopyWith(
          CalibrationResponse value, $Res Function(CalibrationResponse) then) =
      _$CalibrationResponseCopyWithImpl<$Res, CalibrationResponse>;
  @useResult
  $Res call(
      {@JsonKey(name: 'session_id') String sessionId,
      String status,
      @JsonKey(name: 'scale_m_per_px') double? scaleMPerPx,
      @JsonKey(name: 'segments_m') LockedSegments? segmentsM,
      @JsonKey(name: 'stability_check') StabilityCheckResult stabilityCheck,
      @JsonKey(name: 'frames_used') int framesUsed,
      String? error});

  $LockedSegmentsCopyWith<$Res>? get segmentsM;
  $StabilityCheckResultCopyWith<$Res> get stabilityCheck;
}

/// @nodoc
class _$CalibrationResponseCopyWithImpl<$Res, $Val extends CalibrationResponse>
    implements $CalibrationResponseCopyWith<$Res> {
  _$CalibrationResponseCopyWithImpl(this._value, this._then);

  // ignore: unused_field
  final $Val _value;
  // ignore: unused_field
  final $Res Function($Val) _then;

  /// Create a copy of CalibrationResponse
  /// with the given fields replaced by the non-null parameter values.
  @pragma('vm:prefer-inline')
  @override
  $Res call({
    Object? sessionId = null,
    Object? status = null,
    Object? scaleMPerPx = freezed,
    Object? segmentsM = freezed,
    Object? stabilityCheck = null,
    Object? framesUsed = null,
    Object? error = freezed,
  }) {
    return _then(_value.copyWith(
      sessionId: null == sessionId
          ? _value.sessionId
          : sessionId // ignore: cast_nullable_to_non_nullable
              as String,
      status: null == status
          ? _value.status
          : status // ignore: cast_nullable_to_non_nullable
              as String,
      scaleMPerPx: freezed == scaleMPerPx
          ? _value.scaleMPerPx
          : scaleMPerPx // ignore: cast_nullable_to_non_nullable
              as double?,
      segmentsM: freezed == segmentsM
          ? _value.segmentsM
          : segmentsM // ignore: cast_nullable_to_non_nullable
              as LockedSegments?,
      stabilityCheck: null == stabilityCheck
          ? _value.stabilityCheck
          : stabilityCheck // ignore: cast_nullable_to_non_nullable
              as StabilityCheckResult,
      framesUsed: null == framesUsed
          ? _value.framesUsed
          : framesUsed // ignore: cast_nullable_to_non_nullable
              as int,
      error: freezed == error
          ? _value.error
          : error // ignore: cast_nullable_to_non_nullable
              as String?,
    ) as $Val);
  }

  /// Create a copy of CalibrationResponse
  /// with the given fields replaced by the non-null parameter values.
  @override
  @pragma('vm:prefer-inline')
  $LockedSegmentsCopyWith<$Res>? get segmentsM {
    if (_value.segmentsM == null) {
      return null;
    }

    return $LockedSegmentsCopyWith<$Res>(_value.segmentsM!, (value) {
      return _then(_value.copyWith(segmentsM: value) as $Val);
    });
  }

  /// Create a copy of CalibrationResponse
  /// with the given fields replaced by the non-null parameter values.
  @override
  @pragma('vm:prefer-inline')
  $StabilityCheckResultCopyWith<$Res> get stabilityCheck {
    return $StabilityCheckResultCopyWith<$Res>(_value.stabilityCheck, (value) {
      return _then(_value.copyWith(stabilityCheck: value) as $Val);
    });
  }
}

/// @nodoc
abstract class _$$CalibrationResponseImplCopyWith<$Res>
    implements $CalibrationResponseCopyWith<$Res> {
  factory _$$CalibrationResponseImplCopyWith(_$CalibrationResponseImpl value,
          $Res Function(_$CalibrationResponseImpl) then) =
      __$$CalibrationResponseImplCopyWithImpl<$Res>;
  @override
  @useResult
  $Res call(
      {@JsonKey(name: 'session_id') String sessionId,
      String status,
      @JsonKey(name: 'scale_m_per_px') double? scaleMPerPx,
      @JsonKey(name: 'segments_m') LockedSegments? segmentsM,
      @JsonKey(name: 'stability_check') StabilityCheckResult stabilityCheck,
      @JsonKey(name: 'frames_used') int framesUsed,
      String? error});

  @override
  $LockedSegmentsCopyWith<$Res>? get segmentsM;
  @override
  $StabilityCheckResultCopyWith<$Res> get stabilityCheck;
}

/// @nodoc
class __$$CalibrationResponseImplCopyWithImpl<$Res>
    extends _$CalibrationResponseCopyWithImpl<$Res, _$CalibrationResponseImpl>
    implements _$$CalibrationResponseImplCopyWith<$Res> {
  __$$CalibrationResponseImplCopyWithImpl(_$CalibrationResponseImpl _value,
      $Res Function(_$CalibrationResponseImpl) _then)
      : super(_value, _then);

  /// Create a copy of CalibrationResponse
  /// with the given fields replaced by the non-null parameter values.
  @pragma('vm:prefer-inline')
  @override
  $Res call({
    Object? sessionId = null,
    Object? status = null,
    Object? scaleMPerPx = freezed,
    Object? segmentsM = freezed,
    Object? stabilityCheck = null,
    Object? framesUsed = null,
    Object? error = freezed,
  }) {
    return _then(_$CalibrationResponseImpl(
      sessionId: null == sessionId
          ? _value.sessionId
          : sessionId // ignore: cast_nullable_to_non_nullable
              as String,
      status: null == status
          ? _value.status
          : status // ignore: cast_nullable_to_non_nullable
              as String,
      scaleMPerPx: freezed == scaleMPerPx
          ? _value.scaleMPerPx
          : scaleMPerPx // ignore: cast_nullable_to_non_nullable
              as double?,
      segmentsM: freezed == segmentsM
          ? _value.segmentsM
          : segmentsM // ignore: cast_nullable_to_non_nullable
              as LockedSegments?,
      stabilityCheck: null == stabilityCheck
          ? _value.stabilityCheck
          : stabilityCheck // ignore: cast_nullable_to_non_nullable
              as StabilityCheckResult,
      framesUsed: null == framesUsed
          ? _value.framesUsed
          : framesUsed // ignore: cast_nullable_to_non_nullable
              as int,
      error: freezed == error
          ? _value.error
          : error // ignore: cast_nullable_to_non_nullable
              as String?,
    ));
  }
}

/// @nodoc
@JsonSerializable()
class _$CalibrationResponseImpl implements _CalibrationResponse {
  const _$CalibrationResponseImpl(
      {@JsonKey(name: 'session_id') required this.sessionId,
      required this.status,
      @JsonKey(name: 'scale_m_per_px') this.scaleMPerPx,
      @JsonKey(name: 'segments_m') this.segmentsM,
      @JsonKey(name: 'stability_check') required this.stabilityCheck,
      @JsonKey(name: 'frames_used') required this.framesUsed,
      this.error});

  factory _$CalibrationResponseImpl.fromJson(Map<String, dynamic> json) =>
      _$$CalibrationResponseImplFromJson(json);

  @override
  @JsonKey(name: 'session_id')
  final String sessionId;

  /// "LOCKED" | "FAILED" | "INSUFFICIENT_DATA"
  @override
  final String status;

  /// S = 0.22 / d_ball_px [m/pixel]. [FIFA-2024, SPEC §1.2.1]
  @override
  @JsonKey(name: 'scale_m_per_px')
  final double? scaleMPerPx;
  @override
  @JsonKey(name: 'segments_m')
  final LockedSegments? segmentsM;
  @override
  @JsonKey(name: 'stability_check')
  final StabilityCheckResult stabilityCheck;
  @override
  @JsonKey(name: 'frames_used')
  final int framesUsed;
  @override
  final String? error;

  @override
  String toString() {
    return 'CalibrationResponse(sessionId: $sessionId, status: $status, scaleMPerPx: $scaleMPerPx, segmentsM: $segmentsM, stabilityCheck: $stabilityCheck, framesUsed: $framesUsed, error: $error)';
  }

  @override
  bool operator ==(Object other) {
    return identical(this, other) ||
        (other.runtimeType == runtimeType &&
            other is _$CalibrationResponseImpl &&
            (identical(other.sessionId, sessionId) ||
                other.sessionId == sessionId) &&
            (identical(other.status, status) || other.status == status) &&
            (identical(other.scaleMPerPx, scaleMPerPx) ||
                other.scaleMPerPx == scaleMPerPx) &&
            (identical(other.segmentsM, segmentsM) ||
                other.segmentsM == segmentsM) &&
            (identical(other.stabilityCheck, stabilityCheck) ||
                other.stabilityCheck == stabilityCheck) &&
            (identical(other.framesUsed, framesUsed) ||
                other.framesUsed == framesUsed) &&
            (identical(other.error, error) || other.error == error));
  }

  @JsonKey(includeFromJson: false, includeToJson: false)
  @override
  int get hashCode => Object.hash(runtimeType, sessionId, status, scaleMPerPx,
      segmentsM, stabilityCheck, framesUsed, error);

  /// Create a copy of CalibrationResponse
  /// with the given fields replaced by the non-null parameter values.
  @JsonKey(includeFromJson: false, includeToJson: false)
  @override
  @pragma('vm:prefer-inline')
  _$$CalibrationResponseImplCopyWith<_$CalibrationResponseImpl> get copyWith =>
      __$$CalibrationResponseImplCopyWithImpl<_$CalibrationResponseImpl>(
          this, _$identity);

  @override
  Map<String, dynamic> toJson() {
    return _$$CalibrationResponseImplToJson(
      this,
    );
  }
}

abstract class _CalibrationResponse implements CalibrationResponse {
  const factory _CalibrationResponse(
      {@JsonKey(name: 'session_id') required final String sessionId,
      required final String status,
      @JsonKey(name: 'scale_m_per_px') final double? scaleMPerPx,
      @JsonKey(name: 'segments_m') final LockedSegments? segmentsM,
      @JsonKey(name: 'stability_check')
      required final StabilityCheckResult stabilityCheck,
      @JsonKey(name: 'frames_used') required final int framesUsed,
      final String? error}) = _$CalibrationResponseImpl;

  factory _CalibrationResponse.fromJson(Map<String, dynamic> json) =
      _$CalibrationResponseImpl.fromJson;

  @override
  @JsonKey(name: 'session_id')
  String get sessionId;

  /// "LOCKED" | "FAILED" | "INSUFFICIENT_DATA"
  @override
  String get status;

  /// S = 0.22 / d_ball_px [m/pixel]. [FIFA-2024, SPEC §1.2.1]
  @override
  @JsonKey(name: 'scale_m_per_px')
  double? get scaleMPerPx;
  @override
  @JsonKey(name: 'segments_m')
  LockedSegments? get segmentsM;
  @override
  @JsonKey(name: 'stability_check')
  StabilityCheckResult get stabilityCheck;
  @override
  @JsonKey(name: 'frames_used')
  int get framesUsed;
  @override
  String? get error;

  /// Create a copy of CalibrationResponse
  /// with the given fields replaced by the non-null parameter values.
  @override
  @JsonKey(includeFromJson: false, includeToJson: false)
  _$$CalibrationResponseImplCopyWith<_$CalibrationResponseImpl> get copyWith =>
      throw _privateConstructorUsedError;
}

LockedSegments _$LockedSegmentsFromJson(Map<String, dynamic> json) {
  return _LockedSegments.fromJson(json);
}

/// @nodoc
mixin _$LockedSegments {
  /// Thigh length: hip → knee [m]. [WINTER-2009 Ch.3]
  @JsonKey(name: 'thigh_m')
  double get thighM => throw _privateConstructorUsedError;

  /// Shank length: knee → ankle [m]. [WINTER-2009 Ch.3]
  @JsonKey(name: 'shank_m')
  double get shankM => throw _privateConstructorUsedError;

  /// Trunk length: hip → shoulder [m]. [WINTER-2009 Ch.3]
  @JsonKey(name: 'trunk_m')
  double get trunkM => throw _privateConstructorUsedError;

  /// L_thigh + L_shank [m]. [SPEC §1.3.4]
  @JsonKey(name: 'leg_m')
  double get legM => throw _privateConstructorUsedError;

  /// Serializes this LockedSegments to a JSON map.
  Map<String, dynamic> toJson() => throw _privateConstructorUsedError;

  /// Create a copy of LockedSegments
  /// with the given fields replaced by the non-null parameter values.
  @JsonKey(includeFromJson: false, includeToJson: false)
  $LockedSegmentsCopyWith<LockedSegments> get copyWith =>
      throw _privateConstructorUsedError;
}

/// @nodoc
abstract class $LockedSegmentsCopyWith<$Res> {
  factory $LockedSegmentsCopyWith(
          LockedSegments value, $Res Function(LockedSegments) then) =
      _$LockedSegmentsCopyWithImpl<$Res, LockedSegments>;
  @useResult
  $Res call(
      {@JsonKey(name: 'thigh_m') double thighM,
      @JsonKey(name: 'shank_m') double shankM,
      @JsonKey(name: 'trunk_m') double trunkM,
      @JsonKey(name: 'leg_m') double legM});
}

/// @nodoc
class _$LockedSegmentsCopyWithImpl<$Res, $Val extends LockedSegments>
    implements $LockedSegmentsCopyWith<$Res> {
  _$LockedSegmentsCopyWithImpl(this._value, this._then);

  // ignore: unused_field
  final $Val _value;
  // ignore: unused_field
  final $Res Function($Val) _then;

  /// Create a copy of LockedSegments
  /// with the given fields replaced by the non-null parameter values.
  @pragma('vm:prefer-inline')
  @override
  $Res call({
    Object? thighM = null,
    Object? shankM = null,
    Object? trunkM = null,
    Object? legM = null,
  }) {
    return _then(_value.copyWith(
      thighM: null == thighM
          ? _value.thighM
          : thighM // ignore: cast_nullable_to_non_nullable
              as double,
      shankM: null == shankM
          ? _value.shankM
          : shankM // ignore: cast_nullable_to_non_nullable
              as double,
      trunkM: null == trunkM
          ? _value.trunkM
          : trunkM // ignore: cast_nullable_to_non_nullable
              as double,
      legM: null == legM
          ? _value.legM
          : legM // ignore: cast_nullable_to_non_nullable
              as double,
    ) as $Val);
  }
}

/// @nodoc
abstract class _$$LockedSegmentsImplCopyWith<$Res>
    implements $LockedSegmentsCopyWith<$Res> {
  factory _$$LockedSegmentsImplCopyWith(_$LockedSegmentsImpl value,
          $Res Function(_$LockedSegmentsImpl) then) =
      __$$LockedSegmentsImplCopyWithImpl<$Res>;
  @override
  @useResult
  $Res call(
      {@JsonKey(name: 'thigh_m') double thighM,
      @JsonKey(name: 'shank_m') double shankM,
      @JsonKey(name: 'trunk_m') double trunkM,
      @JsonKey(name: 'leg_m') double legM});
}

/// @nodoc
class __$$LockedSegmentsImplCopyWithImpl<$Res>
    extends _$LockedSegmentsCopyWithImpl<$Res, _$LockedSegmentsImpl>
    implements _$$LockedSegmentsImplCopyWith<$Res> {
  __$$LockedSegmentsImplCopyWithImpl(
      _$LockedSegmentsImpl _value, $Res Function(_$LockedSegmentsImpl) _then)
      : super(_value, _then);

  /// Create a copy of LockedSegments
  /// with the given fields replaced by the non-null parameter values.
  @pragma('vm:prefer-inline')
  @override
  $Res call({
    Object? thighM = null,
    Object? shankM = null,
    Object? trunkM = null,
    Object? legM = null,
  }) {
    return _then(_$LockedSegmentsImpl(
      thighM: null == thighM
          ? _value.thighM
          : thighM // ignore: cast_nullable_to_non_nullable
              as double,
      shankM: null == shankM
          ? _value.shankM
          : shankM // ignore: cast_nullable_to_non_nullable
              as double,
      trunkM: null == trunkM
          ? _value.trunkM
          : trunkM // ignore: cast_nullable_to_non_nullable
              as double,
      legM: null == legM
          ? _value.legM
          : legM // ignore: cast_nullable_to_non_nullable
              as double,
    ));
  }
}

/// @nodoc
@JsonSerializable()
class _$LockedSegmentsImpl implements _LockedSegments {
  const _$LockedSegmentsImpl(
      {@JsonKey(name: 'thigh_m') required this.thighM,
      @JsonKey(name: 'shank_m') required this.shankM,
      @JsonKey(name: 'trunk_m') required this.trunkM,
      @JsonKey(name: 'leg_m') required this.legM});

  factory _$LockedSegmentsImpl.fromJson(Map<String, dynamic> json) =>
      _$$LockedSegmentsImplFromJson(json);

  /// Thigh length: hip → knee [m]. [WINTER-2009 Ch.3]
  @override
  @JsonKey(name: 'thigh_m')
  final double thighM;

  /// Shank length: knee → ankle [m]. [WINTER-2009 Ch.3]
  @override
  @JsonKey(name: 'shank_m')
  final double shankM;

  /// Trunk length: hip → shoulder [m]. [WINTER-2009 Ch.3]
  @override
  @JsonKey(name: 'trunk_m')
  final double trunkM;

  /// L_thigh + L_shank [m]. [SPEC §1.3.4]
  @override
  @JsonKey(name: 'leg_m')
  final double legM;

  @override
  String toString() {
    return 'LockedSegments(thighM: $thighM, shankM: $shankM, trunkM: $trunkM, legM: $legM)';
  }

  @override
  bool operator ==(Object other) {
    return identical(this, other) ||
        (other.runtimeType == runtimeType &&
            other is _$LockedSegmentsImpl &&
            (identical(other.thighM, thighM) || other.thighM == thighM) &&
            (identical(other.shankM, shankM) || other.shankM == shankM) &&
            (identical(other.trunkM, trunkM) || other.trunkM == trunkM) &&
            (identical(other.legM, legM) || other.legM == legM));
  }

  @JsonKey(includeFromJson: false, includeToJson: false)
  @override
  int get hashCode => Object.hash(runtimeType, thighM, shankM, trunkM, legM);

  /// Create a copy of LockedSegments
  /// with the given fields replaced by the non-null parameter values.
  @JsonKey(includeFromJson: false, includeToJson: false)
  @override
  @pragma('vm:prefer-inline')
  _$$LockedSegmentsImplCopyWith<_$LockedSegmentsImpl> get copyWith =>
      __$$LockedSegmentsImplCopyWithImpl<_$LockedSegmentsImpl>(
          this, _$identity);

  @override
  Map<String, dynamic> toJson() {
    return _$$LockedSegmentsImplToJson(
      this,
    );
  }
}

abstract class _LockedSegments implements LockedSegments {
  const factory _LockedSegments(
          {@JsonKey(name: 'thigh_m') required final double thighM,
          @JsonKey(name: 'shank_m') required final double shankM,
          @JsonKey(name: 'trunk_m') required final double trunkM,
          @JsonKey(name: 'leg_m') required final double legM}) =
      _$LockedSegmentsImpl;

  factory _LockedSegments.fromJson(Map<String, dynamic> json) =
      _$LockedSegmentsImpl.fromJson;

  /// Thigh length: hip → knee [m]. [WINTER-2009 Ch.3]
  @override
  @JsonKey(name: 'thigh_m')
  double get thighM;

  /// Shank length: knee → ankle [m]. [WINTER-2009 Ch.3]
  @override
  @JsonKey(name: 'shank_m')
  double get shankM;

  /// Trunk length: hip → shoulder [m]. [WINTER-2009 Ch.3]
  @override
  @JsonKey(name: 'trunk_m')
  double get trunkM;

  /// L_thigh + L_shank [m]. [SPEC §1.3.4]
  @override
  @JsonKey(name: 'leg_m')
  double get legM;

  /// Create a copy of LockedSegments
  /// with the given fields replaced by the non-null parameter values.
  @override
  @JsonKey(includeFromJson: false, includeToJson: false)
  _$$LockedSegmentsImplCopyWith<_$LockedSegmentsImpl> get copyWith =>
      throw _privateConstructorUsedError;
}

StabilityCheckResult _$StabilityCheckResultFromJson(Map<String, dynamic> json) {
  return _StabilityCheckResult.fromJson(json);
}

/// @nodoc
mixin _$StabilityCheckResult {
  @JsonKey(name: 'thigh_variation_m')
  double get thighVariationM => throw _privateConstructorUsedError;
  @JsonKey(name: 'shank_variation_m')
  double get shankVariationM => throw _privateConstructorUsedError;
  @JsonKey(name: 'trunk_variation_m')
  double get trunkVariationM => throw _privateConstructorUsedError;
  @JsonKey(name: 'thigh_tolerance_m')
  double get thighToleranceM => throw _privateConstructorUsedError;
  @JsonKey(name: 'shank_tolerance_m')
  double get shankToleranceM => throw _privateConstructorUsedError;
  @JsonKey(name: 'trunk_tolerance_m')
  double get trunkToleranceM => throw _privateConstructorUsedError;
  @JsonKey(name: 'window_duration_s')
  double get windowDurationS => throw _privateConstructorUsedError;
  @JsonKey(name: 'thigh_passed')
  bool get thighPassed => throw _privateConstructorUsedError;
  @JsonKey(name: 'shank_passed')
  bool get shankPassed => throw _privateConstructorUsedError;
  @JsonKey(name: 'trunk_passed')
  bool get trunkPassed => throw _privateConstructorUsedError;
  @JsonKey(name: 'overall_passed')
  bool get overallPassed => throw _privateConstructorUsedError;

  /// Serializes this StabilityCheckResult to a JSON map.
  Map<String, dynamic> toJson() => throw _privateConstructorUsedError;

  /// Create a copy of StabilityCheckResult
  /// with the given fields replaced by the non-null parameter values.
  @JsonKey(includeFromJson: false, includeToJson: false)
  $StabilityCheckResultCopyWith<StabilityCheckResult> get copyWith =>
      throw _privateConstructorUsedError;
}

/// @nodoc
abstract class $StabilityCheckResultCopyWith<$Res> {
  factory $StabilityCheckResultCopyWith(StabilityCheckResult value,
          $Res Function(StabilityCheckResult) then) =
      _$StabilityCheckResultCopyWithImpl<$Res, StabilityCheckResult>;
  @useResult
  $Res call(
      {@JsonKey(name: 'thigh_variation_m') double thighVariationM,
      @JsonKey(name: 'shank_variation_m') double shankVariationM,
      @JsonKey(name: 'trunk_variation_m') double trunkVariationM,
      @JsonKey(name: 'thigh_tolerance_m') double thighToleranceM,
      @JsonKey(name: 'shank_tolerance_m') double shankToleranceM,
      @JsonKey(name: 'trunk_tolerance_m') double trunkToleranceM,
      @JsonKey(name: 'window_duration_s') double windowDurationS,
      @JsonKey(name: 'thigh_passed') bool thighPassed,
      @JsonKey(name: 'shank_passed') bool shankPassed,
      @JsonKey(name: 'trunk_passed') bool trunkPassed,
      @JsonKey(name: 'overall_passed') bool overallPassed});
}

/// @nodoc
class _$StabilityCheckResultCopyWithImpl<$Res,
        $Val extends StabilityCheckResult>
    implements $StabilityCheckResultCopyWith<$Res> {
  _$StabilityCheckResultCopyWithImpl(this._value, this._then);

  // ignore: unused_field
  final $Val _value;
  // ignore: unused_field
  final $Res Function($Val) _then;

  /// Create a copy of StabilityCheckResult
  /// with the given fields replaced by the non-null parameter values.
  @pragma('vm:prefer-inline')
  @override
  $Res call({
    Object? thighVariationM = null,
    Object? shankVariationM = null,
    Object? trunkVariationM = null,
    Object? thighToleranceM = null,
    Object? shankToleranceM = null,
    Object? trunkToleranceM = null,
    Object? windowDurationS = null,
    Object? thighPassed = null,
    Object? shankPassed = null,
    Object? trunkPassed = null,
    Object? overallPassed = null,
  }) {
    return _then(_value.copyWith(
      thighVariationM: null == thighVariationM
          ? _value.thighVariationM
          : thighVariationM // ignore: cast_nullable_to_non_nullable
              as double,
      shankVariationM: null == shankVariationM
          ? _value.shankVariationM
          : shankVariationM // ignore: cast_nullable_to_non_nullable
              as double,
      trunkVariationM: null == trunkVariationM
          ? _value.trunkVariationM
          : trunkVariationM // ignore: cast_nullable_to_non_nullable
              as double,
      thighToleranceM: null == thighToleranceM
          ? _value.thighToleranceM
          : thighToleranceM // ignore: cast_nullable_to_non_nullable
              as double,
      shankToleranceM: null == shankToleranceM
          ? _value.shankToleranceM
          : shankToleranceM // ignore: cast_nullable_to_non_nullable
              as double,
      trunkToleranceM: null == trunkToleranceM
          ? _value.trunkToleranceM
          : trunkToleranceM // ignore: cast_nullable_to_non_nullable
              as double,
      windowDurationS: null == windowDurationS
          ? _value.windowDurationS
          : windowDurationS // ignore: cast_nullable_to_non_nullable
              as double,
      thighPassed: null == thighPassed
          ? _value.thighPassed
          : thighPassed // ignore: cast_nullable_to_non_nullable
              as bool,
      shankPassed: null == shankPassed
          ? _value.shankPassed
          : shankPassed // ignore: cast_nullable_to_non_nullable
              as bool,
      trunkPassed: null == trunkPassed
          ? _value.trunkPassed
          : trunkPassed // ignore: cast_nullable_to_non_nullable
              as bool,
      overallPassed: null == overallPassed
          ? _value.overallPassed
          : overallPassed // ignore: cast_nullable_to_non_nullable
              as bool,
    ) as $Val);
  }
}

/// @nodoc
abstract class _$$StabilityCheckResultImplCopyWith<$Res>
    implements $StabilityCheckResultCopyWith<$Res> {
  factory _$$StabilityCheckResultImplCopyWith(_$StabilityCheckResultImpl value,
          $Res Function(_$StabilityCheckResultImpl) then) =
      __$$StabilityCheckResultImplCopyWithImpl<$Res>;
  @override
  @useResult
  $Res call(
      {@JsonKey(name: 'thigh_variation_m') double thighVariationM,
      @JsonKey(name: 'shank_variation_m') double shankVariationM,
      @JsonKey(name: 'trunk_variation_m') double trunkVariationM,
      @JsonKey(name: 'thigh_tolerance_m') double thighToleranceM,
      @JsonKey(name: 'shank_tolerance_m') double shankToleranceM,
      @JsonKey(name: 'trunk_tolerance_m') double trunkToleranceM,
      @JsonKey(name: 'window_duration_s') double windowDurationS,
      @JsonKey(name: 'thigh_passed') bool thighPassed,
      @JsonKey(name: 'shank_passed') bool shankPassed,
      @JsonKey(name: 'trunk_passed') bool trunkPassed,
      @JsonKey(name: 'overall_passed') bool overallPassed});
}

/// @nodoc
class __$$StabilityCheckResultImplCopyWithImpl<$Res>
    extends _$StabilityCheckResultCopyWithImpl<$Res, _$StabilityCheckResultImpl>
    implements _$$StabilityCheckResultImplCopyWith<$Res> {
  __$$StabilityCheckResultImplCopyWithImpl(_$StabilityCheckResultImpl _value,
      $Res Function(_$StabilityCheckResultImpl) _then)
      : super(_value, _then);

  /// Create a copy of StabilityCheckResult
  /// with the given fields replaced by the non-null parameter values.
  @pragma('vm:prefer-inline')
  @override
  $Res call({
    Object? thighVariationM = null,
    Object? shankVariationM = null,
    Object? trunkVariationM = null,
    Object? thighToleranceM = null,
    Object? shankToleranceM = null,
    Object? trunkToleranceM = null,
    Object? windowDurationS = null,
    Object? thighPassed = null,
    Object? shankPassed = null,
    Object? trunkPassed = null,
    Object? overallPassed = null,
  }) {
    return _then(_$StabilityCheckResultImpl(
      thighVariationM: null == thighVariationM
          ? _value.thighVariationM
          : thighVariationM // ignore: cast_nullable_to_non_nullable
              as double,
      shankVariationM: null == shankVariationM
          ? _value.shankVariationM
          : shankVariationM // ignore: cast_nullable_to_non_nullable
              as double,
      trunkVariationM: null == trunkVariationM
          ? _value.trunkVariationM
          : trunkVariationM // ignore: cast_nullable_to_non_nullable
              as double,
      thighToleranceM: null == thighToleranceM
          ? _value.thighToleranceM
          : thighToleranceM // ignore: cast_nullable_to_non_nullable
              as double,
      shankToleranceM: null == shankToleranceM
          ? _value.shankToleranceM
          : shankToleranceM // ignore: cast_nullable_to_non_nullable
              as double,
      trunkToleranceM: null == trunkToleranceM
          ? _value.trunkToleranceM
          : trunkToleranceM // ignore: cast_nullable_to_non_nullable
              as double,
      windowDurationS: null == windowDurationS
          ? _value.windowDurationS
          : windowDurationS // ignore: cast_nullable_to_non_nullable
              as double,
      thighPassed: null == thighPassed
          ? _value.thighPassed
          : thighPassed // ignore: cast_nullable_to_non_nullable
              as bool,
      shankPassed: null == shankPassed
          ? _value.shankPassed
          : shankPassed // ignore: cast_nullable_to_non_nullable
              as bool,
      trunkPassed: null == trunkPassed
          ? _value.trunkPassed
          : trunkPassed // ignore: cast_nullable_to_non_nullable
              as bool,
      overallPassed: null == overallPassed
          ? _value.overallPassed
          : overallPassed // ignore: cast_nullable_to_non_nullable
              as bool,
    ));
  }
}

/// @nodoc
@JsonSerializable()
class _$StabilityCheckResultImpl implements _StabilityCheckResult {
  const _$StabilityCheckResultImpl(
      {@JsonKey(name: 'thigh_variation_m') required this.thighVariationM,
      @JsonKey(name: 'shank_variation_m') required this.shankVariationM,
      @JsonKey(name: 'trunk_variation_m') required this.trunkVariationM,
      @JsonKey(name: 'thigh_tolerance_m') required this.thighToleranceM,
      @JsonKey(name: 'shank_tolerance_m') required this.shankToleranceM,
      @JsonKey(name: 'trunk_tolerance_m') required this.trunkToleranceM,
      @JsonKey(name: 'window_duration_s') required this.windowDurationS,
      @JsonKey(name: 'thigh_passed') required this.thighPassed,
      @JsonKey(name: 'shank_passed') required this.shankPassed,
      @JsonKey(name: 'trunk_passed') required this.trunkPassed,
      @JsonKey(name: 'overall_passed') required this.overallPassed});

  factory _$StabilityCheckResultImpl.fromJson(Map<String, dynamic> json) =>
      _$$StabilityCheckResultImplFromJson(json);

  @override
  @JsonKey(name: 'thigh_variation_m')
  final double thighVariationM;
  @override
  @JsonKey(name: 'shank_variation_m')
  final double shankVariationM;
  @override
  @JsonKey(name: 'trunk_variation_m')
  final double trunkVariationM;
  @override
  @JsonKey(name: 'thigh_tolerance_m')
  final double thighToleranceM;
  @override
  @JsonKey(name: 'shank_tolerance_m')
  final double shankToleranceM;
  @override
  @JsonKey(name: 'trunk_tolerance_m')
  final double trunkToleranceM;
  @override
  @JsonKey(name: 'window_duration_s')
  final double windowDurationS;
  @override
  @JsonKey(name: 'thigh_passed')
  final bool thighPassed;
  @override
  @JsonKey(name: 'shank_passed')
  final bool shankPassed;
  @override
  @JsonKey(name: 'trunk_passed')
  final bool trunkPassed;
  @override
  @JsonKey(name: 'overall_passed')
  final bool overallPassed;

  @override
  String toString() {
    return 'StabilityCheckResult(thighVariationM: $thighVariationM, shankVariationM: $shankVariationM, trunkVariationM: $trunkVariationM, thighToleranceM: $thighToleranceM, shankToleranceM: $shankToleranceM, trunkToleranceM: $trunkToleranceM, windowDurationS: $windowDurationS, thighPassed: $thighPassed, shankPassed: $shankPassed, trunkPassed: $trunkPassed, overallPassed: $overallPassed)';
  }

  @override
  bool operator ==(Object other) {
    return identical(this, other) ||
        (other.runtimeType == runtimeType &&
            other is _$StabilityCheckResultImpl &&
            (identical(other.thighVariationM, thighVariationM) ||
                other.thighVariationM == thighVariationM) &&
            (identical(other.shankVariationM, shankVariationM) ||
                other.shankVariationM == shankVariationM) &&
            (identical(other.trunkVariationM, trunkVariationM) ||
                other.trunkVariationM == trunkVariationM) &&
            (identical(other.thighToleranceM, thighToleranceM) ||
                other.thighToleranceM == thighToleranceM) &&
            (identical(other.shankToleranceM, shankToleranceM) ||
                other.shankToleranceM == shankToleranceM) &&
            (identical(other.trunkToleranceM, trunkToleranceM) ||
                other.trunkToleranceM == trunkToleranceM) &&
            (identical(other.windowDurationS, windowDurationS) ||
                other.windowDurationS == windowDurationS) &&
            (identical(other.thighPassed, thighPassed) ||
                other.thighPassed == thighPassed) &&
            (identical(other.shankPassed, shankPassed) ||
                other.shankPassed == shankPassed) &&
            (identical(other.trunkPassed, trunkPassed) ||
                other.trunkPassed == trunkPassed) &&
            (identical(other.overallPassed, overallPassed) ||
                other.overallPassed == overallPassed));
  }

  @JsonKey(includeFromJson: false, includeToJson: false)
  @override
  int get hashCode => Object.hash(
      runtimeType,
      thighVariationM,
      shankVariationM,
      trunkVariationM,
      thighToleranceM,
      shankToleranceM,
      trunkToleranceM,
      windowDurationS,
      thighPassed,
      shankPassed,
      trunkPassed,
      overallPassed);

  /// Create a copy of StabilityCheckResult
  /// with the given fields replaced by the non-null parameter values.
  @JsonKey(includeFromJson: false, includeToJson: false)
  @override
  @pragma('vm:prefer-inline')
  _$$StabilityCheckResultImplCopyWith<_$StabilityCheckResultImpl>
      get copyWith =>
          __$$StabilityCheckResultImplCopyWithImpl<_$StabilityCheckResultImpl>(
              this, _$identity);

  @override
  Map<String, dynamic> toJson() {
    return _$$StabilityCheckResultImplToJson(
      this,
    );
  }
}

abstract class _StabilityCheckResult implements StabilityCheckResult {
  const factory _StabilityCheckResult(
      {@JsonKey(name: 'thigh_variation_m')
      required final double thighVariationM,
      @JsonKey(name: 'shank_variation_m') required final double shankVariationM,
      @JsonKey(name: 'trunk_variation_m') required final double trunkVariationM,
      @JsonKey(name: 'thigh_tolerance_m') required final double thighToleranceM,
      @JsonKey(name: 'shank_tolerance_m') required final double shankToleranceM,
      @JsonKey(name: 'trunk_tolerance_m') required final double trunkToleranceM,
      @JsonKey(name: 'window_duration_s') required final double windowDurationS,
      @JsonKey(name: 'thigh_passed') required final bool thighPassed,
      @JsonKey(name: 'shank_passed') required final bool shankPassed,
      @JsonKey(name: 'trunk_passed') required final bool trunkPassed,
      @JsonKey(name: 'overall_passed')
      required final bool overallPassed}) = _$StabilityCheckResultImpl;

  factory _StabilityCheckResult.fromJson(Map<String, dynamic> json) =
      _$StabilityCheckResultImpl.fromJson;

  @override
  @JsonKey(name: 'thigh_variation_m')
  double get thighVariationM;
  @override
  @JsonKey(name: 'shank_variation_m')
  double get shankVariationM;
  @override
  @JsonKey(name: 'trunk_variation_m')
  double get trunkVariationM;
  @override
  @JsonKey(name: 'thigh_tolerance_m')
  double get thighToleranceM;
  @override
  @JsonKey(name: 'shank_tolerance_m')
  double get shankToleranceM;
  @override
  @JsonKey(name: 'trunk_tolerance_m')
  double get trunkToleranceM;
  @override
  @JsonKey(name: 'window_duration_s')
  double get windowDurationS;
  @override
  @JsonKey(name: 'thigh_passed')
  bool get thighPassed;
  @override
  @JsonKey(name: 'shank_passed')
  bool get shankPassed;
  @override
  @JsonKey(name: 'trunk_passed')
  bool get trunkPassed;
  @override
  @JsonKey(name: 'overall_passed')
  bool get overallPassed;

  /// Create a copy of StabilityCheckResult
  /// with the given fields replaced by the non-null parameter values.
  @override
  @JsonKey(includeFromJson: false, includeToJson: false)
  _$$StabilityCheckResultImplCopyWith<_$StabilityCheckResultImpl>
      get copyWith => throw _privateConstructorUsedError;
}
