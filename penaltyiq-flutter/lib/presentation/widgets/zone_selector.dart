import 'package:flutter/material.dart';

/// 8-Zone Goal Selector Widget.
///
/// Displays a 4×2 grid matching the FIFA goal zone layout.
/// [SPEC §2.3, Table 2.1]:
///   Top row:    T1 T2 T3 T4   (y = 2.20m)
///   Bottom row: B1 B2 B3 B4   (y = 0.30m)
///
/// Visual design:
///   - Goal post outline with crossbar.
///   - 8 tappable zone cells.
///   - Selected zone highlighted with accent colour.
///   - Difficulty badge per zone.
class ZoneSelector extends StatelessWidget {
  const ZoneSelector({
    super.key,
    required this.selectedZone,
    required this.onZoneSelected,
  });

  final String? selectedZone;
  final ValueChanged<String> onZoneSelected;

  static const _zones = [
    // Top row [SPEC Table 2.1]
    _ZoneData('T1', 'Top\nFar Left',    'HIGH',     Color(0xFFEF5350)),
    _ZoneData('T2', 'Top\nCentre Left', 'HIGH',     Color(0xFFEF5350)),
    _ZoneData('T3', 'Top\nCentre Right','MODERATE', Color(0xFFFF9800)),
    _ZoneData('T4', 'Top\nFar Right',   'HIGH',     Color(0xFFEF5350)),
    // Bottom row [SPEC Table 2.1]
    _ZoneData('B1', 'Bot\nFar Left',    'MODERATE', Color(0xFFFF9800)),
    _ZoneData('B2', 'Bot\nCentre Left', 'LOW-MOD',  Color(0xFF8BC34A)),
    _ZoneData('B3', 'Bot\nCentre Right','LOW',       Color(0xFF4CAF50)),
    _ZoneData('B4', 'Bot\nFar Right',   'MODERATE', Color(0xFFFF9800)),
  ];

  @override
  Widget build(BuildContext context) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        const Padding(
          padding: EdgeInsets.only(left: 2, bottom: 8),
          child: Text(
            'SELECT TARGET ZONE',
            style: TextStyle(
              color: Colors.white38,
              fontSize: 11,
              fontWeight: FontWeight.w700,
              letterSpacing: 1.5,
            ),
          ),
        ),

        // ── Goal frame ────────────────────────────────────────────────────
        Container(
          decoration: BoxDecoration(
            border: Border.all(color: Colors.white.withOpacity(0.4), width: 2),
            borderRadius: BorderRadius.circular(4),
          ),
          child: ClipRRect(
            borderRadius: BorderRadius.circular(2),
            child: GridView.count(
              crossAxisCount: 4,
              shrinkWrap: true,
              physics: const NeverScrollableScrollPhysics(),
              mainAxisSpacing: 2,
              crossAxisSpacing: 2,
              padding: const EdgeInsets.all(2),
              childAspectRatio: 1.4,
              children: _zones.map((zone) {
                final isSelected = selectedZone == zone.id;
                return _ZoneCell(
                  zone: zone,
                  isSelected: isSelected,
                  onTap: () => onZoneSelected(zone.id),
                );
              }).toList(),
            ),
          ),
        ),

        if (selectedZone != null) ...[
          const SizedBox(height: 10),
          _SelectedZoneInfo(
            zone: _zones.firstWhere((z) => z.id == selectedZone),
          ),
        ],
      ],
    );
  }
}

class _ZoneCell extends StatelessWidget {
  const _ZoneCell({
    required this.zone,
    required this.isSelected,
    required this.onTap,
  });

  final _ZoneData zone;
  final bool isSelected;
  final VoidCallback onTap;

  @override
  Widget build(BuildContext context) {
    return GestureDetector(
      onTap: onTap,
      child: AnimatedContainer(
        duration: const Duration(milliseconds: 200),
        decoration: BoxDecoration(
          color: isSelected
              ? zone.difficultyColor.withOpacity(0.35)
              : Colors.white.withOpacity(0.04),
          borderRadius: BorderRadius.circular(4),
          border: Border.all(
            color: isSelected
                ? zone.difficultyColor
                : Colors.white.withOpacity(0.1),
            width: isSelected ? 2.0 : 1.0,
          ),
        ),
        child: Stack(
          children: [
            // Zone ID
            Center(
              child: Text(
                zone.id,
                style: TextStyle(
                  color: isSelected
                      ? zone.difficultyColor
                      : Colors.white.withOpacity(0.5),
                  fontSize: 15,
                  fontWeight: isSelected
                      ? FontWeight.w800
                      : FontWeight.w500,
                ),
              ),
            ),
            // Selected checkmark
            if (isSelected)
              Positioned(
                top: 4,
                right: 4,
                child: Icon(
                  Icons.check_circle,
                  color: zone.difficultyColor,
                  size: 12,
                ),
              ),
          ],
        ),
      ),
    );
  }
}

class _SelectedZoneInfo extends StatelessWidget {
  const _SelectedZoneInfo({required this.zone});

  final _ZoneData zone;

  @override
  Widget build(BuildContext context) {
    return Row(
      children: [
        Icon(Icons.sports_soccer,
            color: zone.difficultyColor, size: 16),
        const SizedBox(width: 8),
        Text(
          'Zone ${zone.id} selected — ${zone.label.replaceAll('\n', ' ')}',
          style: TextStyle(
            color: zone.difficultyColor,
            fontSize: 12,
            fontWeight: FontWeight.w600,
          ),
        ),
        const Spacer(),
        Container(
          padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 2),
          decoration: BoxDecoration(
            color: zone.difficultyColor.withOpacity(0.15),
            borderRadius: BorderRadius.circular(4),
          ),
          child: Text(
            zone.difficulty,
            style: TextStyle(
              color: zone.difficultyColor,
              fontSize: 9,
              fontWeight: FontWeight.w700,
              letterSpacing: 0.8,
            ),
          ),
        ),
      ],
    );
  }
}

class _ZoneData {
  const _ZoneData(
      this.id, this.label, this.difficulty, this.difficultyColor);

  final String id;
  final String label;
  final String difficulty;
  final Color difficultyColor;
}