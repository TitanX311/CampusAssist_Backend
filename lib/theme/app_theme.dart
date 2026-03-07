import 'package:flutter/material.dart';
import 'package:google_fonts/google_fonts.dart';

class AppTheme {
  // ── Core Brand Palette ──────────────────────────────────────────────────────
  static const Color primary = Color(0xFF3A7BD5); // Calm Trust Blue
  static const Color primaryLight = Color(
    0xFF7AA7E6,
  ); // Light Blue (avatars, highlights)
  static const Color primaryHover = Color(0xFF2F65B4); // Deeper Blue
  static const Color primaryActive = Color(0xFF244F8F); // Strong Blue
  static const Color secondary = Color(0xFF6BCB77); // Community Green
  static const Color secondaryHover = Color(0xFF54B864); // Deeper Green
  static const Color accent = Color(0xFFFFB84C); // Friendly Orange
  static const Color accentHover = Color(0xFFF5A623); // Warm Orange

  // ── Background System ───────────────────────────────────────────────────────
  static const Color surface = Color(
    0xFFF6F8FB,
  ); // App Background (Soft Blue Gray)
  static const Color cardBg = Color(0xFFFFFFFF); // Surface / Cards
  static const Color secondarySurface = Color(0xFFF1F3F7); // Secondary Surface
  static const Color elevatedSurface = Color(0xFFFCFDFF); // Elevated Surface
  static const Color divider = Color(0xFFE5E7EB); // Neutral Gray

  // ── Text Colors ─────────────────────────────────────────────────────────────
  static const Color textPrimary = Color(0xFF2D3748); // Titles, main content
  static const Color textSecondary = Color(0xFF6B7280); // Descriptions
  static const Color textLight = Color(0xFFB0B7C3); // Timestamps, hints
  static const Color textMuted = Color(0xFF9CA3AF); // Metadata
  static const Color textOnPrimary = Color(0xFFFFFFFF); // Buttons
  static const Color textOnAccent = Color(0xFF1F2937); // Badges

  // ── Status Colors ───────────────────────────────────────────────────────────
  static const Color success = Color(0xFF4CAF50);
  static const Color warning = Color(0xFFF59E0B);
  static const Color error = Color(0xFFEF4444);
  static const Color info = Color(0xFF38BDF8);

  // ── Interactive Elements ────────────────────────────────────────────────────
  static const Color buttonDisabled = Color(0xFFA0AEC0);
  static const Color focusRing = Color(0xFF7AA7E6);
  static const Color link = Color(0xFF3A7BD5);
  static const Color linkHover = Color(0xFF2F65B4);

  // ── Community & Social UI ───────────────────────────────────────────────────
  static const Color memberBadge = Color(0xFF6BCB77);
  static const Color notificationBadge = Color(0xFFFFB84C);
  static const Color onlineStatus = Color(0xFF22C55E);
  static const Color mentionHighlight = Color(0xFFFFE6B3);

  // ── Input Fields ────────────────────────────────────────────────────────────
  static const Color inputBorder = Color(0xFFD1D5DB);
  static const Color inputFocusBorder = Color(0xFF3A7BD5);
  static const Color inputErrorBorder = Color(0xFFEF4444);

  // ── Category Colors ─────────────────────────────────────────────────────────
  static const Color academics = Color(0xFF3A7BD5); // Primary Blue
  static const Color hostel = Color(0xFF6BCB77); // Community Green
  static const Color facilities = Color(0xFF4CAF50); // Success Green
  static const Color food = Color(0xFFFFB84C); // Friendly Orange
  static const Color career = Color(0xFF8B5CF6); // Purple (kept distinct)
  static const Color events = Color(0xFFF59E0B); // Amber
  static const Color general = Color(0xFF6B7280); // Muted Gray

  // ── Dark Mode Colors ────────────────────────────────────────────────────────
  static const Color darkBackground = Color(0xFF0F172A);
  static const Color darkSurface = Color(0xFF1E293B);
  static const Color darkCard = Color(0xFF273449);
  static const Color darkPrimary = Color(0xFF60A5FA);
  static const Color darkSecondary = Color(0xFF86EFAC);
  static const Color darkAccent = Color(0xFFFBBF24);
  static const Color darkTextPrimary = Color(0xFFF1F5F9);
  static const Color darkTextSecondary = Color(0xFF94A3B8);

  // ── Light Theme ─────────────────────────────────────────────────────────────
  static ThemeData get lightTheme {
    return ThemeData(
      useMaterial3: true,
      colorScheme: ColorScheme.fromSeed(
        seedColor: primary,
        brightness: Brightness.light,
        surface: surface,
        primary: primary,
        secondary: secondary,
        tertiary: accent,
        onPrimary: textOnPrimary,
        error: error,
      ),
      scaffoldBackgroundColor: surface,
      textTheme: GoogleFonts.poppinsTextTheme().copyWith(
        headlineLarge: GoogleFonts.poppins(
          fontSize: 28,
          fontWeight: FontWeight.w700,
          color: textPrimary,
        ),
        headlineMedium: GoogleFonts.poppins(
          fontSize: 22,
          fontWeight: FontWeight.w700,
          color: textPrimary,
        ),
        titleLarge: GoogleFonts.poppins(
          fontSize: 18,
          fontWeight: FontWeight.w600,
          color: textPrimary,
        ),
        titleMedium: GoogleFonts.poppins(
          fontSize: 15,
          fontWeight: FontWeight.w600,
          color: textPrimary,
        ),
        bodyLarge: GoogleFonts.poppins(
          fontSize: 14,
          fontWeight: FontWeight.w400,
          color: textPrimary,
        ),
        bodyMedium: GoogleFonts.poppins(
          fontSize: 13,
          fontWeight: FontWeight.w400,
          color: textSecondary,
        ),
        bodySmall: GoogleFonts.poppins(
          fontSize: 11,
          fontWeight: FontWeight.w400,
          color: textMuted,
        ),
      ),
      appBarTheme: AppBarTheme(
        elevation: 0,
        backgroundColor: cardBg,
        foregroundColor: textPrimary,
        titleTextStyle: GoogleFonts.poppins(
          fontSize: 18,
          fontWeight: FontWeight.w700,
          color: textPrimary,
        ),
      ),
      cardTheme: CardThemeData(
        elevation: 0,
        color: cardBg,
        shape: RoundedRectangleBorder(
          borderRadius: BorderRadius.circular(16),
          side: const BorderSide(color: divider, width: 1),
        ),
      ),
      elevatedButtonTheme: ElevatedButtonThemeData(
        style: ElevatedButton.styleFrom(
          backgroundColor: primary,
          foregroundColor: textOnPrimary,
          disabledBackgroundColor: buttonDisabled,
          elevation: 0,
          shape: RoundedRectangleBorder(
            borderRadius: BorderRadius.circular(12),
          ),
          padding: const EdgeInsets.symmetric(horizontal: 24, vertical: 14),
          textStyle: GoogleFonts.poppins(
            fontSize: 14,
            fontWeight: FontWeight.w600,
          ),
        ),
      ),
      inputDecorationTheme: InputDecorationTheme(
        filled: true,
        fillColor: cardBg,
        border: OutlineInputBorder(
          borderRadius: BorderRadius.circular(12),
          borderSide: const BorderSide(color: inputBorder),
        ),
        enabledBorder: OutlineInputBorder(
          borderRadius: BorderRadius.circular(12),
          borderSide: const BorderSide(color: inputBorder),
        ),
        focusedBorder: OutlineInputBorder(
          borderRadius: BorderRadius.circular(12),
          borderSide: const BorderSide(color: inputFocusBorder, width: 2),
        ),
        errorBorder: OutlineInputBorder(
          borderRadius: BorderRadius.circular(12),
          borderSide: const BorderSide(color: inputErrorBorder),
        ),
        focusedErrorBorder: OutlineInputBorder(
          borderRadius: BorderRadius.circular(12),
          borderSide: const BorderSide(color: inputErrorBorder, width: 2),
        ),
        contentPadding: const EdgeInsets.symmetric(
          horizontal: 16,
          vertical: 14,
        ),
        hintStyle: GoogleFonts.poppins(color: textMuted, fontSize: 13),
      ),
      bottomNavigationBarTheme: const BottomNavigationBarThemeData(
        backgroundColor: cardBg,
        selectedItemColor: primary,
        unselectedItemColor: textMuted,
        elevation: 8,
        type: BottomNavigationBarType.fixed,
      ),
      tabBarTheme: TabBarThemeData(
        labelColor: primary,
        unselectedLabelColor: textSecondary,
        indicatorColor: primary,
        labelStyle: GoogleFonts.poppins(
          fontSize: 13,
          fontWeight: FontWeight.w600,
        ),
        unselectedLabelStyle: GoogleFonts.poppins(
          fontSize: 13,
          fontWeight: FontWeight.w500,
        ),
      ),
      chipTheme: ChipThemeData(
        backgroundColor: secondarySurface,
        selectedColor: primary.withOpacity(0.15),
        labelStyle: GoogleFonts.poppins(
          fontSize: 12,
          fontWeight: FontWeight.w500,
        ),
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(20)),
        side: const BorderSide(color: divider),
      ),
      dividerTheme: const DividerThemeData(color: divider, thickness: 1),
      focusColor: focusRing.withOpacity(0.3),
    );
  }

  // ── Dark Theme ───────────────────────────────────────────────────────────────
  static ThemeData get darkTheme {
    return ThemeData(
      useMaterial3: true,
      colorScheme: ColorScheme.fromSeed(
        seedColor: darkPrimary,
        brightness: Brightness.dark,
        surface: darkSurface,
        primary: darkPrimary,
        secondary: darkSecondary,
        tertiary: darkAccent,
        onPrimary: darkBackground,
        error: error,
      ),
      scaffoldBackgroundColor: darkBackground,
      textTheme: GoogleFonts.poppinsTextTheme().copyWith(
        headlineLarge: GoogleFonts.poppins(
          fontSize: 28,
          fontWeight: FontWeight.w700,
          color: darkTextPrimary,
        ),
        headlineMedium: GoogleFonts.poppins(
          fontSize: 22,
          fontWeight: FontWeight.w700,
          color: darkTextPrimary,
        ),
        titleLarge: GoogleFonts.poppins(
          fontSize: 18,
          fontWeight: FontWeight.w600,
          color: darkTextPrimary,
        ),
        titleMedium: GoogleFonts.poppins(
          fontSize: 15,
          fontWeight: FontWeight.w600,
          color: darkTextPrimary,
        ),
        bodyLarge: GoogleFonts.poppins(
          fontSize: 14,
          fontWeight: FontWeight.w400,
          color: darkTextPrimary,
        ),
        bodyMedium: GoogleFonts.poppins(
          fontSize: 13,
          fontWeight: FontWeight.w400,
          color: darkTextSecondary,
        ),
        bodySmall: GoogleFonts.poppins(
          fontSize: 11,
          fontWeight: FontWeight.w400,
          color: darkTextSecondary,
        ),
      ),
      appBarTheme: AppBarTheme(
        elevation: 0,
        backgroundColor: darkSurface,
        foregroundColor: darkTextPrimary,
        titleTextStyle: GoogleFonts.poppins(
          fontSize: 18,
          fontWeight: FontWeight.w700,
          color: darkTextPrimary,
        ),
      ),
      cardTheme: CardThemeData(
        elevation: 0,
        color: darkCard,
        shape: RoundedRectangleBorder(
          borderRadius: BorderRadius.circular(16),
          side: BorderSide(color: Colors.white.withOpacity(0.08), width: 1),
        ),
      ),
      elevatedButtonTheme: ElevatedButtonThemeData(
        style: ElevatedButton.styleFrom(
          backgroundColor: darkPrimary,
          foregroundColor: darkBackground,
          disabledBackgroundColor: buttonDisabled,
          elevation: 0,
          shape: RoundedRectangleBorder(
            borderRadius: BorderRadius.circular(12),
          ),
          padding: const EdgeInsets.symmetric(horizontal: 24, vertical: 14),
          textStyle: GoogleFonts.poppins(
            fontSize: 14,
            fontWeight: FontWeight.w600,
          ),
        ),
      ),
      inputDecorationTheme: InputDecorationTheme(
        filled: true,
        fillColor: darkCard,
        border: OutlineInputBorder(
          borderRadius: BorderRadius.circular(12),
          borderSide: BorderSide(color: Colors.white.withOpacity(0.12)),
        ),
        enabledBorder: OutlineInputBorder(
          borderRadius: BorderRadius.circular(12),
          borderSide: BorderSide(color: Colors.white.withOpacity(0.12)),
        ),
        focusedBorder: OutlineInputBorder(
          borderRadius: BorderRadius.circular(12),
          borderSide: const BorderSide(color: darkPrimary, width: 2),
        ),
        contentPadding: const EdgeInsets.symmetric(
          horizontal: 16,
          vertical: 14,
        ),
        hintStyle: GoogleFonts.poppins(color: darkTextSecondary, fontSize: 13),
      ),
      bottomNavigationBarTheme: BottomNavigationBarThemeData(
        backgroundColor: darkSurface,
        selectedItemColor: darkPrimary,
        unselectedItemColor: darkTextSecondary,
        elevation: 8,
        type: BottomNavigationBarType.fixed,
      ),
      tabBarTheme: TabBarThemeData(
        labelColor: darkPrimary,
        unselectedLabelColor: darkTextSecondary,
        indicatorColor: darkPrimary,
        labelStyle: GoogleFonts.poppins(
          fontSize: 13,
          fontWeight: FontWeight.w600,
        ),
        unselectedLabelStyle: GoogleFonts.poppins(
          fontSize: 13,
          fontWeight: FontWeight.w500,
        ),
      ),
      chipTheme: ChipThemeData(
        backgroundColor: darkCard,
        selectedColor: darkPrimary.withOpacity(0.2),
        labelStyle: GoogleFonts.poppins(
          fontSize: 12,
          fontWeight: FontWeight.w500,
          color: darkTextPrimary,
        ),
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(20)),
        side: BorderSide(color: Colors.white.withOpacity(0.08)),
      ),
    );
  }

  // ── Helpers ──────────────────────────────────────────────────────────────────
  static Color categoryColor(String category) {
    switch (category.toLowerCase()) {
      case 'academics':
        return academics;
      case 'hostel':
        return hostel;
      case 'facilities':
        return facilities;
      case 'food':
        return food;
      case 'career':
        return career;
      case 'events':
        return events;
      default:
        return general;
    }
  }

  static IconData categoryIcon(String category) {
    switch (category.toLowerCase()) {
      case 'academics':
        return Icons.school_rounded;
      case 'hostel':
        return Icons.hotel_rounded;
      case 'facilities':
        return Icons.business_rounded;
      case 'food':
        return Icons.restaurant_rounded;
      case 'career':
        return Icons.work_rounded;
      case 'events':
        return Icons.event_rounded;
      default:
        return Icons.forum_rounded;
    }
  }
}
