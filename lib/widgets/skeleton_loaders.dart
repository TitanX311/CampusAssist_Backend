// lib/widgets/skeleton_loaders.dart
import 'package:flutter/material.dart';
import '../theme/app_theme.dart';

// ── Shimmer effect ────────────────────────────────────────────────────────────

/// Wraps a child in a repeating shimmer animation.
class Shimmer extends StatefulWidget {
  final Widget child;
  const Shimmer({super.key, required this.child});

  @override
  State<Shimmer> createState() => _ShimmerState();
}

class _ShimmerState extends State<Shimmer> with SingleTickerProviderStateMixin {
  late final AnimationController _ctrl;

  @override
  void initState() {
    super.initState();
    _ctrl = AnimationController(
      vsync: this,
      duration: const Duration(milliseconds: 1500),
    )..repeat();
  }

  @override
  void dispose() {
    _ctrl.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return AnimatedBuilder(
      animation: _ctrl,
      builder: (context, child) {
        return ShaderMask(
          shaderCallback: (bounds) {
            return LinearGradient(
              begin: Alignment.centerLeft,
              end: Alignment.centerRight,
              colors: const [
                AppTheme.secondarySurface,
                AppTheme.elevatedSurface,
                AppTheme.secondarySurface,
              ],
              stops: [_ctrl.value - 0.3, _ctrl.value, _ctrl.value + 0.3],
              tileMode: TileMode.clamp,
            ).createShader(bounds);
          },
          blendMode: BlendMode.srcATop,
          child: child,
        );
      },
      child: widget.child,
    );
  }
}

/// A rounded placeholder rectangle used inside skeleton loaders.
class _Bone extends StatelessWidget {
  final double width;
  final double height;
  final double radius;

  const _Bone({required this.width, required this.height, this.radius = 6});

  @override
  Widget build(BuildContext context) {
    return Container(
      width: width,
      height: height,
      decoration: BoxDecoration(
        color: AppTheme.divider,
        borderRadius: BorderRadius.circular(radius),
      ),
    );
  }
}

// ── Skeleton Post Card (for home feed loading) ────────────────────────────────

class SkeletonPostCard extends StatelessWidget {
  const SkeletonPostCard({super.key});

  @override
  Widget build(BuildContext context) {
    return Shimmer(
      child: Container(
        margin: const EdgeInsets.symmetric(horizontal: 16, vertical: 6),
        padding: const EdgeInsets.all(14),
        decoration: BoxDecoration(
          color: AppTheme.cardBg,
          borderRadius: BorderRadius.circular(16),
          border: Border.all(color: AppTheme.divider),
        ),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            // Avatar + name + time
            Row(
              children: [
                const _Bone(width: 32, height: 32, radius: 16),
                const SizedBox(width: 10),
                Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: const [
                    _Bone(width: 100, height: 12),
                    SizedBox(height: 6),
                    _Bone(width: 60, height: 10),
                  ],
                ),
              ],
            ),
            const SizedBox(height: 14),
            // Content lines
            const _Bone(width: double.infinity, height: 12),
            const SizedBox(height: 8),
            const _Bone(width: double.infinity, height: 12),
            const SizedBox(height: 8),
            const _Bone(width: 200, height: 12),
            const SizedBox(height: 16),
            // Footer
            Row(
              children: const [
                _Bone(width: 40, height: 14),
                SizedBox(width: 20),
                _Bone(width: 40, height: 14),
                Spacer(),
                _Bone(width: 60, height: 28, radius: 14),
              ],
            ),
          ],
        ),
      ),
    );
  }
}

/// A list of skeleton post cards for feed loading state.
class SkeletonPostList extends StatelessWidget {
  final int count;
  const SkeletonPostList({super.key, this.count = 4});

  @override
  Widget build(BuildContext context) {
    return ListView.builder(
      padding: const EdgeInsets.only(top: 4, bottom: 100),
      physics: const NeverScrollableScrollPhysics(),
      itemCount: count,
      itemBuilder: (_, __) => const SkeletonPostCard(),
    );
  }
}

// ── Skeleton Comment Card (for post detail loading) ───────────────────────────

class SkeletonCommentCard extends StatelessWidget {
  const SkeletonCommentCard({super.key});

  @override
  Widget build(BuildContext context) {
    return Shimmer(
      child: Container(
        margin: const EdgeInsets.only(bottom: 10),
        padding: const EdgeInsets.all(14),
        decoration: BoxDecoration(
          color: AppTheme.cardBg,
          borderRadius: BorderRadius.circular(14),
          border: Border.all(color: AppTheme.divider),
        ),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            // Content lines
            const _Bone(width: double.infinity, height: 11),
            const SizedBox(height: 7),
            const _Bone(width: double.infinity, height: 11),
            const SizedBox(height: 7),
            const _Bone(width: 140, height: 11),
            const SizedBox(height: 12),
            // Author row
            Row(
              children: const [
                _Bone(width: 14, height: 14, radius: 7),
                SizedBox(width: 6),
                _Bone(width: 80, height: 10),
                SizedBox(width: 8),
                _Bone(width: 50, height: 10),
              ],
            ),
          ],
        ),
      ),
    );
  }
}

/// A column of skeleton comment cards for the answers loading state.
class SkeletonCommentList extends StatelessWidget {
  final int count;
  const SkeletonCommentList({super.key, this.count = 3});

  @override
  Widget build(BuildContext context) {
    return Column(
      children: List.generate(count, (_) => const SkeletonCommentCard()),
    );
  }
}
