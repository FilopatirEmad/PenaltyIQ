import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../core/theme/app_theme.dart';
import '../../domain/providers/calibration_provider.dart';
import '../../domain/providers/analysis_provider.dart';
import '../widgets/piq_app_bar.dart';
import '../widgets/piq_widgets.dart';
import '../widgets/zone_selector.dart';

/// Home Screen — PERFORMANCE LAB entry point.
///
/// Stitch design language:
///   - Black header with italic lime "PERFORMANCE LAB" branding
///   - 8-zone target grid (soccer goal)
///   - Calibration status card
///   - Lime "CONFIRM TARGET" CTA
class HomeScreen extends ConsumerStatefulWidget {
  const HomeScreen({super.key});

  @override
  ConsumerState<HomeScreen> createState() => _HomeScreenState();
}

class _HomeScreenState extends ConsumerState<HomeScreen> {
  String? _selectedZone;

  @override
  Widget build(BuildContext context) {
    final calibState = ref.watch(calibrationProvider);

    return Scaffold(
      backgroundColor: PiqColors.background,
      appBar: const PiqAppBar(title: 'PERFORMANCE LAB'),
      body: SafeArea(
        top: false,
        child: CustomScrollView(
          slivers: [
            // ── Page header ───────────────────────────────────────────────
            SliverToBoxAdapter(
              child: Padding(
                padding: const EdgeInsets.fromLTRB(20, 24, 20, 4),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      'SET YOUR AIM',
                      style: PiqTextStyles.labelCaps.copyWith(
                        color: PiqColors.primary,
                        letterSpacing: 2,
                      ),
                    ),
                    const SizedBox(height: 4),
                    Text(
                      'SELECT TARGET ZONE',
                      style: PiqTextStyles.headlineLg.copyWith(
                        color: PiqColors.onSurface,
                        letterSpacing: -0.5,
                      ),
                    ),
                    const SizedBox(height: 4),
                    Text(
                      'Choose where your kick is aimed. '
                      'The biomechanical engine will optimise accordingly.',
                      style: PiqTextStyles.bodyMd.copyWith(
                        color: PiqColors.onSurfaceVariant,
                      ),
                    ),
                  ],
                ),
              ),
            ),

            // ── Calibration status ────────────────────────────────────────
            SliverToBoxAdapter(
              child: Padding(
                padding: const EdgeInsets.fromLTRB(20, 16, 20, 0),
                child: _CalibrationBanner(calibState: calibState),
              ),
            ),

            // ── Zone selector (goal grid) ─────────────────────────────────
            SliverToBoxAdapter(
              child: Padding(
                padding: const EdgeInsets.fromLTRB(20, 20, 20, 0),
                child: _GoalZoneGrid(
                  selectedZone: _selectedZone,
                  onZoneSelected: (z) => setState(() => _selectedZone = z),
                ),
              ),
            ),

            // ── Selected zone display ─────────────────────────────────────
            if (_selectedZone != null)
              SliverToBoxAdapter(
                child: Padding(
                  padding: const EdgeInsets.fromLTRB(20, 12, 20, 0),
                  child: _ZoneConfirmRow(zone: _selectedZone!),
                ),
              ),

            // ── Re-calibrate ──────────────────────────────────────────────
            if (calibState.isLocked)
              SliverToBoxAdapter(
                child: Padding(
                  padding: const EdgeInsets.fromLTRB(20, 4, 20, 0),
                  child: TextButton.icon(
                    onPressed: () {
                      ref.read(calibrationProvider.notifier).reset();
                      ref.read(analysisProvider.notifier).reset();
                    },
                    icon: const Icon(Icons.refresh, size: 14,
                        color: PiqColors.onSurfaceVariant),
                    label: Text(
                      'RE-CALIBRATE',
                      style: PiqTextStyles.labelCaps.copyWith(
                        color: PiqColors.onSurfaceVariant,
                      ),
                    ),
                  ),
                ),
              ),

            const SliverToBoxAdapter(child: SizedBox(height: 120)),
          ],
        ),
      ),
      bottomNavigationBar: _ConfirmBar(
        selectedZone: _selectedZone,
        isLocked: calibState.isLocked,
        onConfirm: _selectedZone == null
            ? null
            : () {
                if (calibState.isLocked) {
                  context.go('/recording?zone=${_selectedZone!}');
                } else {
                  context.go('/imu-gate');
                }
              },
      ),
    );
  }
}

// ─────────────────────────────────────────────────────────────────────────────
// Calibration Banner
// ─────────────────────────────────────────────────────────────────────────────

class _CalibrationBanner extends StatelessWidget {
  const _CalibrationBanner({required this.calibState});
  final CalibrationState calibState;

  @override
  Widget build(BuildContext context) {
    final locked = calibState.isLocked;
    final color  = locked ? PiqColors.primary : PiqColors.tertiary;
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 10),
      decoration: BoxDecoration(
        color: color.withOpacity(0.08),
        borderRadius: PiqRadius.borderLg,
        border: Border.all(color: color.withOpacity(0.35)),
      ),
      child: Row(
        children: [
          Icon(locked ? Icons.lock : Icons.lock_open_rounded,
              color: color, size: 16),
          const SizedBox(width: 10),
          Expanded(
            child: Text(
              locked
                  ? 'CALIBRATED — Segments locked. Ready to record.'
                  : 'CALIBRATION REQUIRED — Tap CONFIRM to begin.',
              style: PiqTextStyles.labelCaps.copyWith(color: color),
            ),
          ),
        ],
      ),
    );
  }
}

// ─────────────────────────────────────────────────────────────────────────────
// Goal Zone Grid  (Stitch 4×2 target grid inside a "goal post" frame)
// ─────────────────────────────────────────────────────────────────────────────

class _GoalZoneGrid extends StatelessWidget {
  const _GoalZoneGrid({
    required this.selectedZone,
    required this.onZoneSelected,
  });

  final String? selectedZone;
  final ValueChanged<String> onZoneSelected;

  // Zone IDs matching the backend schema (T1–T4 top row, B1–B4 bottom row)
  static const _zones = [
    ('T1', 'TOP LEFT'),
    ('T2', 'TOP CTR-L'),
    ('T3', 'TOP CTR-R'),
    ('T4', 'TOP RIGHT'),
    ('B1', 'BTM LEFT'),
    ('B2', 'BTM CTR-L'),
    ('B3', 'BTM CTR-R'),
    ('B4', 'BTM RIGHT'),
  ];

  @override
  Widget build(BuildContext context) {
    return Container(
      decoration: BoxDecoration(
        color: PiqColors.surfaceContainer,
        borderRadius: PiqRadius.borderXl,
        border: Border.all(color: PiqColors.outlineVariant),
      ),
      child: Column(
        children: [
          // Goal frame
          Padding(
            padding: const EdgeInsets.all(12),
            child: AspectRatio(
              aspectRatio: 3 / 2,
              child: Container(
                decoration: BoxDecoration(
                  color: Colors.black.withOpacity(0.4),
                  borderRadius: PiqRadius.borderLg,
                  border: Border.all(
                    color: Colors.white.withOpacity(0.2),
                    width: 3,
                  ),
                ),
                child: Stack(
                  children: [
                    // Net pattern overlay
                    Positioned.fill(
                      child: Opacity(
                        opacity: 0.04,
                        child: CustomPaint(painter: _NetPainter()),
                      ),
                    ),
                    // Zone grid
                    Padding(
                      padding: const EdgeInsets.all(6),
                      child: GridView.builder(
                        physics: const NeverScrollableScrollPhysics(),
                        gridDelegate:
                            const SliverGridDelegateWithFixedCrossAxisCount(
                          crossAxisCount: 4,
                          mainAxisSpacing: 6,
                          crossAxisSpacing: 6,
                        ),
                        itemCount: _zones.length,
                        itemBuilder: (_, i) {
                          final (id, lbl) = _zones[i];
                          final active = selectedZone == id;
                          return _ZoneCell(
                            id: id,
                            label: lbl,
                            isSelected: active,
                            onTap: () => onZoneSelected(id),
                          );
                        },
                      ),
                    ),
                  ],
                ),
              ),
            ),
          ),
        ],
      ),
    );
  }
}

class _ZoneCell extends StatelessWidget {
  const _ZoneCell({
    required this.id,
    required this.label,
    required this.isSelected,
    required this.onTap,
  });

  final String id;
  final String label;
  final bool isSelected;
  final VoidCallback onTap;

  @override
  Widget build(BuildContext context) {
    return GestureDetector(
      onTap: onTap,
      child: AnimatedContainer(
        duration: const Duration(milliseconds: 150),
        decoration: BoxDecoration(
          color: isSelected
              ? PiqColors.primary.withOpacity(0.18)
              : Colors.white.withOpacity(0.04),
          borderRadius: PiqRadius.borderMd,
          border: Border.all(
            color: isSelected
                ? PiqColors.primary
                : Colors.white.withOpacity(0.1),
            width: isSelected ? 1.5 : 1,
          ),
        ),
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Text(
              id,
              style: TextStyle(
                fontFamily: 'SpaceGrotesk',
                fontSize: 15,
                fontWeight: FontWeight.w700,
                color: isSelected
                    ? PiqColors.primary
                    : Colors.white.withOpacity(0.3),
              ),
            ),
            const SizedBox(height: 2),
            Text(
              label,
              style: TextStyle(
                fontFamily: 'SpaceGrotesk',
                fontSize: 7,
                fontWeight: FontWeight.w700,
                letterSpacing: 0.6,
                color: isSelected
                    ? PiqColors.primary
                    : Colors.white.withOpacity(0.3),
              ),
              textAlign: TextAlign.center,
            ),
          ],
        ),
      ),
    );
  }
}

class _NetPainter extends CustomPainter {
  @override
  void paint(Canvas canvas, Size size) {
    final p = Paint()
      ..color = Colors.white
      ..strokeWidth = 0.5;
    for (double x = 0; x < size.width; x += 12) {
      canvas.drawLine(Offset(x, 0), Offset(x, size.height), p);
    }
    for (double y = 0; y < size.height; y += 12) {
      canvas.drawLine(Offset(0, y), Offset(size.width, y), p);
    }
  }

  @override
  bool shouldRepaint(_) => false;
}

class _ZoneConfirmRow extends StatelessWidget {
  const _ZoneConfirmRow({required this.zone});
  final String zone;

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 10),
      decoration: BoxDecoration(
        color: PiqColors.surfaceContainerHigh,
        borderRadius: PiqRadius.borderLg,
        border: Border.all(color: PiqColors.outlineVariant),
      ),
      child: Row(
        children: [
          Container(
            width: 40, height: 40,
            decoration: BoxDecoration(
              shape: BoxShape.circle,
              border: Border.all(color: PiqColors.primary),
              color: Colors.black,
            ),
            child: const Icon(Icons.ads_click,
                color: PiqColors.primary, size: 18),
          ),
          const SizedBox(width: 12),
          Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text(
                'CURRENT SELECTION',
                style: PiqTextStyles.labelCaps.copyWith(
                  color: PiqColors.onSurfaceVariant,
                  fontSize: 10,
                ),
              ),
              Text(
                'ZONE $zone',
                style: PiqTextStyles.headlineMd.copyWith(
                  color: PiqColors.primary,
                  fontSize: 18,
                ),
              ),
            ],
          ),
        ],
      ),
    );
  }
}

// ─────────────────────────────────────────────────────────────────────────────
// Bottom Confirm Bar
// ─────────────────────────────────────────────────────────────────────────────

class _ConfirmBar extends StatelessWidget {
  const _ConfirmBar({
    required this.selectedZone,
    required this.isLocked,
    required this.onConfirm,
  });

  final String? selectedZone;
  final bool isLocked;
  final VoidCallback? onConfirm;

  @override
  Widget build(BuildContext context) {
    return Container(
      color: PiqColors.background,
      padding: EdgeInsets.fromLTRB(
          20, 12, 20, 12 + MediaQuery.of(context).padding.bottom),
      child: PiqPrimaryButton(
        label: selectedZone == null
            ? 'SELECT A ZONE FIRST'
            : isLocked
                ? 'RECORD KICK — ZONE $selectedZone'
                : 'CONFIRM TARGET',
        icon: selectedZone != null ? Icons.bolt : null,
        onPressed: onConfirm,
      ),
    );
  }
}