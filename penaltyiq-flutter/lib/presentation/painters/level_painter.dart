import 'dart:math' as math;
import 'package:flutter/material.dart';

/// Custom painter for the Digital Level Tool (bubble level).
///
/// [SPEC §1.7.1]: Visual representation of phone tilt.
/// Shows a bubble that moves with tilt angle.
/// Green zone: |tilt| ≤ 2° → recording permitted.
/// Red zone: |tilt| > 2° → recording blocked.
///
/// Visual design:
///   - Circular level vial with crosshair at centre.
///   - Bubble position proportional to [rollDeg, pitchDeg].
///   - Green fill when both roll and pitch ≤ ±2°.
///   - Red fill when outside tolerance.
///   - Degree readouts displayed as text.

class LevelPainter extends CustomPainter {
  const LevelPainter({
    required this.rollDeg,
    required this.pitchDeg,
    required this.isLevel,
  });

  final double rollDeg;
  final double pitchDeg;
  final bool isLevel;

  // ── Visual constants ──────────────────────────────────────────────────────
  /// Maximum tilt displayed before bubble hits edge [degrees].
  static const double _maxDisplayDeg = 10.0;

  /// Tolerance zone radius as fraction of vial radius.
  /// 2° / 10° = 0.2 of total radius.
  static const double _toleranceFraction = 0.2;

  @override
  void paint(Canvas canvas, Size size) {
    final centre = Offset(size.width / 2, size.height / 2);
    final vialRadius = size.width * 0.45;
    final bubbleRadius = vialRadius * 0.18;

    // ── Vial background ───────────────────────────────────────────────────
    final vialPaint = Paint()
      ..color = Colors.black.withOpacity(0.15)
      ..style = PaintingStyle.fill;
    canvas.drawCircle(centre, vialRadius, vialPaint);

    // ── Tolerance zone (green circle = ±2°) ───────────────────────────────
    final toleranceRadius = vialRadius * _toleranceFraction;
    final tolerancePaint = Paint()
      ..color = isLevel
          ? const Color(0xFF4CAF50).withOpacity(0.35)
          : const Color(0xFFF44336).withOpacity(0.20)
      ..style = PaintingStyle.fill;
    canvas.drawCircle(centre, toleranceRadius, tolerancePaint);

    // Tolerance ring border
    final toleranceBorderPaint = Paint()
      ..color = isLevel ? const Color(0xFF4CAF50) : const Color(0xFFF44336)
      ..style = PaintingStyle.stroke
      ..strokeWidth = 2.0;
    canvas.drawCircle(centre, toleranceRadius, toleranceBorderPaint);

    // ── Crosshair ─────────────────────────────────────────────────────────
    final crosshairPaint = Paint()
      ..color = Colors.white.withOpacity(0.6)
      ..strokeWidth = 1.0;
    canvas.drawLine(
      Offset(centre.dx - vialRadius * 0.8, centre.dy),
      Offset(centre.dx + vialRadius * 0.8, centre.dy),
      crosshairPaint,
    );
    canvas.drawLine(
      Offset(centre.dx, centre.dy - vialRadius * 0.8),
      Offset(centre.dx, centre.dy + vialRadius * 0.8),
      crosshairPaint,
    );

    // ── Bubble position computation ────────────────────────────────────────
    // Map tilt angle → bubble offset within vial.
    // Clamp to _maxDisplayDeg so bubble stays within vial boundary.
    final clampedRoll  = rollDeg.clamp(-_maxDisplayDeg, _maxDisplayDeg);
    final clampedPitch = pitchDeg.clamp(-_maxDisplayDeg, _maxDisplayDeg);

    // Linear mapping: _maxDisplayDeg → vialRadius − bubbleRadius
    final maxBubbleOffset = vialRadius - bubbleRadius - 4.0;
    final bubbleOffsetX = (clampedRoll  / _maxDisplayDeg) * maxBubbleOffset;
    final bubbleOffsetY = (clampedPitch / _maxDisplayDeg) * maxBubbleOffset;

    // Constrain bubble to circle boundary
    final rawOffset = Offset(bubbleOffsetX, bubbleOffsetY);
    final Offset constrainedOffset;
    if (rawOffset.distance > maxBubbleOffset) {
      constrainedOffset = rawOffset / rawOffset.distance * maxBubbleOffset;
    } else {
      constrainedOffset = rawOffset;
    }

    final bubbleCentre = centre + constrainedOffset;

    // ── Bubble ────────────────────────────────────────────────────────────
    // Gradient fill for 3D appearance
    final bubblePaint = Paint()
      ..shader = RadialGradient(
        colors: isLevel
            ? [
                const Color(0xFF81C784),
                const Color(0xFF4CAF50),
              ]
            : [
                const Color(0xFFEF9A9A),
                const Color(0xFFF44336),
              ],
        center: const Alignment(-0.3, -0.3),
      ).createShader(Rect.fromCircle(
        center: bubbleCentre,
        radius: bubbleRadius,
      ));
    canvas.drawCircle(bubbleCentre, bubbleRadius, bubblePaint);

    // Bubble highlight
    final highlightPaint = Paint()
      ..color = Colors.white.withOpacity(0.4)
      ..style = PaintingStyle.fill;
    canvas.drawCircle(
      bubbleCentre + Offset(-bubbleRadius * 0.25, -bubbleRadius * 0.25),
      bubbleRadius * 0.35,
      highlightPaint,
    );

    // ── Vial border ───────────────────────────────────────────────────────
    final vialBorderPaint = Paint()
      ..color = Colors.white.withOpacity(0.5)
      ..style = PaintingStyle.stroke
      ..strokeWidth = 2.0;
    canvas.drawCircle(centre, vialRadius, vialBorderPaint);
  }

  @override
  bool shouldRepaint(LevelPainter oldDelegate) =>
      oldDelegate.rollDeg != rollDeg ||
      oldDelegate.pitchDeg != pitchDeg ||
      oldDelegate.isLevel != isLevel;
}