import 'package:flutter/material.dart';
import '../../core/theme/app_theme.dart';

/// Top app bar styled exactly like the Stitch "PERFORMANCE LAB" header.
///
/// - Black background, lime title in italic Space Grotesk
/// - Optional back button (lime chevron)
/// - Optional trailing widget
class PiqAppBar extends StatelessWidget implements PreferredSizeWidget {
  const PiqAppBar({
    super.key,
    this.title = 'PERFORMANCE LAB',
    this.showBack = false,
    this.trailing,
    this.onBack,
  });

  final String title;
  final bool showBack;
  final Widget? trailing;
  final VoidCallback? onBack;

  @override
  Size get preferredSize => const Size.fromHeight(64);

  @override
  Widget build(BuildContext context) {
    return Container(
      height: 64,
      decoration: const BoxDecoration(
        color: Colors.black,
        border: Border(
          bottom: BorderSide(color: Color(0xFF1A1A1A)),
        ),
      ),
      child: SafeArea(
        bottom: false,
        child: Padding(
          padding: const EdgeInsets.symmetric(horizontal: 16),
          child: Row(
            children: [
              if (showBack)
                GestureDetector(
                  onTap: onBack ?? () => Navigator.maybePop(context),
                  child: const Icon(
                    Icons.chevron_left,
                    color: PiqColors.primary,
                    size: 28,
                  ),
                )
              else
                const Icon(
                  Icons.sports_soccer,
                  color: PiqColors.primary,
                  size: 22,
                ),
              const SizedBox(width: 10),
              Text(
                title,
                style: const TextStyle(
                  fontFamily: 'SpaceGrotesk',
                  fontSize: 20,
                  fontWeight: FontWeight.w900,
                  color: PiqColors.primary,
                  fontStyle: FontStyle.italic,
                  letterSpacing: -0.5,
                ),
              ),
              const Spacer(),
              if (trailing != null) trailing!,
            ],
          ),
        ),
      ),
    );
  }
}

/// Bottom navigation bar — Stitch style.
/// Active tab gets full lime background + black icon/text.
class PiqBottomNav extends StatelessWidget {
  const PiqBottomNav({
    super.key,
    required this.currentIndex,
    required this.onTap,
  });

  final int currentIndex;
  final ValueChanged<int> onTap;

  static const _items = [
    _NavItem(icon: Icons.shutter_speed, label: 'TRACK'),
    _NavItem(icon: Icons.analytics,     label: 'LOGS'),
    _NavItem(icon: Icons.fitness_center, label: 'DRILLS'),
    _NavItem(icon: Icons.person,        label: 'PROFILE'),
  ];

  @override
  Widget build(BuildContext context) {
    return Container(
      height: 64 + MediaQuery.of(context).padding.bottom,
      decoration: const BoxDecoration(
        color: Color(0xFF121212),
        border: Border(top: BorderSide(color: Color(0xFF1E1E1E))),
      ),
      child: Padding(
        padding: EdgeInsets.only(bottom: MediaQuery.of(context).padding.bottom),
        child: Row(
          children: List.generate(_items.length, (i) {
            final active = i == currentIndex;
            return Expanded(
              child: GestureDetector(
                onTap: () => onTap(i),
                behavior: HitTestBehavior.opaque,
                child: AnimatedContainer(
                  duration: const Duration(milliseconds: 150),
                  color: active ? PiqColors.primary : Colors.transparent,
                  child: Column(
                    mainAxisAlignment: MainAxisAlignment.center,
                    children: [
                      Icon(
                        _items[i].icon,
                        color: active ? Colors.black : const Color(0xFF5A5A5A),
                        size: 22,
                      ),
                      const SizedBox(height: 4),
                      Text(
                        _items[i].label,
                        style: TextStyle(
                          fontFamily: 'SpaceGrotesk',
                          fontSize: 9,
                          fontWeight: FontWeight.w700,
                          letterSpacing: 1.5,
                          color: active ? Colors.black : const Color(0xFF5A5A5A),
                        ),
                      ),
                    ],
                  ),
                ),
              ),
            );
          }),
        ),
      ),
    );
  }
}

class _NavItem {
  const _NavItem({required this.icon, required this.label});
  final IconData icon;
  final String label;
}
