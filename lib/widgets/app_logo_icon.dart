import 'package:flutter/material.dart';
import '../theme/app_theme.dart';

/// AppLogoIcon
///
/// Reusable gradient logo widget used across the app.
///
/// Usage patterns:
///
/// Presets (recommended for consistency):
/// ```dart
/// const AppLogoIcon.large();   // Auth screen, splash screen
/// const AppLogoIcon.medium();  // AppBar, section headers
/// const AppLogoIcon.small();   // List items, compact UI
/// ```
///
/// Custom sizes (when needed):
/// ```dart
/// const AppLogoIcon(
///   size: 60,
///   iconSize: 30,
///   borderRadius: 18,
///   showShadow: true,
/// );
/// ```
///
/// Custom icon example:
/// ```dart
/// const AppLogoIcon(
///   size: 40,
///   iconSize: 20,
///   borderRadius: 12,
///   icon: Icons.event,
/// );
/// ```

class AppLogoIcon extends StatelessWidget {
  final double size;
  final double iconSize;
  final double borderRadius;
  final bool showShadow;
  final IconData icon;

  const AppLogoIcon({
    super.key,
    required this.size,
    required this.iconSize,
    required this.borderRadius,
    this.showShadow = false,
    this.icon = Icons.school_rounded,
  });

  /// Large logo (login / splash)
  const AppLogoIcon.large({super.key})
    : size = 76,
      iconSize = 38,
      borderRadius = 22,
      showShadow = true,
      icon = Icons.school_rounded;

  /// Medium logo (app bar / section headers)
  const AppLogoIcon.medium({super.key})
    : size = 48,
      iconSize = 24,
      borderRadius = 14,
      showShadow = false,
      icon = Icons.school_rounded;

  /// Small logo (compact UI)
  const AppLogoIcon.small({super.key})
    : size = 34,
      iconSize = 18,
      borderRadius = 10,
      showShadow = false,
      icon = Icons.school_rounded;

  @override
  Widget build(BuildContext context) {
    return Container(
      width: size,
      height: size,
      decoration: BoxDecoration(
        gradient: const LinearGradient(
          colors: [AppTheme.primary, AppTheme.primaryLight],
          begin: Alignment.topLeft,
          end: Alignment.bottomRight,
        ),
        borderRadius: BorderRadius.circular(borderRadius),
        boxShadow: showShadow
            ? [
                BoxShadow(
                  color: AppTheme.primary.withOpacity(0.38),
                  blurRadius: 20,
                  offset: const Offset(0, 8),
                ),
              ]
            : null,
      ),
      child: Icon(icon, color: Colors.white, size: iconSize),
    );
  }
}
