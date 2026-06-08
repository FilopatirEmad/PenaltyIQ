import 'dart:math' as math;
import 'package:flutter/material.dart';
import '../../data/models/analysis_response.dart';

// ─────────────────────────────────────────────────────────────────────────────
// ELITE CUE TRANSFORMER — logic unchanged, same switch cases
// ─────────────────────────────────────────────────────────────────────────────
String _transformCue(CoachingFeedbackItem item) {
  final isPositiveDelta = item.deltaDeg > 0;
  switch (item.variable) {
    case 'hip_flexion':
      return isPositiveDelta
          ? "Increase backswing depth to generate maximal foot velocity."
          : "Reduce backswing over-extension for a tighter, faster kinetic chain.";
    case 'knee_flexion':
      return isPositiveDelta
          ? "Relax knee during wind-up to prevent stiffening and speed loss."
          : "Increase knee bend to maximize elastic energy storage in the quadriceps.";
    case 'support_knee':
      return isPositiveDelta
          ? "Lower your center of mass by bending the plant leg for elite stability."
          : "Extend plant leg slightly to maintain a powerful, uncompressed base.";
    case 'trunk_inclination':
      return isPositiveDelta
          ? "Lean forward at contact to drive the ball trajectory down."
          : "Keep chest upright to ensure maximum elevation on top-corner strikes.";
    default:
      final sentences = item.cue.split('.');
      return sentences.isNotEmpty ? '${sentences[0]}.' : item.cue;
  }
}

// ─────────────────────────────────────────────────────────────────────────────
// DESIGN TOKENS
// ─────────────────────────────────────────────────────────────────────────────
class _T {
  static const bg       = Color(0xFF080810);
  static const surface  = Color(0xFF0F0F1A);
  static const card     = Color(0xFF13131F);
  static const cardHigh = Color(0xFF181828);
  static const border   = Color(0x14FFFFFF);
  static const border2  = Color(0x22FFFFFF);
  static const text     = Color(0xFFF2F2FA);
  static const muted    = Color(0xFF6B6B8A);
  static const subtle   = Color(0xFF2E2E45);

  static const green    = Color(0xFF00E5A0);
  static const greenDim = Color(0x1500E5A0);
  static const greenGlow= Color(0x4000E5A0);

  static const blue     = Color(0xFF3D9BFF);
  static const blueDim  = Color(0x153D9BFF);

  static const orange   = Color(0xFFFF8C3A);
  static const orangeDim= Color(0x15FF8C3A);

  static const red      = Color(0xFFFF3D60);
  static const redDim   = Color(0x15FF3D60);
  static const redGlow  = Color(0x40FF3D60);
}

// ─────────────────────────────────────────────────────────────────────────────
// STATUS CONFIG — same map keys as original
// ─────────────────────────────────────────────────────────────────────────────
class _StatusConfig {
  final Color accent;
  final Color dim;
  final Color glow;
  final String label;
  final IconData icon;
  const _StatusConfig({
    required this.accent,
    required this.dim,
    required this.glow,
    required this.label,
    required this.icon,
  });
}

const Map<String, _StatusConfig> _statusMap = {
  'OPTIMAL': _StatusConfig(
    accent: _T.green, dim: _T.greenDim, glow: _T.greenGlow,
    label: 'ELITE', icon: Icons.verified_rounded,
  ),
  'ACCEPTABLE': _StatusConfig(
    accent: _T.blue, dim: _T.blueDim, glow: Color(0x403D9BFF),
    label: 'GOOD', icon: Icons.check_circle_outline_rounded,
  ),
  'NEEDS_WORK': _StatusConfig(
    accent: _T.orange, dim: _T.orangeDim, glow: Color(0x40FF8C3A),
    label: 'IMPROVE', icon: Icons.trending_up_rounded,
  ),
  'CRITICAL': _StatusConfig(
    accent: _T.red, dim: _T.redDim, glow: _T.redGlow,
    label: 'CRITICAL', icon: Icons.bolt_rounded,
  ),
};

_StatusConfig _cfg(String status) =>
    _statusMap[status] ??
    const _StatusConfig(
      accent: _T.muted, dim: Color(0x156B6B8A), glow: Color(0x406B6B8A),
      label: 'UNKNOWN', icon: Icons.help_outline,
    );

// ─────────────────────────────────────────────────────────────────────────────
// MAIN CARD WIDGET
// ─────────────────────────────────────────────────────────────────────────────
class CoachingCard extends StatefulWidget {
  const CoachingCard({super.key, required this.item, this.index = 0});
  final CoachingFeedbackItem item;
  final int index;

  @override
  State<CoachingCard> createState() => _CoachingCardState();
}

class _CoachingCardState extends State<CoachingCard>
    with SingleTickerProviderStateMixin {
  late final AnimationController _ctrl;
  late final Animation<double> _fade;
  late final Animation<Offset> _slide;
  bool _hovered = false;

  @override
  void initState() {
    super.initState();
    _ctrl = AnimationController(
      vsync: this,
      duration: const Duration(milliseconds: 700),
    );
    _fade  = CurvedAnimation(parent: _ctrl, curve: Curves.easeOut);
    _slide = Tween<Offset>(
      begin: const Offset(0, 0.08),
      end: Offset.zero,
    ).animate(CurvedAnimation(parent: _ctrl, curve: Curves.easeOutCubic));

    Future.delayed(Duration(milliseconds: 120 * widget.index), () {
      if (mounted) _ctrl.forward();
    });
  }

  @override
  void dispose() {
    _ctrl.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final cfg   = _cfg(widget.item.status);
    final label = widget.item.label.isNotEmpty
        ? widget.item.label
        : widget.item.variable
            .split('_')
            .map((w) => w.isEmpty ? '' : w[0].toUpperCase() + w.substring(1))
            .join(' ');

    return FadeTransition(
      opacity: _fade,
      child: SlideTransition(
        position: _slide,
        child: MouseRegion(
          onEnter: (_) => setState(() => _hovered = true),
          onExit:  (_) => setState(() => _hovered = false),
          child: AnimatedContainer(
            duration: const Duration(milliseconds: 280),
            curve: Curves.easeOutCubic,
            margin: const EdgeInsets.only(bottom: 14),
            transform: Matrix4.identity()
              ..translate(0.0, _hovered ? -3.0 : 0.0),
            decoration: BoxDecoration(
              color: _hovered ? _T.cardHigh : _T.card,
              borderRadius: BorderRadius.circular(20),
              border: Border.all(
                color: _hovered
                    ? cfg.accent.withOpacity(0.22)
                    : _T.border,
                width: 1,
              ),
              boxShadow: _hovered
                  ? [
                      BoxShadow(
                        color: cfg.glow.withOpacity(0.18),
                        blurRadius: 28,
                        offset: const Offset(0, 6),
                      ),
                      BoxShadow(
                        color: Colors.black.withOpacity(0.5),
                        blurRadius: 16,
                        offset: const Offset(0, 4),
                      ),
                    ]
                  : [
                      BoxShadow(
                        color: Colors.black.withOpacity(0.35),
                        blurRadius: 12,
                        offset: const Offset(0, 3),
                      ),
                    ],
            ),
            child: ClipRRect(
              borderRadius: BorderRadius.circular(20),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  // ── accent top strip ──────────────────────────────────
                  _AccentStrip(color: cfg.accent),

                  // ── header ────────────────────────────────────────────
                  _CardHeader(label: label, item: widget.item, cfg: cfg),

                  // ── metrics row ───────────────────────────────────────
                  _MetricsRow(item: widget.item, cfg: cfg),

                  // ── visualizer + cue ─────────────────────────────────
                  Padding(
                    padding: const EdgeInsets.fromLTRB(18, 16, 18, 18),
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        _RangeVisualizer(item: widget.item, cfg: cfg),
                        const SizedBox(height: 14),
                        _CueBox(item: widget.item, cfg: cfg),
                      ],
                    ),
                  ),
                ],
              ),
            ),
          ),
        ),
      ),
    );
  }
}

// ─────────────────────────────────────────────────────────────────────────────
// ACCENT STRIP
// ─────────────────────────────────────────────────────────────────────────────
class _AccentStrip extends StatelessWidget {
  const _AccentStrip({required this.color});
  final Color color;

  @override
  Widget build(BuildContext context) {
    return Container(
      height: 3,
      decoration: BoxDecoration(
        gradient: LinearGradient(
          colors: [color.withOpacity(0.0), color, color.withOpacity(0.4)],
          stops: const [0.0, 0.45, 1.0],
        ),
      ),
    );
  }
}

// ─────────────────────────────────────────────────────────────────────────────
// CARD HEADER
// ─────────────────────────────────────────────────────────────────────────────
class _CardHeader extends StatelessWidget {
  const _CardHeader({
    required this.label,
    required this.item,
    required this.cfg,
  });
  final String label;
  final CoachingFeedbackItem item;
  final _StatusConfig cfg;

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.fromLTRB(18, 16, 18, 0),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  label.toUpperCase(),
                  style: const TextStyle(
                    color: _T.text,
                    fontSize: 15,
                    fontWeight: FontWeight.w800,
                    letterSpacing: 0.6,
                    fontFamily: 'SF Pro Display',
                  ),
                ),
                if (item.source.isNotEmpty) ...[
                  const SizedBox(height: 3),
                  Text(
                    item.source.split(',')[0].toUpperCase(),
                    style: const TextStyle(
                      color: _T.muted,
                      fontSize: 9,
                      fontWeight: FontWeight.w700,
                      letterSpacing: 1.8,
                    ),
                  ),
                ],
              ],
            ),
          ),
          const SizedBox(width: 12),
          _StatusBadge(cfg: cfg),
        ],
      ),
    );
  }
}

class _StatusBadge extends StatelessWidget {
  const _StatusBadge({required this.cfg});
  final _StatusConfig cfg;

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 5),
      decoration: BoxDecoration(
        color: cfg.dim,
        borderRadius: BorderRadius.circular(8),
        border: Border.all(color: cfg.accent.withOpacity(0.28), width: 1),
      ),
      child: Row(
        mainAxisSize: MainAxisSize.min,
        children: [
          Icon(cfg.icon, color: cfg.accent, size: 12),
          const SizedBox(width: 5),
          Text(
            cfg.label,
            style: TextStyle(
              color: cfg.accent,
              fontSize: 9,
              fontWeight: FontWeight.w900,
              letterSpacing: 1.6,
            ),
          ),
        ],
      ),
    );
  }
}

// ─────────────────────────────────────────────────────────────────────────────
// METRICS ROW  (Measured / Target / Delta)
// ─────────────────────────────────────────────────────────────────────────────
class _MetricsRow extends StatelessWidget {
  const _MetricsRow({required this.item, required this.cfg});
  final CoachingFeedbackItem item;
  final _StatusConfig cfg;

  @override
  Widget build(BuildContext context) {
    final sign = item.deltaDeg > 0 ? '+' : '';
    return Padding(
      padding: const EdgeInsets.fromLTRB(18, 18, 18, 0),
      child: IntrinsicHeight(
        child: Row(
          children: [
            _MetricCell(
              metricKey: 'MEASURED',
              value: '${item.measuredDeg.toStringAsFixed(1)}°',
              color: cfg.accent,
            ),
            _VertDivider(),
            _MetricCell(
              metricKey: 'TARGET',
              value: '${item.targetDeg.toStringAsFixed(1)}°',
              color: _T.text,
            ),
            _VertDivider(),
            _MetricCell(
              metricKey: 'DELTA',
              value: '$sign${item.deltaDeg.toStringAsFixed(1)}°',
              color: cfg.accent,
            ),
          ],
        ),
      ),
    );
  }
}

class _VertDivider extends StatelessWidget {
  @override
  Widget build(BuildContext context) =>
      Container(width: 1, color: _T.border, margin: const EdgeInsets.symmetric(horizontal: 16));
}

class _MetricCell extends StatelessWidget {
  const _MetricCell({
    required this.metricKey,
    required this.value,
    required this.color,
  });
  final String metricKey;
  final String value;
  final Color color;

  @override
  Widget build(BuildContext context) {
    return Expanded(
      child: Column(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          Text(
            metricKey,
            style: const TextStyle(
              color: _T.muted,
              fontSize: 8,
              fontWeight: FontWeight.w800,
              letterSpacing: 1.8,
            ),
          ),
          const SizedBox(height: 5),
          Text(
            value,
            style: TextStyle(
              color: color,
              fontSize: 22,
              fontWeight: FontWeight.w900,
              letterSpacing: -0.5,
              fontFeatures: const [FontFeature.tabularFigures()],
            ),
          ),
        ],
      ),
    );
  }
}

// ─────────────────────────────────────────────────────────────────────────────
// RANGE VISUALIZER — same logic as original, new visuals
// ─────────────────────────────────────────────────────────────────────────────
class _RangeVisualizer extends StatelessWidget {
  const _RangeVisualizer({required this.item, required this.cfg});
  final CoachingFeedbackItem item;
  final _StatusConfig cfg;

  @override
  Widget build(BuildContext context) {
    final rangeSpread = (item.targetRangeMaxDeg - item.targetRangeMinDeg) > 0
        ? (item.targetRangeMaxDeg - item.targetRangeMinDeg)
        : 10.0;
    final displayMin  = item.targetRangeMinDeg - (rangeSpread * 0.5);
    final displayMax  = item.targetRangeMaxDeg + (rangeSpread * 0.5);
    final totalWidth  = displayMax - displayMin;

    final targetPos   = ((item.targetDeg - displayMin) / totalWidth).clamp(0.0, 1.0);
    final measuredPos = ((item.measuredDeg - displayMin) / totalWidth).clamp(0.0, 1.0);
    final safeStart   = ((item.targetRangeMinDeg - displayMin) / totalWidth).clamp(0.0, 1.0);
    final safeWidth   = (rangeSpread / totalWidth).clamp(0.0, 1.0);

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        // range track label
        Row(
          children: [
            const Text(
              'RANGE ANALYSIS',
              style: TextStyle(
                color: _T.muted,
                fontSize: 8,
                fontWeight: FontWeight.w800,
                letterSpacing: 2.0,
              ),
            ),
            const Spacer(),
            Text(
              '${item.targetRangeMinDeg.toStringAsFixed(0)}° – ${item.targetRangeMaxDeg.toStringAsFixed(0)}°',
              style: const TextStyle(
                color: _T.muted,
                fontSize: 9,
                fontWeight: FontWeight.w700,
              ),
            ),
          ],
        ),
        const SizedBox(height: 10),
        LayoutBuilder(
          builder: (context, constraints) {
            final w = constraints.maxWidth;
            return SizedBox(
              height: 28,
              child: Stack(
                clipBehavior: Clip.none,
                alignment: Alignment.centerLeft,
                children: [
                  // background track
                  Positioned(
                    top: 9,
                    left: 0,
                    right: 0,
                    child: Container(
                      height: 6,
                      decoration: BoxDecoration(
                        color: Colors.white.withOpacity(0.04),
                        borderRadius: BorderRadius.circular(3),
                      ),
                    ),
                  ),
                  // safe zone
                  Positioned(
                    top: 9,
                    left: safeStart * w,
                    width: safeWidth * w,
                    child: Container(
                      height: 6,
                      decoration: BoxDecoration(
                        color: cfg.accent.withOpacity(0.18),
                        borderRadius: BorderRadius.circular(3),
                      ),
                    ),
                  ),
                  // target line + glow
                  Positioned(
                    top: 4,
                    left: targetPos * w - 1,
                    child: Container(
                      width: 2,
                      height: 16,
                      decoration: BoxDecoration(
                        color: Colors.white.withOpacity(0.55),
                        borderRadius: BorderRadius.circular(1),
                        boxShadow: [
                          BoxShadow(
                            color: Colors.white.withOpacity(0.25),
                            blurRadius: 4,
                          ),
                        ],
                      ),
                    ),
                  ),
                  // measured dot + glow
                  Positioned(
                    top: 4,
                    left: measuredPos * w - 9,
                    child: Container(
                      width: 18,
                      height: 18,
                      decoration: BoxDecoration(
                        color: cfg.accent,
                        shape: BoxShape.circle,
                        border: Border.all(color: _T.card, width: 2.5),
                        boxShadow: [
                          BoxShadow(
                            color: cfg.glow,
                            blurRadius: 10,
                            spreadRadius: 1,
                          ),
                        ],
                      ),
                    ),
                  ),
                ],
              ),
            );
          },
        ),
      ],
    );
  }
}

// ─────────────────────────────────────────────────────────────────────────────
// CUE BOX
// ─────────────────────────────────────────────────────────────────────────────
class _CueBox extends StatelessWidget {
  const _CueBox({required this.item, required this.cfg});
  final CoachingFeedbackItem item;
  final _StatusConfig cfg;

  @override
  Widget build(BuildContext context) {
    return Container(
      width: double.infinity,
      padding: const EdgeInsets.fromLTRB(14, 12, 14, 12),
      decoration: BoxDecoration(
        color: cfg.dim,
        borderRadius: BorderRadius.circular(10),
        border: Border(
          left: BorderSide(color: cfg.accent, width: 2.5),
        ),
      ),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Padding(
            padding: const EdgeInsets.only(top: 1),
            child: Icon(Icons.format_quote_rounded, color: cfg.accent.withOpacity(0.5), size: 14),
          ),
          const SizedBox(width: 8),
          Expanded(
            child: Text(
              _transformCue(item),
              style: const TextStyle(
                color: Color(0xFFB8B8D0),
                fontSize: 12.5,
                height: 1.6,
                fontWeight: FontWeight.w500,
                letterSpacing: 0.1,
              ),
            ),
          ),
        ],
      ),
    );
  }
}