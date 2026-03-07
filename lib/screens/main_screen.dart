// lib/screens/main_screen.dart
import 'dart:ui';

import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../models/community_model.dart';
import '../theme/app_theme.dart';
import '../viewmodel/community_viewmodel.dart';
import 'home_screen.dart';
import 'communities_screen.dart';
import 'create_post_screen.dart';
import 'profile_screen.dart';

class MainScreen extends StatefulWidget {
  const MainScreen({super.key});

  @override
  State<MainScreen> createState() => _MainScreenState();
}

class _MainScreenState extends State<MainScreen> {
  int _index = 0;

  final _screens = const [HomeScreen(), CommunitiesScreen(), ProfileScreen()];

  void _openCreatePost({String? communityId, String? communityName}) {
    Navigator.push(
      context,
      MaterialPageRoute(
        builder: (_) => CreatePostScreen(
          communityId: communityId,
          communityName: communityName,
        ),
      ),
    ).then((v) {
      if (v == true) setState(() {});
    });
  }

  Future<void> _onAskTap() async {
    // Show a community picker bottom sheet so the user can select
    // which community they want to post in.
    final picked = await showModalBottomSheet<Community>(
      context: context,
      isScrollControlled: true,
      backgroundColor: Colors.transparent,
      builder: (_) => const _CommunityPickerSheet(),
    );
    if (picked != null && mounted) {
      _openCreatePost(communityId: picked.id, communityName: picked.name);
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      extendBody: true,
      body: Stack(
        children: [
          _screens[_index],
          Align(
            alignment: Alignment.bottomCenter,
            child: _FloatingNavBar(
              currentIndex: _index,
              onTap: (i) => setState(() => _index = i),
              onAskTap: _onAskTap,
            ),
          ),
        ],
      ),
    );
  }
}

class _FloatingNavBar extends StatefulWidget {
  final int currentIndex;
  final ValueChanged<int> onTap;
  final Future<void> Function() onAskTap;

  const _FloatingNavBar({
    required this.currentIndex,
    required this.onTap,
    required this.onAskTap,
  });

  @override
  State<_FloatingNavBar> createState() => _FloatingNavBarState();
}

class _FloatingNavBarState extends State<_FloatingNavBar>
    with SingleTickerProviderStateMixin {
  late AnimationController _askCtrl;
  late Animation<double> _askScale;

  @override
  void initState() {
    super.initState();
    _askCtrl = AnimationController(
      vsync: this,
      duration: const Duration(milliseconds: 140),
      lowerBound: 0.0,
      upperBound: 1.0,
      value: 1.0,
    );
    _askScale = CurvedAnimation(parent: _askCtrl, curve: Curves.easeInOut);
  }

  @override
  void dispose() {
    _askCtrl.dispose();
    super.dispose();
  }

  void _onAskTapDown(_) => _askCtrl.reverse();
  void _onAskTapUp(_) {
    _askCtrl.forward();
    widget.onAskTap();
  }

  void _onAskTapCancel() => _askCtrl.forward();

  @override
  Widget build(BuildContext context) {
    final bottomInset = MediaQuery.of(context).padding.bottom;

    return Padding(
      padding: EdgeInsets.fromLTRB(
        20,
        10,
        20,
        (bottomInset > 0 ? bottomInset : 16),
      ),
      child: Material(
        color: Colors.transparent, // Required to see the blur behind it
        elevation: 10, // Try values between 0 and 20
        borderRadius: const BorderRadius.all(Radius.circular(32)),
        shadowColor: Colors.black, // Controls the shadow color
        child: ClipRRect(
          borderRadius: const BorderRadius.all(Radius.circular(32)),
          child: BackdropFilter(
            filter: ImageFilter.blur(sigmaX: 20, sigmaY: 20),
            child: Container(
              height: 68,
              decoration: BoxDecoration(
                color: Colors.white.withOpacity(0.88),
                borderRadius: const BorderRadius.only(
                  topLeft: Radius.circular(32),
                  topRight: Radius.circular(32),
                ),
                border: Border.all(
                  color: Colors.white.withOpacity(0.6),
                  width: 1.2,
                ),
                boxShadow: [
                  BoxShadow(
                    color: AppTheme.primary.withOpacity(0.10),
                    blurRadius: 24,
                    offset: const Offset(0, 8),
                  ),
                  BoxShadow(
                    color: Colors.black.withOpacity(0.07),
                    blurRadius: 12,
                    offset: const Offset(0, 2),
                  ),
                ],
              ),
              child: Row(
                children: [
                  // Home tab
                  Expanded(
                    child: _NavTab(
                      icon: Icons.home_rounded,
                      label: 'Home',
                      selected: widget.currentIndex == 0,
                      onTap: () => widget.onTap(0),
                    ),
                  ),

                  // Communities tab
                  Expanded(
                    child: _NavTab(
                      icon: Icons.people_rounded,
                      label: 'Community',
                      selected: widget.currentIndex == 1,
                      onTap: () => widget.onTap(1),
                    ),
                  ),

                  // Ask (center pill button)
                  Padding(
                    padding: const EdgeInsets.symmetric(vertical: 10),
                    child: GestureDetector(
                      onTapDown: _onAskTapDown,
                      onTapUp: _onAskTapUp,
                      onTapCancel: _onAskTapCancel,
                      child: ScaleTransition(
                        scale: Tween<double>(
                          begin: 0.92,
                          end: 1.0,
                        ).animate(_askScale),
                        child: Container(
                          width: 80,
                          decoration: BoxDecoration(
                            gradient: const LinearGradient(
                              colors: [AppTheme.primary, AppTheme.primaryLight],
                              begin: Alignment.topLeft,
                              end: Alignment.bottomRight,
                            ),
                            borderRadius: BorderRadius.circular(22),
                            boxShadow: [
                              BoxShadow(
                                color: AppTheme.primary.withOpacity(0.4),
                                blurRadius: 12,
                                offset: const Offset(0, 4),
                              ),
                            ],
                          ),
                          child: const Column(
                            mainAxisAlignment: MainAxisAlignment.center,
                            children: [
                              Icon(
                                Icons.add_rounded,
                                color: Colors.white,
                                size: 22,
                              ),
                              SizedBox(height: 1),
                              Text(
                                'Ask',
                                style: TextStyle(
                                  color: Colors.white,
                                  fontSize: 11,
                                  fontWeight: FontWeight.w700,
                                  letterSpacing: 0.3,
                                ),
                              ),
                            ],
                          ),
                        ),
                      ),
                    ),
                  ),

                  // Profile tab
                  Expanded(
                    child: _NavTab(
                      icon: Icons.person_rounded,
                      label: 'Profile',
                      selected: widget.currentIndex == 2,
                      onTap: () => widget.onTap(2),
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

class _NavTab extends StatefulWidget {
  final IconData icon;
  final String label;
  final bool selected;
  final VoidCallback onTap;

  const _NavTab({
    required this.icon,
    required this.label,
    required this.selected,
    required this.onTap,
  });

  @override
  State<_NavTab> createState() => _NavTabState();
}

class _NavTabState extends State<_NavTab> with SingleTickerProviderStateMixin {
  late AnimationController _ctrl;
  late Animation<double> _scale;

  @override
  void initState() {
    super.initState();
    _ctrl = AnimationController(
      vsync: this,
      duration: const Duration(milliseconds: 180),
      value: widget.selected ? 1.0 : 0.0,
    );
    _scale = CurvedAnimation(parent: _ctrl, curve: Curves.easeOutBack);
  }

  @override
  void didUpdateWidget(_NavTab old) {
    super.didUpdateWidget(old);
    if (widget.selected != old.selected) {
      widget.selected ? _ctrl.forward() : _ctrl.reverse();
    }
  }

  @override
  void dispose() {
    _ctrl.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return GestureDetector(
      onTap: widget.onTap,
      behavior: HitTestBehavior.opaque,
      child: Column(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          AnimatedBuilder(
            animation: _scale,
            builder: (_, child) => Transform.scale(
              scale: 1.0 + (_scale.value * 0.12),
              child: child,
            ),
            child: Icon(
              widget.icon,
              size: 24,
              color: widget.selected ? AppTheme.primary : AppTheme.textLight,
            ),
          ),
          const SizedBox(height: 3),
          Text(
            widget.label,
            style: TextStyle(
              fontSize: 11,
              fontWeight: widget.selected ? FontWeight.w700 : FontWeight.w500,
              color: widget.selected ? AppTheme.primary : AppTheme.textLight,
            ),
          ),
          const SizedBox(height: 4),
          AnimatedContainer(
            duration: const Duration(milliseconds: 250),
            curve: Curves.easeOutCubic,
            width: widget.selected ? 18 : 0,
            height: 3,
            decoration: BoxDecoration(
              color: AppTheme.primary,
              borderRadius: BorderRadius.circular(2),
            ),
          ),
        ],
      ),
    );
  }
}

// ── Community Picker Sheet ────────────────────────────────────────────────────

class _CommunityPickerSheet extends ConsumerWidget {
  const _CommunityPickerSheet();

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final communitiesAsync = ref.watch(communityViewModelProvider);

    return Container(
      decoration: const BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.vertical(top: Radius.circular(24)),
      ),
      padding: EdgeInsets.fromLTRB(
        20,
        16,
        20,
        MediaQuery.of(context).viewInsets.bottom + 24,
      ),
      child: Column(
        mainAxisSize: MainAxisSize.min,
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          // Handle
          Center(
            child: Container(
              width: 40,
              height: 4,
              decoration: BoxDecoration(
                color: AppTheme.divider,
                borderRadius: BorderRadius.circular(2),
              ),
            ),
          ),
          const SizedBox(height: 16),
          const Text(
            'Post to a Community',
            style: TextStyle(
              fontSize: 16,
              fontWeight: FontWeight.w800,
              color: AppTheme.textPrimary,
            ),
          ),
          const SizedBox(height: 4),
          const Text(
            'Choose which community to post in',
            style: TextStyle(fontSize: 13, color: AppTheme.textSecondary),
          ),
          const SizedBox(height: 16),
          communitiesAsync.when(
            loading: () => const Padding(
              padding: EdgeInsets.all(24),
              child: Center(child: CircularProgressIndicator()),
            ),
            error: (e, _) => Padding(
              padding: const EdgeInsets.all(16),
              child: Text(
                'Could not load communities: $e',
                style: const TextStyle(color: AppTheme.textSecondary),
              ),
            ),
            data: (communities) {
              if (communities.isEmpty) {
                return const Padding(
                  padding: EdgeInsets.all(24),
                  child: Center(
                    child: Text(
                      'You haven\'t joined any communities yet.\nJoin one from the Community tab first.',
                      textAlign: TextAlign.center,
                      style: TextStyle(
                        color: AppTheme.textSecondary,
                        fontSize: 13,
                      ),
                    ),
                  ),
                );
              }
              return ListView.separated(
                shrinkWrap: true,
                physics: const NeverScrollableScrollPhysics(),
                itemCount: communities.length,
                separatorBuilder: (_, __) => const Divider(height: 1),
                itemBuilder: (_, i) {
                  final c = communities[i];
                  return ListTile(
                    contentPadding: EdgeInsets.zero,
                    leading: Container(
                      width: 40,
                      height: 40,
                      decoration: BoxDecoration(
                        color: AppTheme.primary.withOpacity(0.1),
                        borderRadius: BorderRadius.circular(10),
                      ),
                      child: const Icon(
                        Icons.people_rounded,
                        color: AppTheme.primary,
                        size: 20,
                      ),
                    ),
                    title: Text(
                      c.name,
                      style: const TextStyle(
                        fontSize: 14,
                        fontWeight: FontWeight.w600,
                        color: AppTheme.textPrimary,
                      ),
                    ),
                    subtitle: Text(
                      c.type == 'PUBLIC' ? 'Public' : 'Private',
                      style: const TextStyle(
                        fontSize: 12,
                        color: AppTheme.textSecondary,
                      ),
                    ),
                    trailing: const Icon(
                      Icons.chevron_right_rounded,
                      color: AppTheme.textLight,
                    ),
                    onTap: () => Navigator.pop(context, c),
                  );
                },
              );
            },
          ),
        ],
      ),
    );
  }
}
