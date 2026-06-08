import 'package:flutter/material.dart';
import '../../core/theme/app_theme.dart';

/// Metric card — large number with label above, subtext below.
/// Used in results screen for score, velocity, etc.
class PiqMetricCard extends StatelessWidget {
  const PiqMetricCard({
    super.key,
    required this.label,
    required this.value,
    this.unit,
    this.valueColor = PiqColors.primary,
    this.subtext,
  });

  final String label;
  final String value;
  final String? unit;
  final Color valueColor;
  final String? subtext;

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.all(20),
      decoration: BoxDecoration(
        color: PiqColors.surfaceContainer,
        borderRadius: PiqRadius.borderXl,
        border: Border.all(color: PiqColors.outlineVariant),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(
            label.toUpperCase(),
            style: PiqTextStyles.labelCaps,
          ),
          const SizedBox(height: 12),
          Row(
            crossAxisAlignment: CrossAxisAlignment.end,
            children: [
              Text(
                value,
                style: PiqTextStyles.metricHuge.copyWith(
                  fontSize: 48,
                  color: valueColor,
                ),
              ),
              if (unit != null) ...[
                const SizedBox(width: 4),
                Padding(
                  padding: const EdgeInsets.only(bottom: 8),
                  child: Text(
                    unit!,
                    style: PiqTextStyles.headlineMd.copyWith(
                      color: PiqColors.onSurfaceVariant,
                    ),
                  ),
                ),
              ],
            ],
          ),
          if (subtext != null) ...[
            const SizedBox(height: 8),
            Text(subtext!, style: PiqTextStyles.bodyMd.copyWith(
              color: PiqColors.onSurfaceVariant,
            )),
          ],
        ],
      ),
    );
  }
}

/// Labelled progress bar row — label left, value right, bar below.
class PiqProgressRow extends StatelessWidget {
  const PiqProgressRow({
    super.key,
    required this.label,
    required this.valueText,
    required this.fraction,
    this.barColor = PiqColors.primary,
  });

  final String label;
  final String valueText;
  final double fraction;   // 0.0 – 1.0
  final Color barColor;

  @override
  Widget build(BuildContext context) {
    return Column(
      children: [
        Row(
          mainAxisAlignment: MainAxisAlignment.spaceBetween,
          children: [
            Text(label.toUpperCase(), style: PiqTextStyles.labelCaps),
            Text(
              valueText,
              style: PiqTextStyles.labelCaps.copyWith(color: barColor),
            ),
          ],
        ),
        const SizedBox(height: 6),
        ClipRRect(
          borderRadius: PiqRadius.borderMd,
          child: LinearProgressIndicator(
            value: fraction.clamp(0.0, 1.0),
            backgroundColor: PiqColors.surfaceVariant,
            valueColor: AlwaysStoppedAnimation<Color>(barColor),
            minHeight: 6,
          ),
        ),
      ],
    );
  }
}

/// Kinematic parameter row — icon, name, value, colored dot.
/// Matches Stitch "KINEMATIC PARAMETERS" list items.
class PiqParamRow extends StatelessWidget {
  const PiqParamRow({
    super.key,
    required this.label,
    required this.value,
    this.color = PiqColors.primary,
    this.icon = Icons.straighten,
  });

  final String label;
  final String value;
  final Color color;
  final IconData icon;

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 10),
      decoration: BoxDecoration(
        color: PiqColors.surfaceContainer,
        borderRadius: PiqRadius.borderMd,
        border: Border(left: BorderSide(color: color, width: 2)),
      ),
      child: Row(
        children: [
          Icon(icon, color: PiqColors.onSurfaceVariant, size: 20),
          const SizedBox(width: 12),
          Expanded(
            child: Text(label, style: PiqTextStyles.bodyMd),
          ),
          Text(
            value,
            style: PiqTextStyles.headlineMd.copyWith(
              fontSize: 20, color: color,
            ),
          ),
          const SizedBox(width: 10),
          Container(
            width: 8, height: 8,
            decoration: BoxDecoration(color: color, shape: BoxShape.circle),
          ),
        ],
      ),
    );
  }
}

/// Primary CTA button — full width, lime, Space Grotesk bold.
/// Wraps [ElevatedButton] with Stitch glow shadow.
class PiqPrimaryButton extends StatelessWidget {
  const PiqPrimaryButton({
    super.key,
    required this.label,
    this.onPressed,
    this.icon,
    this.isLoading = false,
  });

  final String label;
  final VoidCallback? onPressed;
  final IconData? icon;
  final bool isLoading;

  @override
  Widget build(BuildContext context) {
    return SizedBox(
      width: double.infinity,
      height: 54,
      child: ElevatedButton(
        onPressed: isLoading ? null : onPressed,
        style: ElevatedButton.styleFrom(
          backgroundColor:
              onPressed != null ? PiqColors.primary : PiqColors.surfaceVariant,
          foregroundColor:
              onPressed != null ? PiqColors.onPrimary : PiqColors.onSurfaceVariant,
          shape: const RoundedRectangleBorder(borderRadius: PiqRadius.borderLg),
          elevation: 0,
          shadowColor: Colors.transparent,
        ).copyWith(
          overlayColor: WidgetStateProperty.resolveWith(
            (states) => PiqColors.onPrimary.withOpacity(0.08),
          ),
        ),
        child: isLoading
            ? const SizedBox(
                height: 20, width: 20,
                child: CircularProgressIndicator(
                  strokeWidth: 2,
                  valueColor: AlwaysStoppedAnimation<Color>(PiqColors.onPrimary),
                ),
              )
            : Row(
                mainAxisAlignment: MainAxisAlignment.center,
                children: [
                  Text(
                    label.toUpperCase(),
                    style: const TextStyle(
                      fontFamily: 'SpaceGrotesk',
                      fontSize: 14,
                      fontWeight: FontWeight.w700,
                      letterSpacing: 1.2,
                    ),
                  ),
                  if (icon != null) ...[
                    const SizedBox(width: 8),
                    Icon(icon, size: 18),
                  ],
                ],
              ),
      ),
    );
  }
}

/// Lime glow chip / badge — small label in lime container.
class PiqChip extends StatelessWidget {
  const PiqChip(this.label, {super.key, this.color = PiqColors.primary});
  final String label;
  final Color color;

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
      decoration: BoxDecoration(
        color: color.withOpacity(0.15),
        borderRadius: PiqRadius.borderMd,
        border: Border.all(color: color.withOpacity(0.5)),
      ),
      child: Text(
        label.toUpperCase(),
        style: PiqTextStyles.labelCaps.copyWith(color: color),
      ),
    );
  }
}

/// Section header — uppercase label with optional accent bar.
class PiqSectionHeader extends StatelessWidget {
  const PiqSectionHeader(this.title, {super.key, this.color});
  final String title;
  final Color? color;

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.only(bottom: 12),
      child: Text(
        title.toUpperCase(),
        style: PiqTextStyles.labelCaps.copyWith(
          color: color ?? PiqColors.onSurfaceVariant,
          letterSpacing: 2,
        ),
      ),
    );
  }
}
