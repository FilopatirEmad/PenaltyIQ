import 'package:flutter/material.dart';
import 'dart:math' as math;

/// Goal zone heatmap — visualises predicted ball position at goal line.
///
/// Renders an accurate goal frame (7.32m × 2.44m proportional) with:
///   - Zone grid overlay.
///   - Target zone highlight.
///   - Predicted ball impact marker.
///   - Error distance indicator.
///
/// Coordinate mapping:
///   z_m (lateral) ∈ [−3.66, +3.66] → canvas x
///   y_m (vertical) ∈ [0, 2.44] → canvas y (inverted: y=0 at bottom)
///
/// [FIFA-2024]: Goal width = 7.32m, height = 2.44m.
class ZoneHeatmap extends StatelessWidget {
  const ZoneHeatmap({
    super.key,
    required this.targetZone,
    required this.hitZone,
    required this.predictedX,   // lateral (z) position [m]
    required this.predictedY,   // vertical position [m]
  });

  final String targetZone;
  final String hitZone;
  final double predictedX;
  final double predictedY;

  @override
  Widget build(BuildContext context) {
    return Container(
      height: 200,
      margin: const EdgeInsets.symmetric(vertical: 8),
      decoration: BoxDecoration(
        color: const Color(0xFF0D1117),
        borderRadius: BorderRadius.circular(12),
        border: Border.all(color: Colors.white.withOpacity(0.1)),
      ),
      child: Padding(
        padding: const EdgeInsets.all(12),
        child: CustomPaint(
          painter: _GoalHeatmapPainter(
            targetZone: targetZone,
            hitZone: hitZone,
            predictedX: predictedX,
            predictedY: predictedY,
          ),
          size: Size.infinite,
        ),
      ),
    );
  }
}

class _GoalHeatmapPainter extends CustomPainter {
  const _GoalHeatmapPainter({
    required this.targetZone,
    required this.hitZone,
    required this.predictedX,
    required this.predictedY,
  });

  final String targetZone;
  final String hitZone;
  final double predictedX;   // lateral [m]
  final double predictedY;   // vertical [m]

  // FIFA dimensions [FIFA-2024]
  static const double _goalW = 7.32;  // m
  static const double _goalH = 2.44;  // m

  // Zone geometry [SPEC §2.3]
  static const double _zoneW = _goalW / 4;   // 1.83m
  static const double _zoneH = _goalH / 2;   // 1.22m

  @override
  void paint(Canvas canvas, Size size) {
    final scaleX = size.width  / _goalW;
    final scaleY = size.height / _goalH;

    // Helper: convert (z_m, y_m) → canvas (x, y)
    // z=0 is goal centre, positive z = right
    // y=0 is ground, positive y = up
    // Canvas: x=0 left, y=0 top
    Offset toCanvas(double zm, double ym) {
      final cx = (zm + _goalW / 2) * scaleX;
      final cy = size.height - ym * scaleY;
      return Offset(cx, cy);
    }

    // ── Draw zone cells ───────────────────────────────────────────────────
    const zones = {
      'T1': (-3.36, 2.20), 'T2': (-1.22, 2.20),
      'T3': ( 1.22, 2.20), 'T4': ( 3.36, 2.20),
      'B1': (-3.36, 0.30), 'B2': (-1.22, 0.30),
      'B3': ( 1.22, 0.30), 'B4': ( 3.36, 0.30),
    };

    for (final entry in zones.entries) {
      final zoneId = entry.key;
      final (zc, yc) = entry.value;

      final topLeft     = toCanvas(zc - _zoneW/2, yc + _zoneH/2);
      final bottomRight = toCanvas(zc + _zoneW/2, yc - _zoneH/2);

      final rect = Rect.fromPoints(topLeft, bottomRight);

      // Fill
      final isTarget = zoneId == targetZone;
      final isHit    = zoneId == hitZone;

      Color fillColor;
      if (isTarget && isHit) {
        fillColor = const Color(0xFF4CAF50).withOpacity(0.25);
      } else if (isTarget) {
        fillColor = const Color(0xFF64B5F6).withOpacity(0.15);
      } else {
        fillColor = Colors.white.withOpacity(0.03);
      }

      canvas.drawRect(rect, Paint()..color = fillColor);

      // Border
      final borderColor = isTarget
          ? const Color(0xFF64B5F6).withOpacity(0.7)
          : Colors.white.withOpacity(0.15);
      canvas.drawRect(
        rect,
        Paint()
          ..color = borderColor
          ..style = PaintingStyle.stroke
          ..strokeWidth = isTarget ? 1.5 : 0.75,
      );

      // Zone label
      final textPainter = TextPainter(
        text: TextSpan(
          text: zoneId,
          style: TextStyle(
            color: isTarget
                ? const Color(0xFF64B5F6)
                : Colors.white.withOpacity(0.25),
            fontSize: 9,
            fontWeight: isTarget ? FontWeight.bold : FontWeight.normal,
          ),
        ),
        textDirection: TextDirection.ltr,
      )..layout();
      textPainter.paint(
        canvas,
        rect.center - Offset(textPainter.width / 2, textPainter.height / 2),
      );
    }

    // ── Goal frame (posts + crossbar) ─────────────────────────────────────
    final goalPaint = Paint()
      ..color = Colors.white.withOpacity(0.85)
      ..strokeWidth = 3.0
      ..style = PaintingStyle.stroke
      ..strokeCap = StrokeCap.square;

    // Crossbar
    canvas.drawLine(
      toCanvas(-_goalW / 2, _goalH),
      toCanvas( _goalW / 2, _goalH),
      goalPaint,
    );
    // Left post
    canvas.drawLine(
      toCanvas(-_goalW / 2, 0),
      toCanvas(-_goalW / 2, _goalH),
      goalPaint,
    );
    // Right post
    canvas.drawLine(
      toCanvas( _goalW / 2, 0),
      toCanvas( _goalW / 2, _goalH),
      goalPaint,
    );
    // Ground line
    canvas.drawLine(
      toCanvas(-_goalW / 2, 0),
      toCanvas( _goalW / 2, 0),
      Paint()
        ..color = Colors.white.withOpacity(0.3)
        ..strokeWidth = 1.5,
    );

    // ── Predicted impact marker ───────────────────────────────────────────
    final impactPoint = toCanvas(predictedX, predictedY);
    final impactInGoal = predictedY >= 0 &&
        predictedY <= _goalH &&
        predictedX.abs() <= _goalW / 2;

    if (impactInGoal) {
      // Outer glow ring
      canvas.drawCircle(
        impactPoint,
        14,
        Paint()
          ..color = const Color(0xFFFFEB3B).withOpacity(0.2)
          ..style = PaintingStyle.fill,
      );
      // Impact marker
      canvas.drawCircle(
        impactPoint,
        8,
        Paint()
          ..color = const Color(0xFFFFEB3B).withOpacity(0.9)
          ..style = PaintingStyle.fill,
      );
      // Crosshair
      final crossPaint = Paint()
        ..color = Colors.black.withOpacity(0.7)
        ..strokeWidth = 1.5;
      canvas.drawLine(
        impactPoint - const Offset(5, 0),
        impactPoint + const Offset(5, 0),
        crossPaint,
      );
      canvas.drawLine(
        impactPoint - const Offset(0, 5),
        impactPoint + const Offset(0, 5),
        crossPaint,
      );
    }
  }

  @override
  bool shouldRepaint(_GoalHeatmapPainter oldDelegate) =>
      oldDelegate.predictedX != predictedX ||
      oldDelegate.predictedY != predictedY ||
      oldDelegate.targetZone != targetZone ||
      oldDelegate.hitZone    != hitZone;
}