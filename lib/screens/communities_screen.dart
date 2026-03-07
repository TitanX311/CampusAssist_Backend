// lib/screens/communities_screen.dart
// REBUILT CLEAN - all orphaned code removed
import 'package:campusassist/models/college_model.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import 'package:campusassist/core/providers.dart';
import '../models/community_model.dart';
import '../models/search_result_model.dart';
import '../theme/app_theme.dart';
import '../viewmodel/college_select_viewmodel.dart';
import '../viewmodel/community_viewmodel.dart';
import '../viewmodel/search_viewmodel.dart';
import 'college_detail_screen.dart';

class CommunitiesScreen extends ConsumerStatefulWidget {
  const CommunitiesScreen({super.key});

  @override
  ConsumerState<CommunitiesScreen> createState() => _CommunitiesScreenState();
}

class _CommunitiesScreenState extends ConsumerState<CommunitiesScreen> {
  void _openOptions() {
    _openBrowseSheet();
  }

  void _openBrowseSheet() {
    showModalBottomSheet(
      context: context,
      isScrollControlled: true,
      backgroundColor: Colors.transparent,
      builder: (_) => _BrowseSheet(
        onSelectCollege: (item) {
          Navigator.pop(context);
          Navigator.push(
            context,
            MaterialPageRoute(
              builder: (_) => CollegeDetailScreen(
                collegeId: item.id,
                collegeName: item.name,
              ),
            ),
          );
        },
        onCreateCommunity: () {
          Navigator.pop(context);
          _openCreateCommunitySheet();
        },
      ),
    );
  }

  void _openCreateCommunitySheet() async {
    final created = await showModalBottomSheet<bool>(
      context: context,
      isScrollControlled: true,
      backgroundColor: Colors.transparent,
      builder: (_) => const _CreateCommunitySheet(),
    );
    if (created == true && mounted) {
      ScaffoldMessenger.of(
        context,
      ).showSnackBar(const SnackBar(content: Text('Community created!')));
    }
  }

  void _openCollegePicker() async {
    final picked = await showModalBottomSheet<CollegeModel>(
      context: context,
      isScrollControlled: true,
      backgroundColor: Colors.transparent,
      builder: (_) => const _CollegePickerSheet(),
    );
    if (picked != null) {
      ref.read(selectedCollegeProvider.notifier).state = picked;
    }
  }

  void _leaveCollege() {
    showDialog(
      context: context,
      builder: (ctx) => AlertDialog(
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(20)),
        title: const Text('Leave College?'),
        content: const Text(
          'You will no longer see posts from your college feed.',
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(ctx),
            child: const Text('Cancel'),
          ),
          TextButton(
            onPressed: () {
              ref.read(selectedCollegeProvider.notifier).state = null;
              Navigator.pop(ctx);
            },
            child: const Text('Leave', style: TextStyle(color: Colors.red)),
          ),
        ],
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    final college = ref.watch(selectedCollegeProvider);
    final hasCollege = college != null && college.id.isNotEmpty;
    final communitiesAsync = ref.watch(communityViewModelProvider);

    return Scaffold(
      backgroundColor: AppTheme.surface,
      appBar: AppBar(
        backgroundColor: Colors.white,
        elevation: 0,
        title: const Text(
          'Communities',
          style: TextStyle(
            fontSize: 17,
            fontWeight: FontWeight.w800,
            color: AppTheme.textPrimary,
          ),
        ),
        actions: [
          Padding(
            padding: const EdgeInsets.only(right: 8),
            child: TextButton.icon(
              onPressed: _openOptions,
              icon: const Icon(Icons.add_rounded, size: 18),
              label: const Text(
                'Join',
                style: TextStyle(fontWeight: FontWeight.w700, fontSize: 13),
              ),
              style: TextButton.styleFrom(
                foregroundColor: AppTheme.primary,
                backgroundColor: AppTheme.primary.withOpacity(0.08),
                padding: const EdgeInsets.symmetric(
                  horizontal: 14,
                  vertical: 8,
                ),
                shape: RoundedRectangleBorder(
                  borderRadius: BorderRadius.circular(20),
                ),
              ),
            ),
          ),
        ],
      ),
      body: RefreshIndicator(
        color: AppTheme.primary,
        onRefresh: () =>
            ref.read(communityViewModelProvider.notifier).fetchMyCommunities(),
        child: communitiesAsync.when(
          loading: () => LayoutBuilder(
            builder: (context, constraints) => SingleChildScrollView(
              physics: const AlwaysScrollableScrollPhysics(),
              child: SizedBox(
                height: constraints.maxHeight,
                child: const Center(child: CircularProgressIndicator()),
              ),
            ),
          ),
          error: (e, _) => LayoutBuilder(
            builder: (context, constraints) => SingleChildScrollView(
              physics: const AlwaysScrollableScrollPhysics(),
              child: SizedBox(
                height: constraints.maxHeight,
                child: Center(
                  child: Padding(
                    padding: const EdgeInsets.all(32),
                    child: Column(
                      mainAxisSize: MainAxisSize.min,
                      children: [
                        const Icon(
                          Icons.cloud_off_rounded,
                          size: 56,
                          color: AppTheme.textLight,
                        ),
                        const SizedBox(height: 16),
                        Text(
                          'Something went wrong\n$e',
                          textAlign: TextAlign.center,
                          style: const TextStyle(
                            color: AppTheme.textSecondary,
                            fontSize: 13,
                          ),
                        ),
                        const SizedBox(height: 16),
                        TextButton.icon(
                          onPressed: () => ref
                              .read(communityViewModelProvider.notifier)
                              .fetchMyCommunities(),
                          icon: const Icon(Icons.refresh_rounded),
                          label: const Text('Retry'),
                        ),
                      ],
                    ),
                  ),
                ),
              ),
            ),
          ),
          data: (communities) {
            final hasJoined = communities.isNotEmpty || hasCollege;

            if (!hasJoined) {
              return LayoutBuilder(
                builder: (context, constraints) => SingleChildScrollView(
                  physics: const AlwaysScrollableScrollPhysics(),
                  child: SizedBox(
                    height: constraints.maxHeight,
                    child: _EmptyState(onTap: _openOptions),
                  ),
                ),
              );
            }

            return ListView(
              physics: const AlwaysScrollableScrollPhysics(),
              padding: const EdgeInsets.fromLTRB(16, 20, 16, 120),
              children: [
                // ── College section ──
                if (hasCollege) ...[
                  _SectionLabel(label: 'My College', onManage: _leaveCollege),
                  const SizedBox(height: 10),
                  _CollegeCard(college: college, onLeave: _leaveCollege),
                  const SizedBox(height: 28),
                ],

                // ── Communities section ──
                if (communities.isNotEmpty) ...[
                  Row(
                    children: [
                      const Text(
                        'JOINED COMMUNITIES',
                        style: TextStyle(
                          fontSize: 11,
                          fontWeight: FontWeight.w700,
                          color: AppTheme.textLight,
                          letterSpacing: 0.8,
                        ),
                      ),
                      const Spacer(),
                      Text(
                        '${communities.length} joined',
                        style: const TextStyle(
                          fontSize: 11,
                          color: AppTheme.textSecondary,
                        ),
                      ),
                    ],
                  ),
                  const SizedBox(height: 10),
                  ...communities.map(
                    (community) => _CommunityCard(
                      community: community,
                      onLeave: () async {
                        try {
                          await ref
                              .read(communityViewModelProvider.notifier)
                              .leaveCommunity(community.id);
                          if (mounted) {
                            ScaffoldMessenger.of(context).showSnackBar(
                              const SnackBar(
                                content: Text('Left community successfully'),
                              ),
                            );
                          }
                        } catch (e) {
                          if (mounted) {
                            ScaffoldMessenger.of(context).showSnackBar(
                              SnackBar(
                                content: Text('Error leaving community: $e'),
                                backgroundColor: Colors.red,
                              ),
                            );
                          }
                        }
                      },
                    ),
                  ),
                ],
              ],
            );
          },
        ),
      ),
    );
  }
}

// ── Empty State ────────────────────────────────────────────────────────────────

class _EmptyState extends StatelessWidget {
  final VoidCallback onTap;

  const _EmptyState({required this.onTap});

  @override
  Widget build(BuildContext context) {
    return Center(
      child: Padding(
        padding: const EdgeInsets.symmetric(horizontal: 40),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            Container(
              width: 100,
              height: 100,
              decoration: BoxDecoration(
                color: AppTheme.primary.withOpacity(0.08),
                shape: BoxShape.circle,
              ),
              child: Icon(Icons.add_rounded, size: 52, color: AppTheme.primary),
            ),
            const SizedBox(height: 24),
            const Text(
              'Find & Join Your\nCollege Community',
              textAlign: TextAlign.center,
              style: TextStyle(
                fontSize: 22,
                fontWeight: FontWeight.w800,
                color: AppTheme.textPrimary,
                height: 1.3,
              ),
            ),
            const SizedBox(height: 12),
            const Text(
              'Connect with students from your campus,\njoin interest groups, and stay in the loop.',
              textAlign: TextAlign.center,
              style: TextStyle(
                fontSize: 14,
                color: AppTheme.textSecondary,
                height: 1.6,
              ),
            ),
            const SizedBox(height: 32),
            SizedBox(
              width: double.infinity,
              child: ElevatedButton.icon(
                onPressed: onTap,
                icon: const Icon(Icons.add_rounded, size: 20),
                label: const Text(
                  'Get Started',
                  style: TextStyle(fontWeight: FontWeight.w700, fontSize: 15),
                ),
                style: ElevatedButton.styleFrom(
                  padding: const EdgeInsets.symmetric(vertical: 15),
                  shape: RoundedRectangleBorder(
                    borderRadius: BorderRadius.circular(14),
                  ),
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }
}

// ── Section Label ──────────────────────────────────────────────────────────────

class _SectionLabel extends StatelessWidget {
  final String label;
  final VoidCallback? onManage;

  const _SectionLabel({required this.label, this.onManage});

  @override
  Widget build(BuildContext context) {
    return Row(
      children: [
        Text(
          label.toUpperCase(),
          style: const TextStyle(
            fontSize: 11,
            fontWeight: FontWeight.w700,
            color: AppTheme.textLight,
            letterSpacing: 0.8,
          ),
        ),
        const Spacer(),
        if (onManage != null)
          GestureDetector(
            onTap: onManage,
            child: const Text(
              'Manage',
              style: TextStyle(
                fontSize: 12,
                color: AppTheme.primary,
                fontWeight: FontWeight.w600,
              ),
            ),
          ),
      ],
    );
  }
}

// ── Browse Sheet ───────────────────────────────────────────────────────────────

class _BrowseSheet extends ConsumerStatefulWidget {
  final void Function(SearchResultItem) onSelectCollege;
  final VoidCallback onCreateCommunity;

  const _BrowseSheet({
    required this.onSelectCollege,
    required this.onCreateCommunity,
  });

  @override
  ConsumerState<_BrowseSheet> createState() => _BrowseSheetState();
}

class _BrowseSheetState extends ConsumerState<_BrowseSheet> {
  final _searchCtrl = TextEditingController();
  final _scrollCtrl = ScrollController();

  // type filter: 'community' | 'college' | 'all'
  String _typeFilter = 'all';

  static const _filters = [
    ('All', 'all', Icons.apps_rounded),
    ('Communities', 'community', Icons.people_rounded),
    ('Colleges', 'college', Icons.school_rounded),
  ];

  @override
  void initState() {
    super.initState();
    _scrollCtrl.addListener(_onScroll);
    // kick off a default search so results appear immediately
    WidgetsBinding.instance.addPostFrameCallback((_) {
      // Reset providers to a clean state
      ref.read(searchTypeFilterProvider.notifier).state = 'all';
      ref.read(searchQueryProvider.notifier).state = '';
      ref
          .read(searchViewModelProvider.notifier)
          .search(query: 'a', reset: true);
    });
  }

  void _onScroll() {
    if (_scrollCtrl.position.pixels >=
        _scrollCtrl.position.maxScrollExtent - 200) {
      final state = ref.read(searchViewModelProvider).value;
      if (state != null && state.hasMore && !state.isLoadingMore) {
        ref
            .read(searchViewModelProvider.notifier)
            .search(
              query: _searchCtrl.text.trim().isEmpty
                  ? 'a'
                  : _searchCtrl.text.trim(),
              reset: false,
            );
      }
    }
  }

  void _onQueryChanged(String v) {
    final q = v.trim().isEmpty ? 'a' : v.trim();
    ref.read(searchViewModelProvider.notifier).onQueryChanged(q);
  }

  void _setFilter(String type) {
    if (_typeFilter == type) return;
    setState(() => _typeFilter = type);
    ref.read(searchViewModelProvider.notifier).setTypeFilter(type);
  }

  @override
  void dispose() {
    _searchCtrl.dispose();
    _scrollCtrl.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final searchState = ref.watch(searchViewModelProvider);

    return Container(
      height: MediaQuery.of(context).size.height * 0.90,
      decoration: const BoxDecoration(
        color: AppTheme.surface,
        borderRadius: BorderRadius.vertical(top: Radius.circular(28)),
      ),
      child: Column(
        children: [
          // ── Header ──────────────────────────────────────────────────────
          Container(
            decoration: const BoxDecoration(
              color: Colors.white,
              borderRadius: BorderRadius.vertical(top: Radius.circular(28)),
            ),
            padding: const EdgeInsets.fromLTRB(20, 12, 20, 0),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                // Handle
                Center(
                  child: Container(
                    width: 36,
                    height: 4,
                    decoration: BoxDecoration(
                      color: AppTheme.divider,
                      borderRadius: BorderRadius.circular(2),
                    ),
                  ),
                ),
                const SizedBox(height: 16),
                // Title row
                Row(
                  children: [
                    const Expanded(
                      child: Text(
                        'Browse Communities',
                        style: TextStyle(
                          fontSize: 18,
                          fontWeight: FontWeight.w800,
                          color: AppTheme.textPrimary,
                        ),
                      ),
                    ),
                    GestureDetector(
                      onTap: () => Navigator.pop(context),
                      child: Container(
                        width: 32,
                        height: 32,
                        decoration: BoxDecoration(
                          color: AppTheme.surface,
                          shape: BoxShape.circle,
                          border: Border.all(color: AppTheme.divider),
                        ),
                        child: const Icon(
                          Icons.close_rounded,
                          size: 16,
                          color: AppTheme.textSecondary,
                        ),
                      ),
                    ),
                  ],
                ),
                const SizedBox(height: 14),
                // Search bar
                TextField(
                  controller: _searchCtrl,
                  onChanged: _onQueryChanged,
                  decoration: InputDecoration(
                    hintText: 'Search communities or colleges…',
                    prefixIcon: const Icon(
                      Icons.search_rounded,
                      color: AppTheme.textLight,
                      size: 20,
                    ),
                    suffixIcon: _searchCtrl.text.isNotEmpty
                        ? GestureDetector(
                            onTap: () {
                              _searchCtrl.clear();
                              _onQueryChanged('');
                            },
                            child: const Icon(
                              Icons.clear_rounded,
                              size: 18,
                              color: AppTheme.textLight,
                            ),
                          )
                        : null,
                    contentPadding: const EdgeInsets.symmetric(
                      horizontal: 16,
                      vertical: 12,
                    ),
                  ),
                ),
                const SizedBox(height: 12),
                // Type filter chips
                SizedBox(
                  height: 34,
                  child: ListView(
                    scrollDirection: Axis.horizontal,
                    children: _filters.map((f) {
                      final selected = _typeFilter == f.$2;
                      return Padding(
                        padding: const EdgeInsets.only(right: 8),
                        child: GestureDetector(
                          onTap: () => _setFilter(f.$2),
                          child: AnimatedContainer(
                            duration: const Duration(milliseconds: 160),
                            padding: const EdgeInsets.symmetric(horizontal: 14),
                            decoration: BoxDecoration(
                              color: selected ? AppTheme.primary : Colors.white,
                              borderRadius: BorderRadius.circular(20),
                              border: Border.all(
                                color: selected
                                    ? AppTheme.primary
                                    : AppTheme.divider,
                              ),
                            ),
                            child: Row(
                              children: [
                                Icon(
                                  f.$3,
                                  size: 13,
                                  color: selected
                                      ? Colors.white
                                      : AppTheme.textSecondary,
                                ),
                                const SizedBox(width: 5),
                                Text(
                                  f.$1,
                                  style: TextStyle(
                                    fontSize: 12,
                                    fontWeight: FontWeight.w600,
                                    color: selected
                                        ? Colors.white
                                        : AppTheme.textSecondary,
                                  ),
                                ),
                              ],
                            ),
                          ),
                        ),
                      );
                    }).toList(),
                  ),
                ),
                const SizedBox(height: 12),
              ],
            ),
          ),

          // ── Results ─────────────────────────────────────────────────────
          Expanded(
            child: searchState.when(
              loading: () => const Center(child: CircularProgressIndicator()),
              error: (e, _) => Center(
                child: Padding(
                  padding: const EdgeInsets.all(32),
                  child: Column(
                    mainAxisSize: MainAxisSize.min,
                    children: [
                      const Icon(
                        Icons.cloud_off_rounded,
                        size: 48,
                        color: AppTheme.textLight,
                      ),
                      const SizedBox(height: 12),
                      Text(
                        e.toString(),
                        textAlign: TextAlign.center,
                        style: const TextStyle(
                          color: AppTheme.textSecondary,
                          fontSize: 13,
                        ),
                      ),
                    ],
                  ),
                ),
              ),
              data: (state) {
                if (state.items.isEmpty) {
                  return Center(
                    child: Column(
                      mainAxisSize: MainAxisSize.min,
                      children: [
                        const Icon(
                          Icons.search_off_rounded,
                          size: 48,
                          color: AppTheme.textLight,
                        ),
                        const SizedBox(height: 12),
                        Text(
                          _searchCtrl.text.isEmpty
                              ? 'Type to search…'
                              : 'No results for "${_searchCtrl.text}"',
                          style: const TextStyle(
                            color: AppTheme.textSecondary,
                            fontSize: 13,
                          ),
                        ),
                      ],
                    ),
                  );
                }

                // Split items when "All" is selected
                if (_typeFilter == 'all') {
                  final colleges = state.items
                      .where((i) => i.type == 'college')
                      .toList();
                  final communities = state.items
                      .where((i) => i.type != 'college')
                      .toList();

                  return ListView(
                    controller: _scrollCtrl,
                    padding: const EdgeInsets.fromLTRB(16, 8, 16, 32),
                    children: [
                      // ── Colleges section ──────────────────────────────
                      if (colleges.isNotEmpty) ...[
                        _ResultSectionHeader(
                          icon: Icons.school_rounded,
                          label: 'Colleges',
                          count: colleges.length,
                        ),
                        const SizedBox(height: 8),
                        ...colleges.map(
                          (item) => _SearchCollegeTile(
                            item: item,
                            onTap: widget.onSelectCollege,
                          ),
                        ),
                        const SizedBox(height: 16),
                      ],
                      // ── Communities section ───────────────────────────
                      if (communities.isNotEmpty) ...[
                        _ResultSectionHeader(
                          icon: Icons.people_rounded,
                          label: 'Communities',
                          count: communities.length,
                        ),
                        const SizedBox(height: 8),
                        ...communities.map(
                          (item) => _SearchCommunityTile(
                            item: item,
                            onJoined: () {
                              ref
                                  .read(communityViewModelProvider.notifier)
                                  .fetchMyCommunities();
                            },
                          ),
                        ),
                      ],
                      if (state.isLoadingMore)
                        const Padding(
                          padding: EdgeInsets.all(16),
                          child: Center(child: CircularProgressIndicator()),
                        ),
                    ],
                  );
                }

                // Flat list for single-type filters
                return Column(
                  children: [
                    Padding(
                      padding: const EdgeInsets.fromLTRB(20, 10, 20, 6),
                      child: Row(
                        children: [
                          Text(
                            '${state.total} result${state.total == 1 ? '' : 's'}',
                            style: const TextStyle(
                              fontSize: 12,
                              fontWeight: FontWeight.w600,
                              color: AppTheme.textSecondary,
                            ),
                          ),
                        ],
                      ),
                    ),
                    Expanded(
                      child: ListView.builder(
                        controller: _scrollCtrl,
                        padding: const EdgeInsets.fromLTRB(16, 4, 16, 32),
                        itemCount:
                            state.items.length + (state.isLoadingMore ? 1 : 0),
                        itemBuilder: (_, i) {
                          if (i == state.items.length) {
                            return const Padding(
                              padding: EdgeInsets.all(16),
                              child: Center(child: CircularProgressIndicator()),
                            );
                          }
                          final item = state.items[i];
                          return item.type == 'college'
                              ? _SearchCollegeTile(
                                  item: item,
                                  onTap: widget.onSelectCollege,
                                )
                              : _SearchCommunityTile(
                                  item: item,
                                  onJoined: () {
                                    ref
                                        .read(
                                          communityViewModelProvider.notifier,
                                        )
                                        .fetchMyCommunities();
                                  },
                                );
                        },
                      ),
                    ),
                  ],
                );
              },
            ),
          ),
        ],
      ),
    );
  }
}

// ── Result section header ──────────────────────────────────────────────────────

class _ResultSectionHeader extends StatelessWidget {
  final IconData icon;
  final String label;
  final int count;

  const _ResultSectionHeader({
    required this.icon,
    required this.label,
    required this.count,
  });

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.only(bottom: 2),
      child: Row(
        children: [
          Icon(icon, size: 14, color: AppTheme.textLight),
          const SizedBox(width: 6),
          Text(
            label.toUpperCase(),
            style: const TextStyle(
              fontSize: 11,
              fontWeight: FontWeight.w700,
              color: AppTheme.textLight,
              letterSpacing: 0.8,
            ),
          ),
          const SizedBox(width: 6),
          Container(
            padding: const EdgeInsets.symmetric(horizontal: 7, vertical: 2),
            decoration: BoxDecoration(
              color: AppTheme.primary.withOpacity(0.08),
              borderRadius: BorderRadius.circular(8),
            ),
            child: Text(
              '$count',
              style: const TextStyle(
                fontSize: 10.5,
                fontWeight: FontWeight.w700,
                color: AppTheme.primary,
              ),
            ),
          ),
        ],
      ),
    );
  }
}

// ── Search result: community tile ──────────────────────────────────────────────

class _SearchCommunityTile extends ConsumerWidget {
  final SearchResultItem item;
  final VoidCallback onJoined;

  const _SearchCommunityTile({required this.item, required this.onJoined});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final isPrivate = item.communityType == 'PRIVATE';

    return Container(
      margin: const EdgeInsets.only(bottom: 10),
      padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 13),
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(14),
        border: Border.all(color: AppTheme.divider),
      ),
      child: Row(
        children: [
          // Icon
          Container(
            width: 44,
            height: 44,
            decoration: BoxDecoration(
              color: AppTheme.primary.withOpacity(0.08),
              borderRadius: BorderRadius.circular(11),
            ),
            child: const Icon(
              Icons.people_rounded,
              color: AppTheme.primary,
              size: 20,
            ),
          ),
          const SizedBox(width: 12),
          // Info
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Row(
                  children: [
                    Expanded(
                      child: Text(
                        item.name,
                        style: const TextStyle(
                          fontSize: 13.5,
                          fontWeight: FontWeight.w600,
                          color: AppTheme.textPrimary,
                        ),
                        maxLines: 1,
                        overflow: TextOverflow.ellipsis,
                      ),
                    ),
                    if (isPrivate)
                      Container(
                        margin: const EdgeInsets.only(left: 6),
                        padding: const EdgeInsets.symmetric(
                          horizontal: 7,
                          vertical: 2,
                        ),
                        decoration: BoxDecoration(
                          color: AppTheme.textLight.withOpacity(0.12),
                          borderRadius: BorderRadius.circular(8),
                        ),
                        child: const Text(
                          'Private',
                          style: TextStyle(
                            fontSize: 10,
                            color: AppTheme.textSecondary,
                            fontWeight: FontWeight.w600,
                          ),
                        ),
                      ),
                  ],
                ),
                const SizedBox(height: 3),
                Row(
                  children: [
                    const Icon(
                      Icons.people_outline,
                      size: 12,
                      color: AppTheme.textLight,
                    ),
                    const SizedBox(width: 4),
                    Text(
                      item.memberCount != null
                          ? '${item.memberCount} members'
                          : 'Community',
                      style: const TextStyle(
                        fontSize: 11.5,
                        color: AppTheme.textSecondary,
                      ),
                    ),
                    if (item.parentColleges != null &&
                        item.parentColleges!.isNotEmpty) ...[
                      const SizedBox(width: 8),
                      const Icon(
                        Icons.school_outlined,
                        size: 12,
                        color: AppTheme.textLight,
                      ),
                      const SizedBox(width: 3),
                      Expanded(
                        child: Text(
                          item.parentColleges!.first,
                          style: const TextStyle(
                            fontSize: 11,
                            color: AppTheme.textLight,
                          ),
                          maxLines: 1,
                          overflow: TextOverflow.ellipsis,
                        ),
                      ),
                    ],
                  ],
                ),
              ],
            ),
          ),
          const SizedBox(width: 8),
          // Join button
          _JoinButton(item: item, onJoined: onJoined),
        ],
      ),
    );
  }
}

// ── Join button with loading state ────────────────────────────────────────────

class _JoinButton extends ConsumerStatefulWidget {
  final SearchResultItem item;
  final VoidCallback onJoined;

  const _JoinButton({required this.item, required this.onJoined});

  @override
  ConsumerState<_JoinButton> createState() => _JoinButtonState();
}

class _JoinButtonState extends ConsumerState<_JoinButton> {
  bool _loading = false;
  // null = not yet acted, true = joined (member), false = requested (pending)
  bool? _joinResult;

  bool get _isPrivate => widget.item.communityType == 'PRIVATE';

  Future<void> _join() async {
    if (_loading || _joinResult != null) return;
    setState(() => _loading = true);
    try {
      final result = await ref
          .read(communityViewModelProvider.notifier)
          .joinCommunity(widget.item.id);

      if (mounted) {
        // status='joined' = joined instantly, status='requested' = pending
        if (result.status == 'joined') {
          setState(() => _joinResult = true);
          widget.onJoined();
          ScaffoldMessenger.of(context).showSnackBar(
            SnackBar(
              content: Text('Joined "${widget.item.name}"'),
              behavior: SnackBarBehavior.floating,
            ),
          );
        } else {
          // Requested (private community pending approval)
          setState(() => _joinResult = false);
          ScaffoldMessenger.of(context).showSnackBar(
            SnackBar(
              content: Text('Request sent to join "${widget.item.name}"'),
              behavior: SnackBarBehavior.floating,
            ),
          );
        }
      }
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text('Failed to join: $e'),
            backgroundColor: Colors.red,
            behavior: SnackBarBehavior.floating,
          ),
        );
      }
    } finally {
      if (mounted) setState(() => _loading = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    // Joined state
    if (_joinResult == true) {
      return Container(
        padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 6),
        decoration: BoxDecoration(
          color: AppTheme.success.withOpacity(0.10),
          borderRadius: BorderRadius.circular(20),
        ),
        child: const Text(
          'Joined',
          style: TextStyle(
            fontSize: 12,
            fontWeight: FontWeight.w700,
            color: AppTheme.success,
          ),
        ),
      );
    }

    // Requested state (private community pending approval)
    if (_joinResult == false) {
      return Container(
        padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 6),
        decoration: BoxDecoration(
          color: Colors.orange.withOpacity(0.12),
          borderRadius: BorderRadius.circular(20),
          border: Border.all(color: Colors.orange.withOpacity(0.4)),
        ),
        child: Row(
          mainAxisSize: MainAxisSize.min,
          children: const [
            Icon(Icons.hourglass_top_rounded, size: 11, color: Colors.orange),
            SizedBox(width: 4),
            Text(
              'Requested',
              style: TextStyle(
                fontSize: 12,
                fontWeight: FontWeight.w700,
                color: Colors.orange,
              ),
            ),
          ],
        ),
      );
    }

    // Default join button
    return GestureDetector(
      onTap: _join,
      child: Container(
        padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 6),
        decoration: BoxDecoration(
          color: AppTheme.primary,
          borderRadius: BorderRadius.circular(20),
        ),
        child: _loading
            ? const SizedBox(
                width: 14,
                height: 14,
                child: CircularProgressIndicator(
                  strokeWidth: 2,
                  color: Colors.white,
                ),
              )
            : Row(
                mainAxisSize: MainAxisSize.min,
                children: [
                  if (_isPrivate) ...[
                    const Icon(
                      Icons.lock_outline_rounded,
                      size: 11,
                      color: Colors.white,
                    ),
                    const SizedBox(width: 4),
                  ],
                  const Text(
                    'Join',
                    style: TextStyle(
                      fontSize: 12,
                      fontWeight: FontWeight.w700,
                      color: Colors.white,
                    ),
                  ),
                ],
              ),
      ),
    );
  }
}

// ── Search result: college tile ────────────────────────────────────────────────

class _SearchCollegeTile extends StatelessWidget {
  final SearchResultItem item;
  final void Function(SearchResultItem) onTap;

  const _SearchCollegeTile({required this.item, required this.onTap});

  @override
  Widget build(BuildContext context) {
    return GestureDetector(
      onTap: () => onTap(item),
      child: Container(
        margin: const EdgeInsets.only(bottom: 10),
        padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 13),
        decoration: BoxDecoration(
          color: Colors.white,
          borderRadius: BorderRadius.circular(14),
          border: Border.all(color: AppTheme.divider),
        ),
        child: Row(
          children: [
            Container(
              width: 44,
              height: 44,
              decoration: BoxDecoration(
                color: AppTheme.primary.withOpacity(0.08),
                borderRadius: BorderRadius.circular(11),
              ),
              child: const Icon(
                Icons.school_rounded,
                color: AppTheme.primary,
                size: 20,
              ),
            ),
            const SizedBox(width: 12),
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    item.name,
                    style: const TextStyle(
                      fontSize: 13.5,
                      fontWeight: FontWeight.w600,
                      color: AppTheme.textPrimary,
                    ),
                    maxLines: 1,
                    overflow: TextOverflow.ellipsis,
                  ),
                  if (item.physicalAddress != null) ...[
                    const SizedBox(height: 3),
                    Row(
                      children: [
                        const Icon(
                          Icons.location_on_outlined,
                          size: 12,
                          color: AppTheme.textLight,
                        ),
                        const SizedBox(width: 3),
                        Expanded(
                          child: Text(
                            item.physicalAddress!,
                            style: const TextStyle(
                              fontSize: 11.5,
                              color: AppTheme.textSecondary,
                            ),
                            maxLines: 1,
                            overflow: TextOverflow.ellipsis,
                          ),
                        ),
                      ],
                    ),
                  ],
                  if (item.communityCount != null) ...[
                    const SizedBox(height: 2),
                    Text(
                      '${item.communityCount} communities',
                      style: const TextStyle(
                        fontSize: 11,
                        color: AppTheme.textLight,
                      ),
                    ),
                  ],
                ],
              ),
            ),
            const SizedBox(width: 8),
            const Icon(
              Icons.chevron_right_rounded,
              size: 20,
              color: AppTheme.textLight,
            ),
          ],
        ),
      ),
    );
  }
}

// ── College Card ───────────────────────────────────────────────────────────────

class _CollegeCard extends StatelessWidget {
  final CollegeModel college;
  final VoidCallback onLeave;

  const _CollegeCard({required this.college, required this.onLeave});

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(16),
        border: Border.all(color: AppTheme.primary.withOpacity(0.2)),
        boxShadow: [
          BoxShadow(
            color: AppTheme.primary.withOpacity(0.06),
            blurRadius: 12,
            offset: const Offset(0, 2),
          ),
        ],
      ),
      child: Row(
        children: [
          Container(
            width: 48,
            height: 48,
            decoration: BoxDecoration(
              gradient: const LinearGradient(
                colors: [AppTheme.primary, AppTheme.primaryLight],
                begin: Alignment.topLeft,
                end: Alignment.bottomRight,
              ),
              borderRadius: BorderRadius.circular(12),
            ),
            child: const Icon(
              Icons.school_rounded,
              color: Colors.white,
              size: 22,
            ),
          ),
          const SizedBox(width: 14),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  college.name,
                  style: const TextStyle(
                    fontSize: 14,
                    fontWeight: FontWeight.w700,
                    color: AppTheme.textPrimary,
                  ),
                  maxLines: 1,
                  overflow: TextOverflow.ellipsis,
                ),
                const SizedBox(height: 2),
                Text(
                  college.physicalAddress,
                  style: const TextStyle(
                    fontSize: 12,
                    color: AppTheme.textSecondary,
                  ),
                ),
              ],
            ),
          ),
          const SizedBox(width: 8),
          Container(
            padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 5),
            decoration: BoxDecoration(
              color: AppTheme.success.withOpacity(0.1),
              borderRadius: BorderRadius.circular(20),
            ),
            child: const Text(
              'Joined',
              style: TextStyle(
                fontSize: 11,
                fontWeight: FontWeight.w600,
                color: AppTheme.success,
              ),
            ),
          ),
        ],
      ),
    );
  }
}

// ── Community Card ─────────────────────────────────────────────────────────────

class _CommunityCard extends StatelessWidget {
  final Community community;
  final VoidCallback onLeave;

  const _CommunityCard({required this.community, required this.onLeave});

  @override
  Widget build(BuildContext context) {
    return Container(
      margin: const EdgeInsets.only(bottom: 10),
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(16),
        border: Border.all(color: AppTheme.divider),
        boxShadow: [
          BoxShadow(
            color: Colors.black.withOpacity(0.04),
            blurRadius: 10,
            offset: const Offset(0, 2),
          ),
        ],
      ),
      child: Row(
        children: [
          Container(
            width: 44,
            height: 44,
            decoration: BoxDecoration(
              color: AppTheme.accent.withOpacity(0.12),
              borderRadius: BorderRadius.circular(10),
            ),
            child: const Icon(
              Icons.people_rounded,
              color: AppTheme.accent,
              size: 22,
            ),
          ),
          const SizedBox(width: 12),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  community.name,
                  style: const TextStyle(
                    fontSize: 14,
                    fontWeight: FontWeight.w600,
                    color: AppTheme.textPrimary,
                  ),
                ),
                const SizedBox(height: 2),
                Text(
                  '${community.memberCount} member${community.memberCount == 1 ? '' : 's'}',
                  style: const TextStyle(
                    fontSize: 12,
                    color: AppTheme.textSecondary,
                  ),
                ),
              ],
            ),
          ),
          IconButton(
            onPressed: () => _confirmLeave(context),
            icon: const Icon(
              Icons.exit_to_app_rounded,
              color: Colors.red,
              size: 20,
            ),
            tooltip: 'Leave community',
          ),
        ],
      ),
    );
  }

  void _confirmLeave(BuildContext context) {
    showDialog(
      context: context,
      builder: (ctx) => AlertDialog(
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(20)),
        title: const Text('Leave Community?'),
        content: Text('Are you sure you want to leave "${community.name}"?'),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(ctx),
            child: const Text('Cancel'),
          ),
          TextButton(
            onPressed: () {
              Navigator.pop(ctx);
              onLeave();
            },
            child: const Text('Leave', style: TextStyle(color: Colors.red)),
          ),
        ],
      ),
    );
  }
}

// ── College Picker Bottom Sheet ───────────────────────────────────────────────

class _CollegePickerSheet extends ConsumerStatefulWidget {
  const _CollegePickerSheet();

  @override
  ConsumerState<_CollegePickerSheet> createState() =>
      _CollegePickerSheetState();
}

class _CollegePickerSheetState extends ConsumerState<_CollegePickerSheet> {
  final _searchCtrl = TextEditingController();

  @override
  void dispose() {
    _searchCtrl.dispose();
    super.dispose();
  }

  void _onSearch() {
    ref
        .read(collegeSelectViewModelProvider.notifier)
        .searchColleges(_searchCtrl.text);
  }

  @override
  Widget build(BuildContext context) {
    final bottomInset = MediaQuery.of(context).viewInsets.bottom;
    final collegesAsync = ref.watch(collegeSelectViewModelProvider);

    return Container(
      height: MediaQuery.of(context).size.height * 0.75 + bottomInset,
      decoration: const BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.vertical(top: Radius.circular(24)),
      ),
      child: Column(
        children: [
          const SizedBox(height: 12),
          Container(
            width: 36,
            height: 4,
            decoration: BoxDecoration(
              color: AppTheme.divider,
              borderRadius: BorderRadius.circular(2),
            ),
          ),
          const SizedBox(height: 16),
          const Padding(
            padding: EdgeInsets.symmetric(horizontal: 20),
            child: Align(
              alignment: Alignment.centerLeft,
              child: Text(
                'Select Your College',
                style: TextStyle(
                  fontSize: 18,
                  fontWeight: FontWeight.w700,
                  color: AppTheme.textPrimary,
                ),
              ),
            ),
          ),
          const SizedBox(height: 14),
          Padding(
            padding: const EdgeInsets.symmetric(horizontal: 16),
            child: TextField(
              controller: _searchCtrl,
              autofocus: true,
              onChanged: (_) => _onSearch(),
              decoration: InputDecoration(
                hintText: 'Search colleges…',
                prefixIcon: const Icon(
                  Icons.search_rounded,
                  color: AppTheme.textLight,
                  size: 20,
                ),
                suffixIcon: _searchCtrl.text.isNotEmpty
                    ? GestureDetector(
                        onTap: () {
                          _searchCtrl.clear();
                          _onSearch();
                        },
                        child: const Icon(
                          Icons.clear_rounded,
                          size: 18,
                          color: AppTheme.textLight,
                        ),
                      )
                    : null,
              ),
            ),
          ),
          const SizedBox(height: 12),
          Expanded(
            child: collegesAsync.when(
              loading: () => const Center(child: CircularProgressIndicator()),
              error: (e, _) => Center(
                child: Text(
                  e.toString(),
                  style: const TextStyle(color: AppTheme.textSecondary),
                ),
              ),
              data: (colleges) {
                if (colleges.isEmpty) {
                  return const Center(
                    child: Text(
                      'No colleges found',
                      style: TextStyle(color: AppTheme.textSecondary),
                    ),
                  );
                }
                return ListView.separated(
                  padding: const EdgeInsets.symmetric(
                    horizontal: 16,
                    vertical: 4,
                  ),
                  itemCount: colleges.length,
                  separatorBuilder: (_, __) => const Divider(height: 1),
                  itemBuilder: (_, i) {
                    final c = colleges[i];
                    return ListTile(
                      contentPadding: const EdgeInsets.symmetric(
                        horizontal: 8,
                        vertical: 4,
                      ),
                      leading: Container(
                        width: 40,
                        height: 40,
                        decoration: BoxDecoration(
                          color: AppTheme.primary.withOpacity(0.08),
                          borderRadius: BorderRadius.circular(10),
                        ),
                        child: const Icon(
                          Icons.school_outlined,
                          color: AppTheme.primary,
                          size: 20,
                        ),
                      ),
                      title: Text(
                        c.name,
                        style: const TextStyle(
                          fontSize: 13.5,
                          fontWeight: FontWeight.w600,
                          color: AppTheme.textPrimary,
                        ),
                      ),
                      subtitle: Text(
                        c.physicalAddress,
                        style: const TextStyle(
                          fontSize: 12,
                          color: AppTheme.textSecondary,
                        ),
                      ),
                      onTap: () => Navigator.pop(context, c),
                    );
                  },
                );
              },
            ),
          ),
          SizedBox(height: bottomInset),
        ],
      ),
    );
  }
}

// ── Create Community Bottom Sheet ─────────────────────────────────────────────

class _CreateCommunitySheet extends ConsumerStatefulWidget {
  const _CreateCommunitySheet();

  @override
  ConsumerState<_CreateCommunitySheet> createState() =>
      _CreateCommunitySheetState();
}

class _CreateCommunitySheetState extends ConsumerState<_CreateCommunitySheet> {
  final _formKey = GlobalKey<FormState>();
  final _nameCtrl = TextEditingController();
  String _selectedType = _types[0];
  bool _isLoading = false;

  static const _types = ['PUBLIC', 'PRIVATE'];

  @override
  void dispose() {
    _nameCtrl.dispose();
    super.dispose();
  }

  Future<void> _submit() async {
    if (!(_formKey.currentState?.validate() ?? false)) return;
    setState(() => _isLoading = true);
    try {
      await ref
          .read(communityViewModelProvider.notifier)
          .createCommunity(name: _nameCtrl.text.trim(), type: _selectedType);
      if (mounted) Navigator.pop(context, true);
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text('Failed to create community: $e'),
            backgroundColor: Colors.red,
          ),
        );
      }
    } finally {
      if (mounted) setState(() => _isLoading = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    final bottomInset = MediaQuery.of(context).viewInsets.bottom;

    return Container(
      padding: EdgeInsets.fromLTRB(20, 0, 20, 20 + bottomInset),
      decoration: const BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.vertical(top: Radius.circular(24)),
      ),
      child: Form(
        key: _formKey,
        child: Column(
          mainAxisSize: MainAxisSize.min,
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            const SizedBox(height: 12),
            Center(
              child: Container(
                width: 36,
                height: 4,
                decoration: BoxDecoration(
                  color: AppTheme.divider,
                  borderRadius: BorderRadius.circular(2),
                ),
              ),
            ),
            const SizedBox(height: 20),
            const Text(
              'Create a Community',
              style: TextStyle(
                fontSize: 18,
                fontWeight: FontWeight.w700,
                color: AppTheme.textPrimary,
              ),
            ),
            const SizedBox(height: 4),
            const Text(
              'Any student can start a community around a shared interest.',
              style: TextStyle(fontSize: 13, color: AppTheme.textSecondary),
            ),
            const SizedBox(height: 24),
            const Text(
              'Community Name',
              style: TextStyle(
                fontSize: 12.5,
                fontWeight: FontWeight.w600,
                color: AppTheme.textPrimary,
              ),
            ),
            const SizedBox(height: 8),
            TextFormField(
              controller: _nameCtrl,
              autofocus: true,
              textCapitalization: TextCapitalization.words,
              decoration: const InputDecoration(
                hintText: 'e.g. Photography Club, Study Group …',
                prefixIcon: Icon(
                  Icons.people_outline_rounded,
                  color: AppTheme.textLight,
                  size: 20,
                ),
              ),
              validator: (v) {
                if (v == null || v.trim().isEmpty) {
                  return 'Please enter a community name';
                }
                if (v.trim().length < 3) {
                  return 'Name must be at least 3 characters';
                }
                return null;
              },
            ),
            const SizedBox(height: 20),
            const Text(
              'Visibility',
              style: TextStyle(
                fontSize: 12.5,
                fontWeight: FontWeight.w600,
                color: AppTheme.textPrimary,
              ),
            ),
            const SizedBox(height: 8),
            Row(
              children: _types.map((type) {
                final selected = _selectedType == type;
                final isPublic = type == _types[0];
                return Expanded(
                  child: GestureDetector(
                    onTap: () => setState(() => _selectedType = type),
                    child: AnimatedContainer(
                      duration: const Duration(milliseconds: 180),
                      margin: EdgeInsets.only(right: isPublic ? 8 : 0),
                      padding: const EdgeInsets.symmetric(vertical: 12),
                      decoration: BoxDecoration(
                        color: selected
                            ? AppTheme.primary.withOpacity(0.08)
                            : Colors.transparent,
                        borderRadius: BorderRadius.circular(10),
                        border: Border.all(
                          color: selected ? AppTheme.primary : AppTheme.divider,
                          width: selected ? 1.5 : 1,
                        ),
                      ),
                      child: Column(
                        children: [
                          Icon(
                            isPublic
                                ? Icons.public_rounded
                                : Icons.lock_outline_rounded,
                            color: selected
                                ? AppTheme.primary
                                : AppTheme.textLight,
                            size: 20,
                          ),
                          const SizedBox(height: 4),
                          Text(
                            isPublic ? 'Public' : 'Private',
                            style: TextStyle(
                              fontSize: 13,
                              fontWeight: FontWeight.w600,
                              color: selected
                                  ? AppTheme.primary
                                  : AppTheme.textSecondary,
                            ),
                          ),
                          const SizedBox(height: 2),
                          Text(
                            isPublic ? 'Anyone can join' : 'Approval required',
                            style: const TextStyle(
                              fontSize: 10.5,
                              color: AppTheme.textLight,
                            ),
                          ),
                        ],
                      ),
                    ),
                  ),
                );
              }).toList(),
            ),
            const SizedBox(height: 28),
            SizedBox(
              width: double.infinity,
              child: ElevatedButton(
                onPressed: _isLoading ? null : _submit,
                style: ElevatedButton.styleFrom(
                  padding: const EdgeInsets.symmetric(vertical: 14),
                ),
                child: _isLoading
                    ? const SizedBox(
                        width: 20,
                        height: 20,
                        child: CircularProgressIndicator(
                          strokeWidth: 2,
                          color: Colors.white,
                        ),
                      )
                    : const Text(
                        'Create Community',
                        style: TextStyle(
                          fontWeight: FontWeight.w600,
                          fontSize: 14,
                        ),
                      ),
              ),
            ),
          ],
        ),
      ),
    );
  }
}
