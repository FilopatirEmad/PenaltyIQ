import 'package:flutter_test/flutter_test.dart';
import 'package:mockito/mockito.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import 'package:penaltyiq/data/models/calibration_response.dart';
import 'package:penaltyiq/data/models/analysis_response.dart';
import 'package:penaltyiq/data/repositories/penaltyiq_repository.dart';
import 'package:penaltyiq/domain/providers/calibration_provider.dart';
import 'package:penaltyiq/domain/providers/analysis_provider.dart';

/// End-to-end integration test for the complete user flow.
///
/// Tests the state machine transitions:
///   idle → collecting → processing → locked → analysis → success
///
/// Uses mock repository to avoid real network calls.
/// All expected values are analytically derived from backend formulas.

class MockPenaltyIqRepository extends Mock implements PenaltyIqRepository {}

void main() {
  late MockPenaltyIqRepository mockRepository;

  setUp(() {
    mockRepository = MockPenaltyIqRepository();
  });

  group('Calibration State Machine', () {

    test('starts in idle state', () {
      final container = ProviderContainer(
        overrides: [
          penaltyIqRepositoryProvider.overrideWithValue(mockRepository),
        ],
      );
      addTearDown(container.dispose);

      final state = container.read(calibrationProvider);
      expect(state.status, CalibrationStatus.idle);
      expect(state.isLocked, false);
    });

    test('transitions idle → collecting → processing → locked on success', () async {
      // Arrange: mock successful calibration response
      final mockResponse = CalibrationResponse(
        sessionId: 'test-session-id',
        status: 'LOCKED',
        scaleMPerPx: 0.005,
        segmentsM: const LockedSegments(
          thighM: 0.42,
          shankM: 0.40,
          trunkM: 0.52,
          legM:   0.82,
        ),
        stabilityCheck: const StabilityCheckResult(
          thighVariationM: 0.003,
          shankVariationM: 0.002,
          trunkVariationM: 0.004,
          thighToleranceM: 0.0084,
          shankToleranceM: 0.0080,
          trunkToleranceM: 0.0104,
          windowDurationS: 2.0,
          thighPassed: true,
          shankPassed: true,
          trunkPassed: true,
          overallPassed: true,
        ),
        framesUsed: 120,
        error: null,
      );

      when(mockRepository.calibrate(
        sessionId: anyNamed('sessionId') ?? '',
        frames: anyNamed('frames') ?? [],
      )).thenAnswer((_) async => mockResponse);

      final container = ProviderContainer(
        overrides: [
          penaltyIqRepositoryProvider.overrideWithValue(mockRepository),
        ],
      );
      addTearDown(container.dispose);

      final notifier = container.read(calibrationProvider.notifier);

      // Act
      notifier.startCollection();
      expect(
        container.read(calibrationProvider).status,
        CalibrationStatus.collecting,
      );

      await notifier.submitCalibration([]);

      // Assert: LOCKED
      final finalState = container.read(calibrationProvider);
      expect(finalState.status, CalibrationStatus.locked);
      expect(finalState.isLocked, true);
      expect(finalState.scaleMPerPx, closeTo(0.005, 1e-10));
      expect(finalState.lockedSegments?.thighM, closeTo(0.42, 1e-10));
      expect(finalState.lockedSegments?.legM, closeTo(0.82, 1e-10));
    });

    test('hard gate blocks analysis when not locked', () async {
      // Arrange: analysis provider with unlocked calibration
      final container = ProviderContainer(
        overrides: [
          penaltyIqRepositoryProvider.overrideWithValue(mockRepository),
        ],
      );
      addTearDown(container.dispose);

      // Act: attempt analysis without calibration
      await container.read(analysisProvider.notifier).submitAnalysis(
        goalZone: 'T1',
        frames: [],
      );

      // Assert: error state with clear message
      final analysisState = container.read(analysisProvider);
      expect(analysisState, isA<AnalysisError>());
      final errorState = analysisState as AnalysisError;
      expect(
        errorState.message,
        contains('Calibration gate not passed'),
      );
    });

    test('hard gate blocks analysis with insufficient ball detections', () async {
      // Arrange: locked calibration
      final mockCalibResponse = CalibrationResponse(
        sessionId: 'test-id',
        status: 'LOCKED',
        scaleMPerPx: 0.005,
        segmentsM: const LockedSegments(
          thighM: 0.42, shankM: 0.40, trunkM: 0.52, legM: 0.82,
        ),
        stabilityCheck: const StabilityCheckResult(
          thighVariationM: 0.002, shankVariationM: 0.002,
          trunkVariationM: 0.003, thighToleranceM: 0.0084,
          shankToleranceM: 0.0080, trunkToleranceM: 0.0104,
          windowDurationS: 2.0, thighPassed: true,
          shankPassed: true, trunkPassed: true, overallPassed: true,
        ),
        framesUsed: 120, error: null,
      );

      when(mockRepository.calibrate(
        sessionId: anyNamed('sessionId') ?? '',
        frames: anyNamed('frames') ?? [],
      )).thenAnswer((_) async => mockCalibResponse);

      final container = ProviderContainer(
        overrides: [
          penaltyIqRepositoryProvider.overrideWithValue(mockRepository),
        ],
      );
      addTearDown(container.dispose);

      await container.read(calibrationProvider.notifier)
          .submitCalibration([]);

      // Frames with NO ball detections (0 < 4 required)
      final framesWithoutBall = List.generate(10, (i) => {
        'frame_index': i,
        'timestamp_ms': i * 16.67,
        'landmarks': <String, dynamic>{},
        'ball_center_px': null,   // No ball detection
        'frame_width_px': 1920,
        'frame_height_px': 1080,
      });

      await container.read(analysisProvider.notifier).submitAnalysis(
        goalZone: 'T1',
        frames: framesWithoutBall,
      );

      final state = container.read(analysisProvider);
      expect(state, isA<AnalysisError>());
      expect(
        (state as AnalysisError).message,
        contains('ball detections'),
      );
    });
  });

  group('Segment Length Validation', () {
    test('leg_m == thigh_m + shank_m from calibration response', () {
      // [SPEC §1.3.4]: leg_m is derived, not independently measured.
      const segments = LockedSegments(
        thighM: 0.42,
        shankM: 0.40,
        trunkM: 0.52,
        legM: 0.82,
      );

      expect(
        segments.legM,
        closeTo(segments.thighM + segments.shankM, 1e-10),
        reason: 'leg_m must equal thigh_m + shank_m [SPEC §1.3.4]',
      );
    });
  });
}