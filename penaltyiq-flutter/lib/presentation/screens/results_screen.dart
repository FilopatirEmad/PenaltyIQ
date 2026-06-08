import 'dart:math' as math;
import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../core/theme/app_theme.dart';
import '../../data/models/analysis_response.dart';
import '../../domain/providers/analysis_provider.dart';
import '../widgets/coaching_card.dart';
import '../widgets/joint_angle_chart.dart';
import '../widgets/zone_heatmap.dart';
import '../widgets/piq_app_bar.dart';
import '../widgets/piq_widgets.dart';

// ─────────────────────────────────────────────────────────────────────────────
// DESIGN TOKENS — local to this screen
// ─────────────────────────────────────────────────────────────────────────────
class _K {
  static const bg       = Color(0xFF080810);
  static const surface  = Color(0xFF0F0F1A);
  static const card     = Color(0xFF13131F);
  static const border   = Color(0x12FFFFFF);
  static const border2  = Color(0x20FFFFFF);
  static const text     = Color(0xFFF2F2FA);
  static const muted    = Color(0xFF6B6B8A);
  static const subtle   = Color(0xFF2A2A40);

  static const green    = Color(0xFF00E5A0);
  static const greenDim = Color(0x1200E5A0);
  static const greenGlow= Color(0x3000E5A0);

  static const blue     = Color(0xFF3D9BFF);
  static const red      = Color(0xFFFF3D60);
  static const orange   = Color(0xFFFF8C3A);

  static const levelColors = {
    'Beginner' : Color(0xFF3D9BFF),
    'Good'     : Color(0xFF00C9FF),
    'Pro'      : Color(0xFF00E5A0),
    'Elite'    : Color(0xFFFFD700),
  };

  static Color levelColor(String level) =>
      levelColors[level] ?? const Color(0xFF3D9BFF);
}

// ─────────────────────────────────────────────────────────────────────────────
// ROOT SCREEN
// ─────────────────────────────────────────────────────────────────────────────
class ResultsScreen extends ConsumerWidget {
  const ResultsScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final analysisState = ref.watch(analysisProvider);

    return Scaffold(
      backgroundColor: _K.bg,
      appBar: PiqAppBar(
        title: 'KICK ANALYSIS',
        showBack: false,
        trailing: _TryAgainButton(onTap: () => context.go('/home')),
      ),
      body: analysisState.when(
        initial: () => const _EmptyState(),
        loading: () => const _LoadingState(),
        error:   (msg) => _ErrorState(message: msg),
        success: (response) => _ResultsDashboard(response: response),
      ),
    );
  }
}

// ─────────────────────────────────────────────────────────────────────────────
// MAIN DASHBOARD
// ─────────────────────────────────────────────────────────────────────────────
class _ResultsDashboard extends StatelessWidget {
  const _ResultsDashboard({required this.response});
  final AnalysisResponse response;

  @override
  Widget build(BuildContext context) {
    return CustomScrollView(
      physics: const BouncingScrollPhysics(),
      slivers: [

        // ── SESSION LABEL ──────────────────────────────────────────────
        SliverToBoxAdapter(
          child: Padding(
            padding: const EdgeInsets.fromLTRB(22, 14, 22, 0),
            child: Row(
              children: [
                _PillChip(
                  label: 'SESSION · ZONE ${response.goalZone}',
                  color: _K.muted,
                ),
                const Spacer(),
                _PillChip(
                  label: response.physics.speedRegime.toUpperCase(),
                  color: _K.blue,
                ),
              ],
            ),
          ),
        ),

        // ── HERO ───────────────────────────────────────────────────────
        SliverToBoxAdapter(
          child: Padding(
            padding: const EdgeInsets.fromLTRB(22, 16, 22, 0),
            child: _HeroCard(
              playerScore: response.playerScore ?? const PlayerScore(),
              physics: response.physics,
            ),
          ),
        ),

        // ── KEY INSIGHTS ──────────────────────────────────────────────
        SliverToBoxAdapter(
          child: _KeyInsightsSection(coachingFeedback: response.coachingFeedback),
        ),

        // ── SCORE BREAKDOWN ───────────────────────────────────────────
        if (response.ikResult != null) ...[
          _SectionHeader(title: 'Score Breakdown'),
          SliverToBoxAdapter(
            child: Padding(
              padding: const EdgeInsets.fromLTRB(22, 12, 22, 0),
              child: _ScoreBreakdown(
                ik: response.ikResult!,
                playerScore: response.playerScore,
              ),
            ),
          ),
        ],

        // ── DIGITAL TWIN BANNER ───────────────────────────────────────
        if (response.digitalTwin != null)
          SliverToBoxAdapter(
            child: Padding(
              padding: const EdgeInsets.fromLTRB(22, 14, 22, 0),
              child: _DigitalTwinBanner(twin: response.digitalTwin!),
            ),
          ),

        // ── ZONE HEATMAP ──────────────────────────────────────────────
        _SectionHeader(title: 'Ball Trajectory'),
        SliverToBoxAdapter(
          child: Padding(
            padding: const EdgeInsets.fromLTRB(22, 0, 22, 0),
            child: ZoneHeatmap(
              targetZone:  response.goalZone,
              hitZone:     response.digitalTwin?.zoneHit ?? response.goalZone,
              predictedX:  response.digitalTwin?.predictedXM ?? 0.0,
              predictedY:  response.digitalTwin?.predictedYM ?? 0.0,
            ),
          ),
        ),

        // ── COACHING FEEDBACK ─────────────────────────────────────────
        _SectionHeader(title: 'Coaching Feedback'),
        SliverPadding(
          padding: const EdgeInsets.symmetric(horizontal: 22),
          sliver: SliverList.builder(
            itemCount: response.coachingFeedback.length,
            itemBuilder: (_, i) => CoachingCard(
              item: response.coachingFeedback[i],
              index: i,
            ),
          ),
        ),

        // ── PIPELINE WARNINGS ─────────────────────────────────────────
        if (response.pipelineWarnings.isNotEmpty) ...[
          _SectionHeader(title: 'System Warnings', isWarning: true),
          SliverPadding(
            padding: const EdgeInsets.symmetric(horizontal: 22),
            sliver: SliverList.builder(
              itemCount: response.pipelineWarnings.length,
              itemBuilder: (_, i) => _WarningRow(
                warning: response.pipelineWarnings[i],
              ),
            ),
          ),
        ],

        // ── BOTTOM CTA ────────────────────────────────────────────────
        SliverToBoxAdapter(
          child: Padding(
            padding: const EdgeInsets.fromLTRB(22, 28, 22, 0),
            child: Row(
              children: [
                Expanded(
                  child: _OutlineButton(
                    label: 'TRY AGAIN',
                    icon: Icons.refresh_rounded,
                    onTap: () {},
                  ),
                ),
                const SizedBox(width: 12),
                Expanded(
                  child: _PrimaryButton(
                    label: 'SAVE SESSION',
                    icon: Icons.bookmark_add_rounded,
                    onTap: () => _showSaveSnackbar(context),
                  ),
                ),
              ],
            ),
          ),
        ),

        const SliverToBoxAdapter(child: SizedBox(height: 48)),
      ],
    );
  }

  void _showSaveSnackbar(BuildContext context) {
    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(
        backgroundColor: _K.card,
        behavior: SnackBarBehavior.floating,
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
        content: Row(
          children: [
            const Icon(Icons.check_circle_rounded, color: _K.green, size: 18),
            const SizedBox(width: 10),
            Text(
              'Session saved.',
              style: TextStyle(
                color: _K.text,
                fontWeight: FontWeight.w600,
                fontSize: 13,
              ),
            ),
          ],
        ),
        duration: const Duration(seconds: 2),
      ),
    );
  }
}

// ─────────────────────────────────────────────────────────────────────────────
// SECTION HEADER
// ─────────────────────────────────────────────────────────────────────────────
class _SectionHeader extends SliverToBoxAdapter {
  _SectionHeader({required String title, bool isWarning = false})
      : super(
          child: Padding(
            padding: const EdgeInsets.fromLTRB(22, 30, 22, 0),
            child: Row(
              children: [
                Container(
                  width: 3,
                  height: 14,
                  decoration: BoxDecoration(
                    color: isWarning ? _K.red : _K.green,
                    borderRadius: BorderRadius.circular(2),
                  ),
                ),
                const SizedBox(width: 10),
                Text(
                  title.toUpperCase(),
                  style: TextStyle(
                    color: isWarning ? _K.red : _K.text,
                    fontSize: 10,
                    fontWeight: FontWeight.w800,
                    letterSpacing: 2.2,
                  ),
                ),
                const SizedBox(width: 12),
                Expanded(child: Container(height: 1, color: _K.border)),
              ],
            ),
          ),
        );
}

// ─────────────────────────────────────────────────────────────────────────────
// HERO CARD
// ─────────────────────────────────────────────────────────────────────────────
class _HeroCard extends StatefulWidget {
  const _HeroCard({required this.playerScore, required this.physics});
  final PlayerScore playerScore;
  final PhysicsResult physics;

  @override
  State<_HeroCard> createState() => _HeroCardState();
}

class _HeroCardState extends State<_HeroCard>
    with SingleTickerProviderStateMixin {
  late AnimationController _ctrl;
  late Animation<double> _ring;
  late Animation<int>    _counter;

  @override
  void initState() {
    super.initState();
    final score = _resolveScore();
    _ctrl = AnimationController(
      vsync: this,
      duration: const Duration(milliseconds: 1800),
    );
    _ring    = CurvedAnimation(parent: _ctrl, curve: const Interval(0.0, 0.85, curve: _ExpoOut()));
    _counter = IntTween(begin: 0, end: score).animate(
      CurvedAnimation(parent: _ctrl, curve: const Interval(0.0, 0.85, curve: _ExpoOut())),
    );
    _ctrl.forward();
  }

  @override
  void dispose() { _ctrl.dispose(); super.dispose(); }

  int _resolveScore() {
    final s = widget.playerScore.score;
    if (s > 0) return s;
    return ((widget.physics.v0MeasuredMs / 30.0) * 100).clamp(0, 100).toInt();
  }

  @override
  Widget build(BuildContext context) {
    final score = _resolveScore();
    final level = widget.playerScore.level.isNotEmpty
        ? widget.playerScore.level : 'Beginner';
    final accentColor = _K.levelColor(level);

    return AnimatedBuilder(
      animation: _ctrl,
      builder: (_, __) {
        return Container(
          decoration: BoxDecoration(
            color: _K.card,
            borderRadius: BorderRadius.circular(24),
            border: Border.all(color: _K.border2, width: 1),
            boxShadow: [
              BoxShadow(
                color: accentColor.withOpacity(0.08),
                blurRadius: 40,
                offset: const Offset(0, 10),
              ),
              BoxShadow(
                color: Colors.black.withOpacity(0.5),
                blurRadius: 20,
                offset: const Offset(0, 6),
              ),
            ],
          ),
          child: Column(
            children: [
              // top accent line
              Container(
                height: 2,
                decoration: BoxDecoration(
                  borderRadius: const BorderRadius.vertical(top: Radius.circular(24)),
                  gradient: LinearGradient(
                    colors: [Colors.transparent, accentColor, Colors.transparent],
                  ),
                ),
              ),
              Padding(
                padding: const EdgeInsets.fromLTRB(24, 28, 24, 28),
                child: Column(
                  children: [
                    // label
                    Text(
                      'TECHNIQUE SCORE',
                      style: TextStyle(
                        color: _K.muted,
                        fontSize: 9,
                        fontWeight: FontWeight.w800,
                        letterSpacing: 2.5,
                      ),
                    ),
                    const SizedBox(height: 28),
                    // ring
                    Stack(
                      alignment: Alignment.center,
                      children: [
                        // outer glow ring
                        SizedBox(
                          width: 170,
                          height: 170,
                          child: CustomPaint(
                            painter: _GlowRingPainter(
                              progress: _ring.value,
                              color: accentColor,
                              trackColor: Colors.white.withOpacity(0.04),
                            ),
                          ),
                        ),
                        // score + level
                        Column(
                          mainAxisSize: MainAxisSize.min,
                          children: [
                            Text(
                              '${_counter.value}',
                              style: const TextStyle(
                                color: _K.text,
                                fontSize: 58,
                                fontWeight: FontWeight.w900,
                                height: 1.0,
                                letterSpacing: -3,
                              ),
                            ),
                            const SizedBox(height: 2),
                            Text(
                              '/ 100',
                              style: TextStyle(
                                color: _K.muted,
                                fontSize: 12,
                                fontWeight: FontWeight.w600,
                              ),
                            ),
                          ],
                        ),
                      ],
                    ),
                    const SizedBox(height: 22),
                    // rank badge
                    Container(
                      padding: const EdgeInsets.symmetric(horizontal: 18, vertical: 7),
                      decoration: BoxDecoration(
                        color: accentColor.withOpacity(0.10),
                        borderRadius: BorderRadius.circular(50),
                        border: Border.all(
                          color: accentColor.withOpacity(0.35),
                          width: 1,
                        ),
                      ),
                      child: Row(
                        mainAxisSize: MainAxisSize.min,
                        children: [
                          Container(
                            width: 6,
                            height: 6,
                            decoration: BoxDecoration(
                              color: accentColor,
                              shape: BoxShape.circle,
                              boxShadow: [BoxShadow(color: accentColor, blurRadius: 5)],
                            ),
                          ),
                          const SizedBox(width: 8),
                          Text(
                            '${level.toUpperCase()} TIER',
                            style: TextStyle(
                              color: accentColor,
                              fontSize: 11,
                              fontWeight: FontWeight.w800,
                              letterSpacing: 1.8,
                            ),
                          ),
                        ],
                      ),
                    ),
                    const SizedBox(height: 28),
                    // physics stats row
                    Container(
                      padding: const EdgeInsets.symmetric(vertical: 16, horizontal: 8),
                      decoration: BoxDecoration(
                        color: Colors.white.withOpacity(0.02),
                        borderRadius: BorderRadius.circular(14),
                        border: Border.all(color: _K.border),
                      ),
                      child: IntrinsicHeight(
                        child: Row(
                          children: [
                            _PhysStat(
                              value: widget.physics.v0MeasuredMs.toStringAsFixed(1),
                              unit: 'm/s',
                              label: 'Ball Speed',
                            ),
                            _PhysDivider(),
                            _PhysStat(
                              value: widget.physics.thetaVDeg.toStringAsFixed(1),
                              unit: '°',
                              label: 'V. Angle',
                            ),
                            _PhysDivider(),
                            _PhysStat(
                              value: widget.physics.crossbarClearanceM.toStringAsFixed(2),
                              unit: 'm',
                              label: 'Crossbar',
                              color: widget.physics.safetyMarginSatisfied
                                  ? _K.green
                                  : _K.red,
                            ),
                            _PhysDivider(),
                            _PhysStat(
                              value: widget.physics.thetaHDeg.toStringAsFixed(1),
                              unit: '°',
                              label: 'H. Angle',
                            ),
                          ],
                        ),
                      ),
                    ),
                  ],
                ),
              ),
            ],
          ),
        );
      },
    );
  }
}

class _PhysStat extends StatelessWidget {
  const _PhysStat({
    required this.value,
    required this.unit,
    required this.label,
    this.color = _K.text,
  });
  final String value;
  final String unit;
  final String label;
  final Color color;

  @override
  Widget build(BuildContext context) {
    return Expanded(
      child: Column(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          RichText(
            text: TextSpan(
              children: [
                TextSpan(
                  text: value,
                  style: TextStyle(
                    color: color,
                    fontSize: 17,
                    fontWeight: FontWeight.w800,
                    letterSpacing: -0.5,
                    fontFeatures: const [FontFeature.tabularFigures()],
                  ),
                ),
                TextSpan(
                  text: unit,
                  style: TextStyle(
                    color: _K.muted,
                    fontSize: 10,
                    fontWeight: FontWeight.w600,
                  ),
                ),
              ],
            ),
          ),
          const SizedBox(height: 3),
          Text(
            label.toUpperCase(),
            style: const TextStyle(
              color: _K.muted,
              fontSize: 8,
              fontWeight: FontWeight.w700,
              letterSpacing: 1.2,
            ),
          ),
        ],
      ),
    );
  }
}

class _PhysDivider extends StatelessWidget {
  @override
  Widget build(BuildContext context) =>
      Container(width: 1, color: _K.border, margin: const EdgeInsets.symmetric(vertical: 6));
}

// ─────────────────────────────────────────────────────────────────────────────
// GLOW RING PAINTER
// ─────────────────────────────────────────────────────────────────────────────
class _GlowRingPainter extends CustomPainter {
  const _GlowRingPainter({
    required this.progress,
    required this.color,
    required this.trackColor,
  });
  final double progress;
  final Color  color;
  final Color  trackColor;

  @override
  void paint(Canvas canvas, Size size) {
    final center = Offset(size.width / 2, size.height / 2);
    final radius = (size.width - 12) / 2;
    const startAngle = -math.pi / 2;

    // track
    canvas.drawArc(
      Rect.fromCircle(center: center, radius: radius),
      0, math.pi * 2, false,
      Paint()
        ..color = trackColor
        ..style = PaintingStyle.stroke
        ..strokeWidth = 8
        ..strokeCap = StrokeCap.round,
    );

    // glow layer
    if (progress > 0) {
      canvas.drawArc(
        Rect.fromCircle(center: center, radius: radius),
        startAngle,
        math.pi * 2 * progress,
        false,
        Paint()
          ..color = color.withOpacity(0.3)
          ..style = PaintingStyle.stroke
          ..strokeWidth = 18
          ..strokeCap = StrokeCap.round
          ..maskFilter = const MaskFilter.blur(BlurStyle.normal, 10),
      );
      // main arc
      canvas.drawArc(
        Rect.fromCircle(center: center, radius: radius),
        startAngle,
        math.pi * 2 * progress,
        false,
        Paint()
          ..color = color
          ..style = PaintingStyle.stroke
          ..strokeWidth = 8
          ..strokeCap = StrokeCap.round,
      );
    }
  }

  @override
  bool shouldRepaint(_GlowRingPainter old) =>
      old.progress != progress || old.color != color;
}

// ─────────────────────────────────────────────────────────────────────────────
// KEY INSIGHTS
// ─────────────────────────────────────────────────────────────────────────────
class _KeyInsightsSection extends StatelessWidget {
  const _KeyInsightsSection({required this.coachingFeedback});
  final List<CoachingFeedbackItem> coachingFeedback;

  @override
  Widget build(BuildContext context) {
    if (coachingFeedback.isEmpty) return const SizedBox.shrink();

    final sorted = List<CoachingFeedbackItem>.from(coachingFeedback)
      ..sort((a, b) => b.deltaDeg.abs().compareTo(a.deltaDeg.abs()));
    final worst = sorted.first;
    final best  = sorted.last;

    return Padding(
      padding: const EdgeInsets.fromLTRB(22, 26, 22, 0),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Padding(
            padding: const EdgeInsets.only(bottom: 12),
            child: Row(
              children: [
                Container(width: 3, height: 14,
                    decoration: BoxDecoration(
                      color: _K.green, borderRadius: BorderRadius.circular(2))),
                const SizedBox(width: 10),
                const Text(
                  'KEY INSIGHTS',
                  style: TextStyle(
                    color: _K.text,
                    fontSize: 10,
                    fontWeight: FontWeight.w800,
                    letterSpacing: 2.2,
                  ),
                ),
                const SizedBox(width: 12),
                Expanded(child: Container(height: 1, color: _K.border)),
              ],
            ),
          ),
          Row(
            children: [
              Expanded(
                child: _InsightTile(
                  icon: Icons.bolt_rounded,
                  iconColor: _K.red,
                  type: 'Primary Leak',
                  body: _labelFor(worst),
                  delta: worst.deltaDeg,
                ),
              ),
              const SizedBox(width: 10),
              Expanded(
                child: _InsightTile(
                  icon: Icons.verified_rounded,
                  iconColor: _K.green,
                  type: 'Elite Mechanic',
                  body: _labelFor(best),
                  delta: best.deltaDeg,
                  positive: true,
                ),
              ),
            ],
          ),
        ],
      ),
    );
  }

  String _labelFor(CoachingFeedbackItem item) =>
      item.label.isNotEmpty ? item.label : item.variable.replaceAll('_', ' ');
}

class _InsightTile extends StatelessWidget {
  const _InsightTile({
    required this.icon,
    required this.iconColor,
    required this.type,
    required this.body,
    required this.delta,
    this.positive = false,
  });
  final IconData icon;
  final Color    iconColor;
  final String   type;
  final String   body;
  final double   delta;
  final bool     positive;

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.all(14),
      decoration: BoxDecoration(
        color: _K.card,
        borderRadius: BorderRadius.circular(16),
        border: Border.all(color: _K.border),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              Icon(icon, color: iconColor, size: 14),
              const SizedBox(width: 6),
              Text(
                type.toUpperCase(),
                style: TextStyle(
                  color: iconColor,
                  fontSize: 8,
                  fontWeight: FontWeight.w800,
                  letterSpacing: 1.4,
                ),
              ),
            ],
          ),
          const SizedBox(height: 8),
          Text(
            body,
            style: const TextStyle(
              color: _K.text,
              fontSize: 13,
              fontWeight: FontWeight.w700,
              height: 1.3,
            ),
          ),
          const SizedBox(height: 6),
          Container(
            padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 3),
            decoration: BoxDecoration(
              color: iconColor.withOpacity(0.12),
              borderRadius: BorderRadius.circular(6),
            ),
            child: Text(
              positive
                  ? '±${delta.abs().toStringAsFixed(1)}° on target'
                  : '${delta.toStringAsFixed(1)}° off target',
              style: TextStyle(
                color: iconColor,
                fontSize: 10,
                fontWeight: FontWeight.w700,
              ),
            ),
          ),
        ],
      ),
    );
  }
}

// ─────────────────────────────────────────────────────────────────────────────
// SCORE BREAKDOWN — same logic, visual upgrade
// ─────────────────────────────────────────────────────────────────────────────
class _ScoreBreakdown extends StatefulWidget {
  const _ScoreBreakdown({required this.ik, this.playerScore});
  final IkResult    ik;
  final PlayerScore? playerScore;

  @override
  State<_ScoreBreakdown> createState() => _ScoreBreakdownState();
}

class _ScoreBreakdownState extends State<_ScoreBreakdown>
    with SingleTickerProviderStateMixin {
  late AnimationController _ctrl;

  @override
  void initState() {
    super.initState();
    _ctrl = AnimationController(
      vsync: this,
      duration: const Duration(milliseconds: 1200),
    );
    Future.delayed(const Duration(milliseconds: 300), () {
      if (mounted) _ctrl.forward();
    });
  }

  @override
  void dispose() { _ctrl.dispose(); super.dispose(); }

  @override
  Widget build(BuildContext context) {
    final breakdown = Map<String, int>.from(
      widget.playerScore?.breakdown ?? {},
    );
    if (breakdown.isEmpty) {
      breakdown['hip_flexion']       = 75;
      breakdown['knee_angle']        = 85;
      breakdown['support_knee']      = 60;
      breakdown['trunk_inclination'] = 90;
    }

    return Container(
      padding: const EdgeInsets.all(20),
      decoration: BoxDecoration(
        color: _K.card,
        borderRadius: BorderRadius.circular(20),
        border: Border.all(color: _K.border),
      ),
      child: AnimatedBuilder(
        animation: _ctrl,
        builder: (_, __) {
          return Column(
            children: breakdown.entries.toList().asMap().entries.map((entry) {
              final idx = entry.key;
              final e   = entry.value;
              final val = e.value;
              final progress = CurvedAnimation(
                parent: _ctrl,
                curve: Interval(
                  idx * 0.12,
                  0.4 + idx * 0.12,
                  curve: Curves.easeOutCubic,
                ),
              ).value;

              final Color barColor = val >= 80
                  ? _K.green
                  : val >= 60
                      ? _K.blue
                      : val >= 40
                          ? _K.orange
                          : _K.red;

              return Padding(
                padding: const EdgeInsets.only(bottom: 16),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Row(
                      children: [
                        Expanded(
                          child: Text(
                            e.key.replaceAll('_', ' ').toUpperCase(),
                            style: const TextStyle(
                              color: _K.muted,
                              fontSize: 8,
                              fontWeight: FontWeight.w700,
                              letterSpacing: 1.4,
                            ),
                          ),
                        ),
                        Text(
                          val.toString(),
                          style: TextStyle(
                            color: barColor,
                            fontSize: 13,
                            fontWeight: FontWeight.w800,
                            fontFeatures: const [FontFeature.tabularFigures()],
                          ),
                        ),
                      ],
                    ),
                    const SizedBox(height: 6),
                    Stack(
                      children: [
                        // track
                        Container(
                          height: 4,
                          decoration: BoxDecoration(
                            color: Colors.white.withOpacity(0.05),
                            borderRadius: BorderRadius.circular(2),
                          ),
                        ),
                        // fill
                        FractionallySizedBox(
                          widthFactor: (val / 100.0 * progress).clamp(0.0, 1.0),
                          child: Container(
                            height: 4,
                            decoration: BoxDecoration(
                              color: barColor,
                              borderRadius: BorderRadius.circular(2),
                              boxShadow: [
                                BoxShadow(
                                  color: barColor.withOpacity(0.4),
                                  blurRadius: 6,
                                ),
                              ],
                            ),
                          ),
                        ),
                      ],
                    ),
                  ],
                ),
              );
            }).toList(),
          );
        },
      ),
    );
  }
}

// ─────────────────────────────────────────────────────────────────────────────
// DIGITAL TWIN BANNER — same logic, visual upgrade
// ─────────────────────────────────────────────────────────────────────────────
class _DigitalTwinBanner extends StatelessWidget {
  const _DigitalTwinBanner({required this.twin});
  final DigitalTwinResult twin;

  @override
  Widget build(BuildContext context) {
    final passed = twin.verificationPassed;
    final color  = passed ? _K.green : _K.orange;

    return Container(
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: color.withOpacity(0.06),
        borderRadius: BorderRadius.circular(16),
        border: Border.all(color: color.withOpacity(0.28), width: 1),
      ),
      child: Row(
        children: [
          Container(
            width: 40,
            height: 40,
            decoration: BoxDecoration(
              color: color.withOpacity(0.12),
              borderRadius: BorderRadius.circular(10),
            ),
            child: Icon(
              passed ? Icons.verified_rounded : Icons.precision_manufacturing_rounded,
              color: color,
              size: 20,
            ),
          ),
          const SizedBox(width: 14),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  passed ? 'DIGITAL TWIN VERIFIED' : 'DIGITAL TWIN · ZONE ${twin.zoneHit}',
                  style: TextStyle(
                    color: color,
                    fontSize: 10,
                    fontWeight: FontWeight.w800,
                    letterSpacing: 1.6,
                  ),
                ),
                const SizedBox(height: 3),
                Text(
                  'Impact predicted at y=${twin.predictedYM.toStringAsFixed(2)}m  '
                  'x=${twin.predictedXM.toStringAsFixed(2)}m',
                  style: const TextStyle(
                    color: _K.muted,
                    fontSize: 11,
                    fontWeight: FontWeight.w500,
                  ),
                ),
              ],
            ),
          ),
          if (passed)
            Container(
              width: 28,
              height: 28,
              decoration: BoxDecoration(
                color: _K.green.withOpacity(0.15),
                shape: BoxShape.circle,
              ),
              child: const Icon(Icons.check_rounded, color: _K.green, size: 16),
            ),
        ],
      ),
    );
  }
}

// ─────────────────────────────────────────────────────────────────────────────
// WARNING ROW
// ─────────────────────────────────────────────────────────────────────────────
class _WarningRow extends StatelessWidget {
  const _WarningRow({required this.warning});
  final String warning;

  @override
  Widget build(BuildContext context) {
    return Container(
      margin: const EdgeInsets.only(bottom: 8),
      padding: const EdgeInsets.all(12),
      decoration: BoxDecoration(
        color: _K.red.withOpacity(0.06),
        borderRadius: BorderRadius.circular(12),
        border: Border.all(color: _K.red.withOpacity(0.22)),
      ),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          const Icon(Icons.warning_amber_rounded, color: _K.red, size: 14),
          const SizedBox(width: 10),
          Expanded(
            child: Text(
              warning,
              style: const TextStyle(
                color: _K.muted,
                fontSize: 12,
                fontWeight: FontWeight.w500,
                height: 1.5,
              ),
            ),
          ),
        ],
      ),
    );
  }
}

// ─────────────────────────────────────────────────────────────────────────────
// BUTTONS
// ─────────────────────────────────────────────────────────────────────────────
class _TryAgainButton extends StatelessWidget {
  const _TryAgainButton({required this.onTap});
  final VoidCallback onTap;

  @override
  Widget build(BuildContext context) {
    return GestureDetector(
      onTap: onTap,
      child: Container(
        padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 7),
        decoration: BoxDecoration(
          color: _K.subtle.withOpacity(0.8),
          borderRadius: BorderRadius.circular(10),
          border: Border.all(color: _K.border2),
        ),
        child: const Text(
          'TRY AGAIN',
          style: TextStyle(
            color: _K.text,
            fontSize: 10,
            fontWeight: FontWeight.w800,
            letterSpacing: 1.5,
          ),
        ),
      ),
    );
  }
}

class _OutlineButton extends StatelessWidget {
  const _OutlineButton({
    required this.label,
    required this.icon,
    required this.onTap,
  });
  final String label;
  final IconData icon;
  final VoidCallback onTap;

  @override
  Widget build(BuildContext context) {
    return GestureDetector(
      onTap: onTap,
      child: Container(
        height: 54,
        decoration: BoxDecoration(
          color: Colors.transparent,
          borderRadius: BorderRadius.circular(14),
          border: Border.all(color: _K.border2),
        ),
        child: Row(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Icon(icon, color: _K.muted, size: 16),
            const SizedBox(width: 8),
            Text(
              label,
              style: const TextStyle(
                color: _K.muted,
                fontSize: 11,
                fontWeight: FontWeight.w800,
                letterSpacing: 1.5,
              ),
            ),
          ],
        ),
      ),
    );
  }
}

class _PrimaryButton extends StatelessWidget {
  const _PrimaryButton({
    required this.label,
    required this.icon,
    required this.onTap,
  });
  final String label;
  final IconData icon;
  final VoidCallback onTap;

  @override
  Widget build(BuildContext context) {
    return GestureDetector(
      onTap: onTap,
      child: Container(
        height: 54,
        decoration: BoxDecoration(
          gradient: const LinearGradient(
            colors: [Color(0xFF00E5A0), Color(0xFF00C980)],
            begin: Alignment.topLeft,
            end: Alignment.bottomRight,
          ),
          borderRadius: BorderRadius.circular(14),
          boxShadow: [
            BoxShadow(
              color: _K.green.withOpacity(0.35),
              blurRadius: 20,
              offset: const Offset(0, 5),
            ),
          ],
        ),
        child: Row(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Icon(icon, color: _K.bg, size: 16),
            const SizedBox(width: 8),
            Text(
              label,
              style: TextStyle(
                color: _K.bg,
                fontSize: 11,
                fontWeight: FontWeight.w900,
                letterSpacing: 1.5,
              ),
            ),
          ],
        ),
      ),
    );
  }
}

class _PillChip extends StatelessWidget {
  const _PillChip({required this.label, required this.color});
  final String label;
  final Color  color;

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
      decoration: BoxDecoration(
        color: color.withOpacity(0.10),
        borderRadius: BorderRadius.circular(50),
        border: Border.all(color: color.withOpacity(0.25)),
      ),
      child: Text(
        label,
        style: TextStyle(
          color: color,
          fontSize: 9,
          fontWeight: FontWeight.w800,
          letterSpacing: 1.5,
        ),
      ),
    );
  }
}

// ─────────────────────────────────────────────────────────────────────────────
// EMPTY / LOADING / ERROR  — same logic as original
// ─────────────────────────────────────────────────────────────────────────────
class _EmptyState extends StatelessWidget {
  const _EmptyState();

  @override
  Widget build(BuildContext context) {
    return Center(
      child: Column(
        mainAxisSize: MainAxisSize.min,
        children: [
          Container(
            width: 72,
            height: 72,
            decoration: BoxDecoration(
              color: _K.subtle,
              shape: BoxShape.circle,
            ),
            child: const Icon(Icons.sports_soccer, size: 32, color: _K.muted),
          ),
          const SizedBox(height: 18),
          const Text(
            'NO ANALYSIS YET',
            style: TextStyle(
              color: _K.text,
              fontSize: 16,
              fontWeight: FontWeight.w800,
              letterSpacing: 1.5,
            ),
          ),
          const SizedBox(height: 6),
          const Text(
            'Record a kick to begin.',
            style: TextStyle(color: _K.muted, fontSize: 13),
          ),
        ],
      ),
    );
  }
}

class _LoadingState extends StatefulWidget {
  const _LoadingState();

  @override
  State<_LoadingState> createState() => _LoadingStateState();
}

class _LoadingStateState extends State<_LoadingState>
    with SingleTickerProviderStateMixin {
  late AnimationController _ctrl;

  @override
  void initState() {
    super.initState();
    _ctrl = AnimationController(vsync: this, duration: const Duration(seconds: 2))
      ..repeat();
  }

  @override
  void dispose() { _ctrl.dispose(); super.dispose(); }

  @override
  Widget build(BuildContext context) {
    return Center(
      child: Column(
        mainAxisSize: MainAxisSize.min,
        children: [
          SizedBox(
            width: 56,
            height: 56,
            child: AnimatedBuilder(
              animation: _ctrl,
              builder: (_, __) => CircularProgressIndicator(
                value: null,
                strokeWidth: 2.5,
                valueColor: AlwaysStoppedAnimation<Color>(
                  Color.lerp(_K.green, _K.blue, _ctrl.value)!,
                ),
              ),
            ),
          ),
          const SizedBox(height: 24),
          const Text(
            'ANALYSING KICK',
            style: TextStyle(
              color: _K.green,
              fontSize: 14,
              fontWeight: FontWeight.w800,
              letterSpacing: 3,
            ),
          ),
          const SizedBox(height: 8),
          const Text(
            'Physics engine + IK solver running…',
            style: TextStyle(color: _K.muted, fontSize: 12),
          ),
        ],
      ),
    );
  }
}

class _ErrorState extends StatelessWidget {
  const _ErrorState({required this.message});
  final String message;

  @override
  Widget build(BuildContext context) {
    return Center(
      child: Padding(
        padding: const EdgeInsets.all(32),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            Container(
              width: 72,
              height: 72,
              decoration: BoxDecoration(
                color: _K.red.withOpacity(0.10),
                shape: BoxShape.circle,
                border: Border.all(color: _K.red.withOpacity(0.3)),
              ),
              child: const Icon(Icons.error_outline_rounded,
                  color: _K.red, size: 30),
            ),
            const SizedBox(height: 20),
            const Text(
              'ANALYSIS FAILED',
              style: TextStyle(
                color: _K.red,
                fontSize: 14,
                fontWeight: FontWeight.w800,
                letterSpacing: 1.8,
              ),
            ),
            const SizedBox(height: 10),
            Text(
              message,
              style: const TextStyle(
                color: _K.muted,
                fontSize: 13,
                height: 1.5,
              ),
              textAlign: TextAlign.center,
            ),
            const SizedBox(height: 28),
            PiqPrimaryButton(
              label: 'TRY AGAIN',
              icon: Icons.refresh_rounded,
              onPressed: () => context.go('/home'),
            ),
          ],
        ),
      ),
    );
  }
}

// ─────────────────────────────────────────────────────────────────────────────
// CUSTOM EASING
// ─────────────────────────────────────────────────────────────────────────────
class _ExpoOut extends Curve {
  const _ExpoOut();

  @override
  double transformInternal(double t) =>
      t == 1.0 ? 1.0 : 1.0 - math.pow(2, -10 * t);
}