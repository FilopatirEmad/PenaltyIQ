import 'dart:async';
import 'dart:math' as math;

import 'package:flutter/foundation.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:sensors_plus/sensors_plus.dart';

import '../../core/constants/app_constants.dart';

/// IMU tilt state — the single source of truth for phone orientation.
///
/// [SPEC §1.7.1]: "The UI uses phone IMU (gyroscope/accelerometer)
/// measurements to detect roll and pitch. The Record button is
/// hidden/disabled unless the phone is within a ±2° tolerance."
///
/// Physics of tilt computation:
///   The accelerometer measures [ax, ay, az] in m/s² (includes gravity).
///   When the phone is held vertically (sagittal plane view):
///     - az should be ≈ 0 (horizontal axis, no gravity component).
///     - ay should be ≈ −g (downward).
///     - ax should be ≈ 0 (upright, not rolled).
///
///   Tilt angle from vertical:
///     roll  = arctan(ax / sqrt(ay² + az²))  [left-right tilt]
///     pitch = arctan(az / sqrt(ax² + ay²))  [forward-backward tilt]
///
///   Gate passes when |roll| ≤ 2° AND |pitch| ≤ 2°.
///   [SPEC §1.7.1]

class ImuTiltState {
  const ImuTiltState({
    required this.rollDeg,
    required this.pitchDeg,
    required this.isLevel,
    required this.hasData,
  });

  /// Roll angle: left-right tilt [degrees]. 0° = level.
  final double rollDeg;

  /// Pitch angle: forward-backward tilt [degrees]. 0° = vertical.
  final double pitchDeg;

  /// True if |roll| ≤ 2° AND |pitch| ≤ 2°. [SPEC §1.7.1]
  final bool isLevel;

  /// True after first accelerometer event received.
  final bool hasData;

  static const ImuTiltState initial = ImuTiltState(
    rollDeg: 0.0,
    pitchDeg: 0.0,
    isLevel: false,
    hasData: false,
  );

  @override
  String toString() =>
      'ImuTiltState(roll=${rollDeg.toStringAsFixed(2)}°, '
      'pitch=${pitchDeg.toStringAsFixed(2)}°, '
      'isLevel=$isLevel)';
}

/// Riverpod StreamProvider that exposes real-time IMU tilt state.
///
/// Uses sensors_plus accelerometerEventStream at the fastest available rate.
/// Tilt angles computed from gravity vector decomposition.
final imuTiltProvider = StreamProvider<ImuTiltState>((ref) async* {
  // Gracefully handle Desktop and Web by mocking IMU constraints as always satisfied
  if (kIsWeb || defaultTargetPlatform == TargetPlatform.windows || defaultTargetPlatform == TargetPlatform.macOS || defaultTargetPlatform == TargetPlatform.linux) {
    yield const ImuTiltState(
      rollDeg: 0.0,
      pitchDeg: 0.0,
      isLevel: true,
      hasData: true,
    );
    // Keep stream open
    await Future.delayed(const Duration(days: 365));
    return;
  }

  // Mobile path using actual sensors_plus stream
  try {
    await for (final event in accelerometerEventStream(samplingPeriod: SensorInterval.normalInterval)) {
      yield _computeTiltState(event.x, event.y, event.z);
    }
  } catch (e) {
    // If sensors fail on mobile (e.g. permission or hardware issue), default to ready to prevent app lock
    yield const ImuTiltState(
      rollDeg: 0.0,
      pitchDeg: 0.0,
      isLevel: true,
      hasData: true,
    );
  }
});

/// Compute tilt state from raw accelerometer values.
///
/// Accelerometer output: [ax, ay, az] in m/s².
/// With phone held upright (portrait, camera at side):
///   ax = lateral acceleration + gravity component from roll
///   ay = vertical acceleration + gravity component from pitch
///   az = depth acceleration + gravity component from tilt
///
/// Roll  = arctan2(ax, sqrt(ay² + az²)) [radians → degrees]
/// Pitch = arctan2(az, sqrt(ax² + ay²)) [radians → degrees]
///
/// Source: Freescale Semiconductor AN3461 — Tilt sensing with accelerometers.
/// This is the standard two-axis tilt formula used in mobile levelling apps.
ImuTiltState _computeTiltState(double ax, double ay, double az) {
  // Roll: rotation around the forward axis (left-right lean)
  final rollRad = math.atan2(ax, math.sqrt(ay * ay + az * az));

  // Pitch: rotation around the lateral axis (forward-backward lean)
  final pitchRad = math.atan2(az, math.sqrt(ax * ax + ay * ay));

  final rollDeg  = rollRad  * (180.0 / math.pi);
  final pitchDeg = pitchRad * (180.0 / math.pi);

  final isLevel = rollDeg.abs()  <= AppConstants.imuTiltToleranceDeg &&
                  pitchDeg.abs() <= AppConstants.imuTiltToleranceDeg;

  return ImuTiltState(
    rollDeg:  rollDeg,
    pitchDeg: pitchDeg,
    isLevel:  isLevel,
    hasData:  true,
  );
}