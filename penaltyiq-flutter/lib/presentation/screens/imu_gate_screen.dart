import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../domain/providers/imu_provider.dart';
import '../../core/constants/app_constants.dart';
import '../painters/level_painter.dart';

/// Digital Level Tool Screen — Hard Gate for Camera Tilt.
///
/// [SPEC §1.7.1]: "The Record button is hidden/disabled unless the phone
/// is within a ±2° tolerance of the required upright orientation."
///
/// This screen BLOCKS navigation to the calibration screen until the
/// IMU confirms the phone is within tolerance.
///
/// UX design:
///   - Full-screen level with large bubble indicator.
///   - Real-time roll/pitch readouts.
///   - "LEVEL ✓" badge appears green when within ±2°.
///   - Continue button is enabled ONLY when isLevel == true.
///   - Haptic feedback when level is first achieved.
class ImuGateScreen extends ConsumerStatefulWidget {
  const ImuGateScreen({super.key});

  @override
  ConsumerState<ImuGateScreen> createState() => _ImuGateScreenState();
}

class _ImuGateScreenState extends ConsumerState<ImuGateScreen>
    with SingleTickerProviderStateMixin {

  late AnimationController _pulseController;
  late Animation<double> _pulseAnimation;
  bool _levelAchievedOnce = false;

  @override
  void initState() {
    super.initState();
    _pulseController = AnimationController(
      vsync: this,
      duration: const Duration(milliseconds: 800),
    )..repeat(reverse: true);
    _pulseAnimation = Tween<double>(begin: 0.95, end: 1.05).animate(
      CurvedAnimation(parent: _pulseController, curve: Curves.easeInOut),
    );
  }

  @override
  void dispose() {
    _pulseController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final imuState = ref.watch(imuTiltProvider);

    return Scaffold(
      backgroundColor: const Color(0xFF0A0A1A),
      appBar: AppBar(
        backgroundColor: Colors.transparent,
        elevation: 0,
        title: const Text(
          'Phone Level Check',
          style: TextStyle(color: Colors.white, fontSize: 18),
        ),
        centerTitle: true,
      ),
      body: imuState.when(
        loading: () => const _LoadingView(),
        error: (err, _) => _ErrorView(error: err.toString()),
        data: (tiltState) {
          // Haptic on first level achievement
          if (tiltState.isLevel && !_levelAchievedOnce) {
            _levelAchievedOnce = true;
            // Haptic feedback would go here in production:
            // HapticFeedback.mediumImpact();
          }

          return _LevelView(
            tiltState: tiltState,
            pulseAnimation: _pulseAnimation,
            onContinue: tiltState.isLevel
                ? () => context.go('/calibration')
                : null,
          );
        },
      ),
    );
  }
}

class _LevelView extends StatelessWidget {
  const _LevelView({
    required this.tiltState,
    required this.pulseAnimation,
    required this.onContinue,
  });

  final ImuTiltState tiltState;
  final Animation<double> pulseAnimation;
  final VoidCallback? onContinue;

  @override
  Widget build(BuildContext context) {
    return SafeArea(
      child: Padding(
        padding: const EdgeInsets.all(24.0),
        child: Column(
          children: [
            // ── Instruction text ─────────────────────────────────────────
            const _InstructionCard(),
            const SizedBox(height: 32),

            // ── Level indicator ───────────────────────────────────────────
            Expanded(
              child: Center(
                child: AnimatedBuilder(
                  animation: pulseAnimation,
                  builder: (context, child) {
                    return Transform.scale(
                      scale: tiltState.isLevel ? pulseAnimation.value : 1.0,
                      child: child,
                    );
                  },
                  child: SizedBox(
                    width: 260,
                    height: 260,
                    child: CustomPaint(
                      painter: LevelPainter(
                        rollDeg: tiltState.rollDeg,
                        pitchDeg: tiltState.pitchDeg,
                        isLevel: tiltState.isLevel,
                      ),
                    ),
                  ),
                ),
              ),
            ),

            // ── Readout panel ─────────────────────────────────────────────
            _TiltReadoutPanel(tiltState: tiltState),
            const SizedBox(height: 24),

            // ── Status badge ──────────────────────────────────────────────
            _StatusBadge(isLevel: tiltState.isLevel),
            const SizedBox(height: 24),

            // ── Continue button (hard gate) ───────────────────────────────
            _ContinueButton(onPressed: onContinue),
            const SizedBox(height: 16),
          ],
        ),
      ),
    );
  }
}

class _InstructionCard extends StatelessWidget {
  const _InstructionCard();

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: Colors.white.withOpacity(0.06),
        borderRadius: BorderRadius.circular(12),
        border: Border.all(color: Colors.white.withOpacity(0.12)),
      ),
      child: Row(
        children: [
          const Icon(Icons.info_outline, color: Color(0xFF64B5F6), size: 20),
          const SizedBox(width: 12),
          Expanded(
            child: Text(
              'Hold your phone vertically at 90° to the sagittal plane.\n'
              'The bubble must be centred within ±${AppConstants.imuTiltToleranceDeg.toStringAsFixed(0)}° to continue.',
              style: TextStyle(
                color: Colors.white.withOpacity(0.85),
                fontSize: 13,
                height: 1.5,
              ),
            ),
          ),
        ],
      ),
    );
  }
}

class _TiltReadoutPanel extends StatelessWidget {
  const _TiltReadoutPanel({required this.tiltState});

  final ImuTiltState tiltState;

  @override
  Widget build(BuildContext context) {
    return Row(
      mainAxisAlignment: MainAxisAlignment.spaceEvenly,
      children: [
        _TiltReadout(
          label: 'ROLL',
          value: tiltState.rollDeg,
          withinTolerance: tiltState.rollDeg.abs() <=
              AppConstants.imuTiltToleranceDeg,
        ),
        _TiltReadout(
          label: 'PITCH',
          value: tiltState.pitchDeg,
          withinTolerance: tiltState.pitchDeg.abs() <=
              AppConstants.imuTiltToleranceDeg,
        ),
      ],
    );
  }
}

class _TiltReadout extends StatelessWidget {
  const _TiltReadout({
    required this.label,
    required this.value,
    required this.withinTolerance,
  });

  final String label;
  final double value;
  final bool withinTolerance;

  @override
  Widget build(BuildContext context) {
    return Column(
      children: [
        Text(
          label,
          style: const TextStyle(
            color: Colors.white54,
            fontSize: 11,
            letterSpacing: 1.5,
          ),
        ),
        const SizedBox(height: 4),
        Text(
          '${value >= 0 ? '+' : ''}${value.toStringAsFixed(1)}°',
          style: TextStyle(
            color: withinTolerance
                ? const Color(0xFF4CAF50)
                : const Color(0xFFF44336),
            fontSize: 28,
            fontWeight: FontWeight.bold,
            fontFeatures: const [FontFeature.tabularFigures()],
          ),
        ),
      ],
    );
  }
}

class _StatusBadge extends StatelessWidget {
  const _StatusBadge({required this.isLevel});

  final bool isLevel;

  @override
  Widget build(BuildContext context) {
    return AnimatedContainer(
      duration: const Duration(milliseconds: 300),
      padding: const EdgeInsets.symmetric(horizontal: 24, vertical: 10),
      decoration: BoxDecoration(
        color: isLevel
            ? const Color(0xFF4CAF50).withOpacity(0.2)
            : const Color(0xFFF44336).withOpacity(0.15),
        borderRadius: BorderRadius.circular(30),
        border: Border.all(
          color: isLevel
              ? const Color(0xFF4CAF50)
              : const Color(0xFFF44336).withOpacity(0.6),
          width: 1.5,
        ),
      ),
      child: Row(
        mainAxisSize: MainAxisSize.min,
        children: [
          Icon(
            isLevel ? Icons.check_circle : Icons.radio_button_unchecked,
            color: isLevel
                ? const Color(0xFF4CAF50)
                : const Color(0xFFF44336),
            size: 18,
          ),
          const SizedBox(width: 8),
          Text(
            isLevel ? 'LEVEL — READY' : 'ADJUSTING...',
            style: TextStyle(
              color: isLevel
                  ? const Color(0xFF4CAF50)
                  : const Color(0xFFF44336),
              fontSize: 13,
              fontWeight: FontWeight.w700,
              letterSpacing: 1.2,
            ),
          ),
        ],
      ),
    );
  }
}

class _ContinueButton extends StatelessWidget {
  const _ContinueButton({required this.onPressed});

  final VoidCallback? onPressed;

  @override
  Widget build(BuildContext context) {
    return SizedBox(
      width: double.infinity,
      height: 56,
      child: ElevatedButton(
        onPressed: onPressed,
        style: ElevatedButton.styleFrom(
          backgroundColor: onPressed != null
              ? const Color(0xFF4CAF50)
              : Colors.grey.shade800,
          foregroundColor: Colors.white,
          shape: RoundedRectangleBorder(
            borderRadius: BorderRadius.circular(14),
          ),
          elevation: onPressed != null ? 4 : 0,
        ),
        child: Text(
          onPressed != null ? 'CONTINUE TO CALIBRATION' : 'LEVEL PHONE FIRST',
          style: const TextStyle(
            fontSize: 14,
            fontWeight: FontWeight.w700,
            letterSpacing: 1.0,
          ),
        ),
      ),
    );
  }
}

class _LoadingView extends StatelessWidget {
  const _LoadingView();

  @override
  Widget build(BuildContext context) {
    return const Center(
      child: Column(
        mainAxisSize: MainAxisSize.min,
        children: [
          CircularProgressIndicator(color: Colors.white54),
          SizedBox(height: 16),
          Text(
            'Initialising IMU sensor...',
            style: TextStyle(color: Colors.white54),
          ),
        ],
      ),
    );
  }
}

class _ErrorView extends StatelessWidget {
  const _ErrorView({required this.error});

  final String error;

  @override
  Widget build(BuildContext context) {
    return Center(
      child: Padding(
        padding: const EdgeInsets.all(24),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            const Icon(Icons.sensors_off, color: Colors.red, size: 48),
            const SizedBox(height: 16),
            const Text(
              'IMU Sensor Unavailable',
              style: TextStyle(
                color: Colors.white,
                fontSize: 18,
                fontWeight: FontWeight.bold,
              ),
            ),
            const SizedBox(height: 8),
            Text(
              error,
              style: const TextStyle(color: Colors.white54, fontSize: 13),
              textAlign: TextAlign.center,
            ),
          ],
        ),
      ),
    );
  }
}