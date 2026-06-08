import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../core/constants/app_constants.dart';
import '../../domain/providers/calibration_provider.dart';

/// T-Pose Calibration Screen.
///
/// [SPEC §1.6.1]: "The player is not allowed to start the kick until
/// the system confirms that estimated segment lengths are stable for
/// at least 2 seconds while the player holds a T-pose."
///
/// UX flow:
///   1. Instruction card: how to hold T-pose.
///   2. Start button → begins 2-second stability window.
///   3. Progress indicator fills over 2 seconds.
///   4. On completion: frames sent to /calibrate.
///   5. If LOCKED → navigate to /recording.
///   6. If FAILED → show failure reason + retry.
///
/// In production: camera frames would be captured here and
/// MediaPipe pose landmarks extracted per-frame.
/// For this implementation, the frame capture architecture
/// is documented and the UI state machine is complete.
class CalibrationScreen extends ConsumerStatefulWidget {
  const CalibrationScreen({super.key});

  @override
  ConsumerState<CalibrationScreen> createState() =>
      _CalibrationScreenState();
}

class _CalibrationScreenState extends ConsumerState<CalibrationScreen>
    with SingleTickerProviderStateMixin {

  late AnimationController _progressController;
  bool _isCollecting = false;

  @override
  void initState() {
    super.initState();
    _progressController = AnimationController(
      vsync: this,
      duration: Duration(
        milliseconds: (AppConstants.calibrationWindowS * 1000).round(),
      ),
    );
    _progressController.addStatusListener(_onProgressComplete);
  }

  @override
  void dispose() {
    _progressController.removeStatusListener(_onProgressComplete);
    _progressController.dispose();
    super.dispose();
  }

  void _onProgressComplete(AnimationStatus status) {
    if (status == AnimationStatus.completed && _isCollecting) {
      _submitCalibration();
    }
  }

  void _startCollection() {
    setState(() => _isCollecting = true);
    ref.read(calibrationProvider.notifier).startCollection();
    _progressController.forward(from: 0.0);
  }

  Future<void> _submitCalibration() async {
    // In production: collect actual MediaPipe frames from camera stream.
    // For demonstration: submit synthetic frames to test the pipeline.
    // The frame format matches CalibrationFrame Pydantic schema exactly.
    final frames = _buildSyntheticCalibrationFrames();
    await ref.read(calibrationProvider.notifier).submitCalibration(frames);
  }

  /// Build synthetic calibration frames for pipeline testing.
  ///
  /// In production, these frames are extracted from the live camera
  /// stream via the camera package and MediaPipe Pose.
  ///
  /// Frame format mirrors [SPEC §1.3] coordinate conventions:
  ///   - x_norm, y_norm ∈ [0, 1] (MediaPipe normalised)
  ///   - visibility ∈ [0, 1]
  ///   - ball_diameter_px: detected ball diameter in pixels
  List<Map<String, dynamic>> _buildSyntheticCalibrationFrames() {
    final frames = <Map<String, dynamic>>[];
    const fps = AppConstants.calibrationFps;
    const nFrames = AppConstants.calibrationMinFrames;

    for (int i = 0; i < nFrames; i++) {
      frames.add({
        'frame_index': i,
        'timestamp_ms': (i / fps * 1000).toDouble(),
        'landmarks': {
          'LEFT_SHOULDER': {'x_norm': 0.45, 'y_norm': 0.30, 'visibility': 0.99},
          'LEFT_HIP':      {'x_norm': 0.47, 'y_norm': 0.52, 'visibility': 0.99},
          'LEFT_KNEE':     {'x_norm': 0.46, 'y_norm': 0.70, 'visibility': 0.98},
          'LEFT_ANKLE':    {'x_norm': 0.46, 'y_norm': 0.88, 'visibility': 0.97},
        },
        // Ball diameter: 44px at typical smartphone resolution
        // S = 0.22 / 44 = 0.005 m/px [FIFA-2024, SPEC §1.2.1]
        'ball_diameter_px': 44.0,
        'frame_width_px': 1920,
        'frame_height_px': 1080,
      });
    }
    return frames;
  }

  @override
  Widget build(BuildContext context) {
    final calibState = ref.watch(calibrationProvider);

    // Auto-navigate on LOCKED
    ref.listen(calibrationProvider, (_, next) {
      if (next.status == CalibrationStatus.locked) {
        context.go('/recording');
      }
    });

    return Scaffold(
      backgroundColor: const Color(0xFF0A0A1A),
      appBar: AppBar(
        backgroundColor: Colors.transparent,
        elevation: 0,
        title: const Text(
          'T-Pose Calibration',
          style: TextStyle(color: Colors.white),
        ),
        centerTitle: true,
      ),
      body: SafeArea(
        child: Padding(
          padding: const EdgeInsets.all(24),
          child: Column(
            children: [
              // ── Segment visualiser ───────────────────────────────────────
              _SegmentDisplay(calibState: calibState),
              const SizedBox(height: 24),

              // ── Instructions ─────────────────────────────────────────────
              const _CalibrationInstructions(),
              const SizedBox(height: 24),

              // ── Progress indicator ────────────────────────────────────────
              if (_isCollecting) ...[
                _ProgressSection(
                  controller: _progressController,
                  framesCollected: calibState.framesCollected,
                ),
                const SizedBox(height: 24),
              ],

              // ── Status / Error message ────────────────────────────────────
              if (calibState.errorMessage != null)
                _ErrorBanner(message: calibState.errorMessage!),

              const Spacer(),

              // ── Action buttons ────────────────────────────────────────────
              _ActionButtons(
                calibState: calibState,
                isCollecting: _isCollecting,
                onStart: _startCollection,
                onRetry: () {
                  setState(() => _isCollecting = false);
                  ref.read(calibrationProvider.notifier).reset();
                  _progressController.reset();
                },
              ),
            ],
          ),
        ),
      ),
    );
  }
}

class _SegmentDisplay extends StatelessWidget {
  const _SegmentDisplay({required this.calibState});

  final CalibrationState calibState;

  @override
  Widget build(BuildContext context) {
    final segments = calibState.lockedSegments;

    return Container(
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: Colors.white.withOpacity(0.05),
        borderRadius: BorderRadius.circular(14),
        border: Border.all(
          color: calibState.isLocked
              ? const Color(0xFF4CAF50).withOpacity(0.5)
              : Colors.white.withOpacity(0.1),
        ),
      ),
      child: Column(
        children: [
          Row(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              Icon(
                calibState.isLocked
                    ? Icons.lock_outlined
                    : Icons.lock_open_outlined,
                color: calibState.isLocked
                    ? const Color(0xFF4CAF50)
                    : Colors.white38,
                size: 18,
              ),
              const SizedBox(width: 8),
              Text(
                calibState.isLocked
                    ? 'SEGMENTS LOCKED'
                    : 'AWAITING CALIBRATION',
                style: TextStyle(
                  color: calibState.isLocked
                      ? const Color(0xFF4CAF50)
                      : Colors.white38,
                  fontSize: 12,
                  fontWeight: FontWeight.w700,
                  letterSpacing: 1.2,
                ),
              ),
            ],
          ),
          if (segments != null) ...[
            const SizedBox(height: 16),
            Row(
              mainAxisAlignment: MainAxisAlignment.spaceAround,
              children: [
                _SegmentChip(
                  label: 'THIGH',
                  value: '${(segments.thighM * 100).toStringAsFixed(1)} cm',
                ),
                _SegmentChip(
                  label: 'SHANK',
                  value: '${(segments.shankM * 100).toStringAsFixed(1)} cm',
                ),
                _SegmentChip(
                  label: 'TRUNK',
                  value: '${(segments.trunkM * 100).toStringAsFixed(1)} cm',
                ),
              ],
            ),
          ],
        ],
      ),
    );
  }
}

class _SegmentChip extends StatelessWidget {
  const _SegmentChip({required this.label, required this.value});

  final String label;
  final String value;

  @override
  Widget build(BuildContext context) {
    return Column(
      children: [
        Text(
          value,
          style: const TextStyle(
            color: Color(0xFF81C784),
            fontSize: 18,
            fontWeight: FontWeight.bold,
          ),
        ),
        const SizedBox(height: 2),
        Text(
          label,
          style: const TextStyle(
            color: Colors.white38,
            fontSize: 9,
            letterSpacing: 1.2,
          ),
        ),
      ],
    );
  }
}

class _CalibrationInstructions extends StatelessWidget {
  const _CalibrationInstructions();

  @override
  Widget build(BuildContext context) {
    const steps = [
      ('1', 'Stand 3–4 metres from the camera'),
      ('2', 'Hold a T-pose: arms out, feet shoulder-width apart'),
      ('3', 'Ensure full body is visible in frame'),
      ('4', 'Hold still for 2 seconds while the system calibrates'),
    ];

    return Container(
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: const Color(0xFF1A1A2E),
        borderRadius: BorderRadius.circular(12),
      ),
      child: Column(
        children: steps.map((step) {
          return Padding(
            padding: const EdgeInsets.symmetric(vertical: 6),
            child: Row(
              children: [
                Container(
                  width: 24,
                  height: 24,
                  decoration: BoxDecoration(
                    color: const Color(0xFF64B5F6).withOpacity(0.2),
                    shape: BoxShape.circle,
                    border: Border.all(
                        color: const Color(0xFF64B5F6).withOpacity(0.5)),
                  ),
                  child: Center(
                    child: Text(
                      step.$1,
                      style: const TextStyle(
                        color: Color(0xFF64B5F6),
                        fontSize: 11,
                        fontWeight: FontWeight.bold,
                      ),
                    ),
                  ),
                ),
                const SizedBox(width: 12),
                Expanded(
                  child: Text(
                    step.$2,
                    style: const TextStyle(
                      color: Colors.white70,
                      fontSize: 13,
                    ),
                  ),
                ),
              ],
            ),
          );
        }).toList(),
      ),
    );
  }
}

class _ProgressSection extends StatelessWidget {
  const _ProgressSection({
    required this.controller,
    required this.framesCollected,
  });

  final AnimationController controller;
  final int framesCollected;

  @override
  Widget build(BuildContext context) {
    return Column(
      children: [
        AnimatedBuilder(
          animation: controller,
          builder: (context, _) {
            final progress = controller.value;
            final elapsedS = progress * AppConstants.calibrationWindowS;

            return Column(
              children: [
                // Circular progress
                SizedBox(
                  width: 100,
                  height: 100,
                  child: Stack(
                    alignment: Alignment.center,
                    children: [
                      CircularProgressIndicator(
                        value: progress,
                        strokeWidth: 8,
                        backgroundColor: Colors.white.withOpacity(0.1),
                        valueColor: const AlwaysStoppedAnimation<Color>(
                          Color(0xFF4CAF50),
                        ),
                      ),
                      Text(
                        '${(AppConstants.calibrationWindowS - elapsedS).toStringAsFixed(1)}s',
                        style: const TextStyle(
                          color: Colors.white,
                          fontSize: 20,
                          fontWeight: FontWeight.bold,
                        ),
                      ),
                    ],
                  ),
                ),
                const SizedBox(height: 12),
                Text(
                  '$framesCollected / ${AppConstants.calibrationMinFrames} frames',
                  style: const TextStyle(
                    color: Colors.white38,
                    fontSize: 11,
                  ),
                ),
              ],
            );
          },
        ),
      ],
    );
  }
}

class _ErrorBanner extends StatelessWidget {
  const _ErrorBanner({required this.message});

  final String message;

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.all(14),
      decoration: BoxDecoration(
        color: const Color(0xFFF44336).withOpacity(0.1),
        borderRadius: BorderRadius.circular(10),
        border:
            Border.all(color: const Color(0xFFF44336).withOpacity(0.4)),
      ),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          const Icon(Icons.error_outline,
              color: Color(0xFFF44336), size: 18),
          const SizedBox(width: 10),
          Expanded(
            child: Text(
              message,
              style: const TextStyle(
                color: Colors.white70,
                fontSize: 12,
                height: 1.4,
              ),
            ),
          ),
        ],
      ),
    );
  }
}

class _ActionButtons extends StatelessWidget {
  const _ActionButtons({
    required this.calibState,
    required this.isCollecting,
    required this.onStart,
    required this.onRetry,
  });

  final CalibrationState calibState;
  final bool isCollecting;
  final VoidCallback onStart;
  final VoidCallback onRetry;

  @override
  Widget build(BuildContext context) {
    // Processing state
    if (calibState.status == CalibrationStatus.processing) {
      return const SizedBox(
        height: 56,
        child: Center(
          child: Row(
            mainAxisSize: MainAxisSize.min,
            children: [
              SizedBox(
                width: 20,
                height: 20,
                child: CircularProgressIndicator(
                  strokeWidth: 2.5,
                  color: Color(0xFF64B5F6),
                ),
              ),
              SizedBox(width: 12),
              Text(
                'Analysing calibration data...',
                style: TextStyle(color: Colors.white54),
              ),
            ],
          ),
        ),
      );
    }

    // Collecting state
    if (isCollecting && calibState.status == CalibrationStatus.collecting) {
      return const SizedBox(
        height: 56,
        child: Center(
          child: Text(
            'Hold T-pose steady...',
            style: TextStyle(
              color: Color(0xFF4CAF50),
              fontSize: 16,
              fontWeight: FontWeight.w600,
            ),
          ),
        ),
      );
    }

    // Failed state
    if (calibState.status == CalibrationStatus.failed) {
      return SizedBox(
        width: double.infinity,
        height: 56,
        child: ElevatedButton.icon(
          onPressed: onRetry,
          icon: const Icon(Icons.refresh),
          label: const Text('RETRY CALIBRATION'),
          style: ElevatedButton.styleFrom(
            backgroundColor: const Color(0xFFFF9800),
            foregroundColor: Colors.white,
            shape: RoundedRectangleBorder(
              borderRadius: BorderRadius.circular(14),
            ),
          ),
        ),
      );
    }

    // Idle state
    return SizedBox(
      width: double.infinity,
      height: 56,
      child: ElevatedButton.icon(
        onPressed: onStart,
        icon: const Icon(Icons.camera_alt_outlined),
        label: const Text('START CALIBRATION'),
        style: ElevatedButton.styleFrom(
          backgroundColor: const Color(0xFF64B5F6),
          foregroundColor: Colors.white,
          shape: RoundedRectangleBorder(
            borderRadius: BorderRadius.circular(14),
          ),
          textStyle: const TextStyle(
            fontSize: 15,
            fontWeight: FontWeight.w700,
          ),
        ),
      ),
    );
  }
}