import 'package:flutter/material.dart';
import 'package:google_fonts/google_fonts.dart';

/// PenaltyIQ Design System — derived from Stitch "Performance Lab" UI.
///
/// Color palette: dark background, lime primary (#C3F400), orange secondary,
/// cyan tertiary. Fonts: Space Grotesk (headings), Lexend (body).
abstract final class PiqColors {
  // ── Background / Surface ───────────────────────────────────────────────────
  static const background         = Color(0xFF131313);
  static const surface            = Color(0xFF131313);
  static const surfaceContainer   = Color(0xFF201F1F);
  static const surfaceContainerHigh = Color(0xFF2A2A2A);
  static const surfaceContainerHighest = Color(0xFF353534);
  static const surfaceVariant     = Color(0xFF353534);

  // ── Primary — lime ─────────────────────────────────────────────────────────
  static const primary            = Color(0xFFC3F400);
  static const primaryDim         = Color(0xFFABD600);
  static const onPrimary          = Color(0xFF283500);

  // ── Secondary — orange ──────────────────────────────────────────────────────
  static const secondary          = Color(0xFFFF5E07);
  static const onSecondary        = Color(0xFF5A1B00);

  // ── Tertiary — cyan ────────────────────────────────────────────────────────
  static const tertiary           = Color(0xFF7DF4FF);

  // ── Error ──────────────────────────────────────────────────────────────────
  static const error              = Color(0xFFFFB4AB);
  static const errorContainer     = Color(0xFF93000A);

  // ── Text ───────────────────────────────────────────────────────────────────
  static const onSurface          = Color(0xFFE5E2E1);
  static const onSurfaceVariant   = Color(0xFFC4C9AC);
  static const outline            = Color(0xFF8E9379);
  static const outlineVariant     = Color(0xFF444933);

  // ── Semantic shortcuts ─────────────────────────────────────────────────────
  static const lime = primary;
  static const orange = secondary;
  static const cyan = tertiary;
  static const dimText = onSurfaceVariant;
}

/// Text styles matching Stitch design.
/// Space Grotesk = headings, Lexend = body.
abstract final class PiqTextStyles {
  static TextStyle get displayXl => GoogleFonts.spaceGrotesk(
    fontSize: 48, fontWeight: FontWeight.w700, height: 1.1,
    letterSpacing: -0.96, color: PiqColors.onSurface);

  static TextStyle get headlineLg => GoogleFonts.spaceGrotesk(
    fontSize: 32, fontWeight: FontWeight.w600, height: 1.2,
    color: PiqColors.onSurface);

  static TextStyle get headlineMd => GoogleFonts.spaceGrotesk(
    fontSize: 24, fontWeight: FontWeight.w600, height: 1.2,
    color: PiqColors.onSurface);

  static TextStyle get metricHuge => GoogleFonts.spaceGrotesk(
    fontSize: 64, fontWeight: FontWeight.w700, height: 1.0,
    letterSpacing: -2.56, color: PiqColors.primary);

  static TextStyle get labelCaps => GoogleFonts.lexend(
    fontSize: 12, fontWeight: FontWeight.w700, height: 1.0,
    letterSpacing: 1.2, color: PiqColors.onSurfaceVariant);

  static TextStyle get bodyLg => GoogleFonts.lexend(
    fontSize: 18, fontWeight: FontWeight.w400, height: 1.5,
    color: PiqColors.onSurface);

  static TextStyle get bodyMd => GoogleFonts.lexend(
    fontSize: 16, fontWeight: FontWeight.w400, height: 1.5,
    color: PiqColors.onSurface);
}

/// Border radius constants (from Stitch design system).
abstract final class PiqRadius {
  static const sm  = 4.0;
  static const md  = 8.0;
  static const lg  = 12.0;
  static const xl  = 16.0;
  static const xxl = 24.0;

  static const borderSm  = BorderRadius.all(Radius.circular(sm));
  static const borderMd  = BorderRadius.all(Radius.circular(md));
  static const borderLg  = BorderRadius.all(Radius.circular(lg));
  static const borderXl  = BorderRadius.all(Radius.circular(xl));
  static const borderXxl = BorderRadius.all(Radius.circular(xxl));
}

/// MaterialApp theme built from PiqColors.
final class PiqTheme {
  static ThemeData get dark {
    return ThemeData(
      useMaterial3: true,
      brightness: Brightness.dark,
      scaffoldBackgroundColor: PiqColors.background,
      textTheme: GoogleFonts.lexendTextTheme(
        ThemeData.dark().textTheme,
      ),
      colorScheme: const ColorScheme.dark(
        surface:          PiqColors.surface,
        primary:          PiqColors.primary,
        onPrimary:        PiqColors.onPrimary,
        secondary:        PiqColors.secondary,
        onSecondary:      PiqColors.onSecondary,
        tertiary:         PiqColors.tertiary,
        error:            PiqColors.error,
        errorContainer:   PiqColors.errorContainer,
        onSurface:        PiqColors.onSurface,
        onSurfaceVariant: PiqColors.onSurfaceVariant,
        outline:          PiqColors.outline,
        outlineVariant:   PiqColors.outlineVariant,
      ),
      appBarTheme: AppBarTheme(
        backgroundColor: Colors.black,
        foregroundColor: PiqColors.primary,
        elevation: 0,
        centerTitle: false,
        titleTextStyle: GoogleFonts.spaceGrotesk(
          fontSize: 20,
          fontWeight: FontWeight.w900,
          color: PiqColors.primary,
          fontStyle: FontStyle.italic,
          letterSpacing: -0.5,
        ),
      ),
      cardTheme: CardThemeData(
        color: PiqColors.surfaceContainer,
        elevation: 0,
        shape: RoundedRectangleBorder(
          borderRadius: PiqRadius.borderXl,
          side: const BorderSide(color: PiqColors.outlineVariant),
        ),
        margin: EdgeInsets.zero,
      ),
      elevatedButtonTheme: ElevatedButtonThemeData(
        style: ElevatedButton.styleFrom(
          backgroundColor: PiqColors.primary,
          foregroundColor: PiqColors.onPrimary,
          textStyle: GoogleFonts.spaceGrotesk(
            fontWeight: FontWeight.w700,
            letterSpacing: 1.2,
          ),
          shape: const RoundedRectangleBorder(borderRadius: PiqRadius.borderLg),
          minimumSize: const Size.fromHeight(52),
        ),
      ),
      outlinedButtonTheme: OutlinedButtonThemeData(
        style: OutlinedButton.styleFrom(
          foregroundColor: PiqColors.onSurface,
          side: const BorderSide(color: PiqColors.outlineVariant),
          shape: const RoundedRectangleBorder(borderRadius: PiqRadius.borderLg),
          minimumSize: const Size.fromHeight(52),
          textStyle: GoogleFonts.spaceGrotesk(
            fontWeight: FontWeight.w700,
            letterSpacing: 1.2,
          ),
        ),
      ),
      navigationBarTheme: NavigationBarThemeData(
        backgroundColor: const Color(0xFF121212),
        indicatorColor: PiqColors.primary,
        labelTextStyle: WidgetStateProperty.all(
          GoogleFonts.spaceGrotesk(
            fontSize: 10,
            fontWeight: FontWeight.w700,
            letterSpacing: 1.5,
          ),
        ),
      ),
      dividerTheme: const DividerThemeData(
        color: PiqColors.outlineVariant,
        thickness: 1,
      ),
    );
  }
}