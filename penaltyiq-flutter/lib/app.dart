import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:shared_preferences/shared_preferences.dart';

import 'domain/providers/imu_provider.dart';
import 'domain/providers/calibration_provider.dart';
import 'domain/providers/analysis_provider.dart';
import 'presentation/screens/home_screen.dart';
import 'presentation/screens/imu_gate_screen.dart';
import 'presentation/screens/calibration_screen.dart';
import 'presentation/screens/recording_screen.dart';
import 'presentation/screens/results_screen.dart';
import 'presentation/screens/onboarding_screen.dart';
import 'core/theme/app_theme.dart';

final sharedPrefsProvider = Provider<SharedPreferences>((ref) => throw UnimplementedError());

/// GoRouter configuration with hard gate redirect guards.
///
/// Guard logic:
///   [SPEC §1.7.1] IMU gate:
///     /calibration, /recording → redirect to /imu-gate if !isLevel
///
///   [SPEC §1.6.1] Calibration gate:
///     /recording → redirect to /calibration if !isLocked
///
///   Results guard:
///     /results → redirect to /home if no analysis result

final routerProvider = Provider<GoRouter>((ref) {
  // Reactive listenable for router refresh
  final routerNotifier = _RouterNotifier(ref);

  return GoRouter(
    initialLocation: '/home',
    refreshListenable: routerNotifier,
    redirect: (BuildContext context, GoRouterState state) {
      final hasSeenOnboarding = ref.read(sharedPrefsProvider).getBool('has_seen_onboarding') ?? false;
      final location = state.matchedLocation;

      if (!hasSeenOnboarding && location != '/onboarding') {
        return '/onboarding';
      }
      if (hasSeenOnboarding && location == '/onboarding') {
        return '/home';
      }

      final imuAsync    = ref.read(imuTiltProvider);
      final calibState  = ref.read(calibrationProvider);
      final analysisState = ref.read(analysisProvider);

      final isLevel   = imuAsync.valueOrNull?.isLevel ?? false;
      final isLocked  = calibState.isLocked;
      final hasResult = analysisState is AnalysisSuccess;

      // ── IMU hard gate: blocks calibration and recording ───────────────
      // [SPEC §1.7.1]
      if ((location == '/calibration' || location == '/recording') &&
          !isLevel) {
        return '/imu-gate';
      }

      // ── Calibration hard gate: blocks recording ───────────────────────
      // [SPEC §1.6.1]
      if (location == '/recording' && !isLocked) {
        return '/calibration';
      }

      // ── Results guard ─────────────────────────────────────────────────
      if (location == '/results' && !hasResult) {
        return '/home';
      }

      return null; // No redirect
    },
    routes: [
      GoRoute(
        path: '/onboarding',
        name: 'onboarding',
        builder: (_, __) => const OnboardingScreen(),
      ),
      GoRoute(
        path: '/home',
        name: 'home',
        builder: (_, __) => const HomeScreen(),
      ),
      GoRoute(
        path: '/imu-gate',
        name: 'imu-gate',
        builder: (_, __) => const ImuGateScreen(),
      ),
      GoRoute(
        path: '/calibration',
        name: 'calibration',
        builder: (_, __) => const CalibrationScreen(),
      ),
      GoRoute(
        path: '/recording',
        name: 'recording',
        builder: (_, state) {
          final zone = state.uri.queryParameters['zone'] ?? 'B3';
          return RecordingScreen(goalZone: zone);
        },
      ),
      GoRoute(
        path: '/results',
        name: 'results',
        builder: (_, __) => const ResultsScreen(),
      ),
    ],
  );
});

/// ChangeNotifier that triggers router refresh when relevant providers change.
class _RouterNotifier extends ChangeNotifier {
  _RouterNotifier(this._ref) {
    _ref.listen(imuTiltProvider,       (_, __) => notifyListeners());
    _ref.listen(calibrationProvider,   (_, __) => notifyListeners());
    _ref.listen(analysisProvider,      (_, __) => notifyListeners());
  }
  final Ref _ref;
}

class PenaltyIqApp extends ConsumerWidget {
  const PenaltyIqApp({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final router = ref.watch(routerProvider);

    return MaterialApp.router(
      title: 'PenaltyIQ — Performance Lab',
      theme: PiqTheme.dark,
      routerConfig: router,
      debugShowCheckedModeBanner: false,
    );
  }
}