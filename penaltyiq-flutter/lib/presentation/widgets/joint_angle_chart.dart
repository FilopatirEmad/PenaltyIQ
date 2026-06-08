import 'package:fl_chart/fl_chart.dart';
import 'package:flutter/material.dart';

/// Joint angle time-series chart widget.
///
/// Displays the filtered landmark angle trajectory over time.
/// Target range shown as a shaded band (Arguz 2021 reference).
/// Measured trajectory shown as a line.
///
/// [SPEC §4.2]: Tracked kinematic variables:
///   - Support-leg knee angle (SLK)
///   - Trunk inclination
///   - Hip flexion (backswing)
///   - Kicking-leg knee angle (backswing)
///   - Ankle plantarflexion
///
/// [WINTER-2009 Ch.3]: Signal has been Butterworth-filtered at 6Hz
/// before being passed to this widget.
class JointAngleChart extends StatelessWidget {
  const JointAngleChart({
    super.key,
    required this.label,
    required this.anglesDeg,
    required this.targetDeg,
    required this.targetRangeMinDeg,
    required this.targetRangeMaxDeg,
    required this.fps,
  });

  /// Human-readable variable name (e.g., "Hip Flexion").
  final String label;

  /// Time-series of filtered angle values [degrees].
  /// Index corresponds to frame number.
  final List<double> anglesDeg;

  /// Player-specific IK target [degrees].
  final double targetDeg;

  /// Lower bound of Arguz (2021) reference range [degrees].
  final double targetRangeMinDeg;

  /// Upper bound of Arguz (2021) reference range [degrees].
  final double targetRangeMaxDeg;

  /// Video frame rate [fps]. Used for x-axis time labels.
  final double fps;

  @override
  Widget build(BuildContext context) {
    if (anglesDeg.isEmpty) {
      return const SizedBox(
        height: 180,
        child: Center(
          child: Text(
            'No angle data available',
            style: TextStyle(color: Colors.white54),
          ),
        ),
      );
    }

    // Build line data points
    final spots = anglesDeg.asMap().entries.map((e) {
      final timeSec = e.key / fps;
      return FlSpot(timeSec, e.value);
    }).toList();

    // Compute y-axis range with padding
    final minY = ([...anglesDeg, targetRangeMinDeg].reduce(
      (a, b) => a < b ? a : b,
    ) - 10).clamp(0.0, double.infinity);
    final maxY = [...anglesDeg, targetRangeMaxDeg].reduce(
      (a, b) => a > b ? a : b,
    ) + 10;

    final maxTimeSec = (anglesDeg.length - 1) / fps;

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        // Chart title
        Padding(
          padding: const EdgeInsets.only(left: 8, bottom: 8),
          child: Text(
            label,
            style: const TextStyle(
              color: Colors.white,
              fontSize: 13,
              fontWeight: FontWeight.w600,
            ),
          ),
        ),

        SizedBox(
          height: 180,
          child: LineChart(
            LineChartData(
              // ── Grid ───────────────────────────────────────────────────
              gridData: FlGridData(
                show: true,
                horizontalInterval: 15,
                verticalInterval: 0.1,
                getDrawingHorizontalLine: (_) => FlLine(
                  color: Colors.white.withOpacity(0.08),
                  strokeWidth: 1,
                ),
                getDrawingVerticalLine: (_) => FlLine(
                  color: Colors.white.withOpacity(0.05),
                  strokeWidth: 1,
                ),
              ),

              // ── Axes ───────────────────────────────────────────────────
              titlesData: FlTitlesData(
                leftTitles: AxisTitles(
                  sideTitles: SideTitles(
                    showTitles: true,
                    interval: 15,
                    reservedSize: 36,
                    getTitlesWidget: (value, _) => Text(
                      '${value.toInt()}°',
                      style: const TextStyle(
                        color: Colors.white38,
                        fontSize: 10,
                      ),
                    ),
                  ),
                ),
                bottomTitles: AxisTitles(
                  sideTitles: SideTitles(
                    showTitles: true,
                    interval: 0.1,
                    reservedSize: 22,
                    getTitlesWidget: (value, _) => Text(
                      '${value.toStringAsFixed(1)}s',
                      style: const TextStyle(
                        color: Colors.white38,
                        fontSize: 9,
                      ),
                    ),
                  ),
                ),
                rightTitles: const AxisTitles(
                  sideTitles: SideTitles(showTitles: false),
                ),
                topTitles: const AxisTitles(
                  sideTitles: SideTitles(showTitles: false),
                ),
              ),

              // ── Borders ────────────────────────────────────────────────
              borderData: FlBorderData(
                show: true,
                border: Border.all(color: Colors.white.withOpacity(0.15)),
              ),

              // ── Axis bounds ────────────────────────────────────────────
              minX: 0,
              maxX: maxTimeSec,
              minY: minY,
              maxY: maxY,

              // ── Reference band (Arguz 2021 range) ─────────────────────
              // Shown as a semi-transparent horizontal band
              extraLinesData: ExtraLinesData(
                horizontalLines: [
                  // Target line
                  HorizontalLine(
                    y: targetDeg,
                    color: const Color(0xFF4CAF50),
                    strokeWidth: 1.5,
                    dashArray: [6, 4],
                    label: HorizontalLineLabel(
                      show: true,
                      alignment: Alignment.topRight,
                      labelResolver: (_) => 'Target',
                      style: const TextStyle(
                        color: Color(0xFF4CAF50),
                        fontSize: 9,
                      ),
                    ),
                  ),
                  // Upper range bound
                  HorizontalLine(
                    y: targetRangeMaxDeg,
                    color: Colors.green.withOpacity(0.3),
                    strokeWidth: 1.0,
                    dashArray: [3, 6],
                  ),
                  // Lower range bound
                  HorizontalLine(
                    y: targetRangeMinDeg,
                    color: Colors.green.withOpacity(0.3),
                    strokeWidth: 1.0,
                    dashArray: [3, 6],
                  ),
                ],
              ),

              // ── Measured angle line ────────────────────────────────────
              lineBarsData: [
                LineChartBarData(
                  spots: spots,
                  isCurved: true,
                  curveSmoothness: 0.35,
                  color: const Color(0xFF64B5F6),
                  barWidth: 2.5,
                  isStrokeCapRound: true,
                  dotData: const FlDotData(show: false),
                  belowBarData: BarAreaData(
                    show: true,
                    color: const Color(0xFF64B5F6).withOpacity(0.08),
                  ),
                ),
              ],
            ),
          ),
        ),
      ],
    );
  }
}