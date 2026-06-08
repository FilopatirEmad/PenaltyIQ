import 'package:flutter/material.dart';

/// Custom painter for the pose skeleton overlay.
///
/// Renders MediaPipe Pose landmarks and connecting segments
/// onto the camera preview frame.
///
/// [SPEC §1.7.2]: "The UI displays a semi-transparent skeleton overlay
/// and standing-position guide."
///
/// Landmark index convention: MediaPipe Pose (33 landmarks).
/// Connections defined for lower body + trunk (relevant to kick analysis).
///
/// Segment connections drawn [WINTER-2009 Ch.3]:
///   - Left hip → Left knee (thigh)
///   - Left knee → Left ankle (shank)
///   - Left shoulder → Left hip (trunk)
///   - Right hip → Right knee (support thigh)
///   - Right knee → Right ankle (support shank)
///   - Left shoulder → Right shoulder (shoulder line)
///   - Left hip → Right hip (hip line)
class SkeletonPainter extends CustomPainter {
  const SkeletonPainter({
    required this.landmarks,
    required this.imageWidth,
    required this.imageHeight,
    required this.calibrationMode,
  });

  /// Normalised MediaPipe landmarks [x, y] ∈ [0,1].
  /// Map: landmark_name → [x_norm, y_norm, visibility].
  final Map<String, List<double>> landmarks;

  final int imageWidth;
  final int imageHeight;

  /// True = T-pose calibration mode (guides shown).
  /// False = kick recording mode (minimal overlay).
  final bool calibrationMode;

  // ── Landmark name indices (MediaPipe Pose) ────────────────────────────
  static const _connections = [
    // Kicking leg (left by convention)
    ['LEFT_HIP',      'LEFT_KNEE'],
    ['LEFT_KNEE',     'LEFT_ANKLE'],
    ['LEFT_SHOULDER', 'LEFT_HIP'],
    // Support leg (right)
    ['RIGHT_HIP',     'RIGHT_KNEE'],
    ['RIGHT_KNEE',    'RIGHT_ANKLE'],
    ['RIGHT_SHOULDER','RIGHT_HIP'],
    // Cross-body
    ['LEFT_SHOULDER', 'RIGHT_SHOULDER'],
    ['LEFT_HIP',      'RIGHT_HIP'],
  ];

  // ── Joint circle radius ───────────────────────────────────────────────
  static const double _jointRadius = 6.0;
  static const double _segmentWidth = 3.0;

  // ── Colours ───────────────────────────────────────────────────────────
  static const Color _kickingLegColor  = Color(0xFF64B5F6);  // blue
  static const Color _supportLegColor  = Color(0xFF81C784);  // green
  static const Color _trunkColor       = Color(0xFFFFB74D);  // orange
  static const Color _jointColor       = Colors.white;
  static const Color _lowVisColor      = Color(0x33FFFFFF);  // translucent

  @override
  void paint(Canvas canvas, Size size) {
    if (landmarks.isEmpty) return;

    // ── Draw connections ────────────────────────────────────────────────
    for (final connection in _connections) {
      final nameA = connection[0];
      final nameB = connection[1];

      final lmA = landmarks[nameA];
      final lmB = landmarks[nameB];

      if (lmA == null || lmB == null) continue;

      final visA = lmA.length > 2 ? lmA[2] : 0.0;
      final visB = lmB.length > 2 ? lmB[2] : 0.0;

      // Skip low-confidence connections
      if (visA < 0.5 || visB < 0.5) continue;

      final pointA = _toCanvasPoint(lmA[0], lmA[1], size);
      final pointB = _toCanvasPoint(lmB[0], lmB[1], size);

      final segmentColor = _segmentColor(nameA);
      final paint = Paint()
        ..color = segmentColor.withOpacity(0.85)
        ..strokeWidth = _segmentWidth
        ..strokeCap = StrokeCap.round;

      canvas.drawLine(pointA, pointB, paint);
    }

    // ── Draw joint circles ──────────────────────────────────────────────
    final relevantJoints = [
      'LEFT_SHOULDER', 'LEFT_HIP', 'LEFT_KNEE', 'LEFT_ANKLE',
      'RIGHT_SHOULDER', 'RIGHT_HIP', 'RIGHT_KNEE', 'RIGHT_ANKLE',
    ];

    for (final jointName in relevantJoints) {
      final lm = landmarks[jointName];
      if (lm == null) continue;

      final visibility = lm.length > 2 ? lm[2] : 0.0;
      final point = _toCanvasPoint(lm[0], lm[1], size);

      final jointPaint = Paint()
        ..color = visibility >= 0.75
            ? _jointColor.withOpacity(0.9)
            : _lowVisColor
        ..style = PaintingStyle.fill;

      canvas.drawCircle(point, _jointRadius, jointPaint);

      // Ring for high-confidence joints
      if (visibility >= 0.75) {
        final ringPaint = Paint()
          ..color = _segmentColor(jointName).withOpacity(0.7)
          ..style = PaintingStyle.stroke
          ..strokeWidth = 2.0;
        canvas.drawCircle(point, _jointRadius + 2, ringPaint);
      }
    }

    // ── Calibration mode: draw T-pose guide ─────────────────────────────
    if (calibrationMode) {
      _drawTPoseGuide(canvas, size);
    }
  }

  /// Map normalised [0,1] landmark coordinates to canvas pixels.
  Offset _toCanvasPoint(double xNorm, double yNorm, Size canvasSize) {
    return Offset(
      xNorm * canvasSize.width,
      yNorm * canvasSize.height,
    );
  }

  /// Assign colour based on body segment.
  Color _segmentColor(String landmarkName) {
    if (landmarkName.startsWith('RIGHT')) return _supportLegColor;
    if (landmarkName.contains('SHOULDER')) return _trunkColor;
    return _kickingLegColor;
  }

  /// Draw T-pose reference guide overlay for calibration screen.
  ///
  /// [SPEC §1.7.2]: "Records blocked until player visually aligns
  /// body with the overlay."
  void _drawTPoseGuide(Canvas canvas, Size size) {
    final guidePaint = Paint()
      ..color = Colors.white.withOpacity(0.15)
      ..strokeWidth = 1.5
      ..style = PaintingStyle.stroke;

    final cx = size.width * 0.5;
    final cy = size.height * 0.5;

    // Simplified T-pose silhouette guide
    // Head
    canvas.drawCircle(
      Offset(cx, cy - size.height * 0.28),
      size.width * 0.06,
      guidePaint,
    );

    // Spine
    canvas.drawLine(
      Offset(cx, cy - size.height * 0.22),
      Offset(cx, cy + size.height * 0.08),
      guidePaint,
    );

    // Arms (horizontal — T-pose)
    canvas.drawLine(
      Offset(cx - size.width * 0.35, cy - size.height * 0.12),
      Offset(cx + size.width * 0.35, cy - size.height * 0.12),
      guidePaint,
    );

    // Left leg
    canvas.drawLine(
      Offset(cx - size.width * 0.07, cy + size.height * 0.08),
      Offset(cx - size.width * 0.07, cy + size.height * 0.38),
      guidePaint,
    );

    // Right leg
    canvas.drawLine(
      Offset(cx + size.width * 0.07, cy + size.height * 0.08),
      Offset(cx + size.width * 0.07, cy + size.height * 0.38),
      guidePaint,
    );
  }

  @override
  bool shouldRepaint(SkeletonPainter oldDelegate) =>
      oldDelegate.landmarks != landmarks ||
      oldDelegate.calibrationMode != calibrationMode;
}