// lib/screens/college_detail_screen.dart
import 'package:campusassist/models/community_model.dart';
import 'package:campusassist/viewmodel/college_detail_viewmodel.dart';
import 'package:campusassist/viewmodel/community_viewmodel.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../theme/app_theme.dart';

class CollegeDetailScreen extends ConsumerStatefulWidget {
  final String collegeId;
  final String collegeName; // shown instantly before data loads

  const CollegeDetailScreen({
    super.key,
    required this.collegeId,
    required this.collegeName,
  });

  @override
  ConsumerState<CollegeDetailScreen> createState() =>
      _CollegeDetailScreenState();
}

class _CollegeDetailScreenState extends ConsumerState<CollegeDetailScreen> {
  final _scrollCtrl = ScrollController();

  @override
  void initState() {
    super.initState();
    _scrollCtrl.addListener(_onScroll);
  }

  void _onScroll() {
    if (_scrollCtrl.position.pixels >=
        _scrollCtrl.position.maxScrollExtent - 200) {
      ref
          .read(collegeDetailViewModelProvider(widget.collegeId).notifier)
          .loadMoreCommunities();
    }
  }

  @override
  void dispose() {
    _scrollCtrl.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final asyncState = ref.watch(
      collegeDetailViewModelProvider(widget.collegeId),
    );

    return Scaffold(
      backgroundColor: AppTheme.surface,
      body: asyncState.when(
        loading: () => _buildScrollable(null, loading: true),
        error: (e, _) => _buildScrollable(null, error: e.toString()),
        data: (state) => _buildScrollable(state),
      ),
    );
  }

  Widget _buildScrollable(
    CollegeDetailState? state, {
    bool loading = false,
    String? error,
  }) {
    final college = state?.college;

    return RefreshIndicator(
      color: AppTheme.primary,
      onRefresh: state != null
          ? () => ref
                .read(collegeDetailViewModelProvider(widget.collegeId).notifier)
                .refresh()
          : () async {},
      child: CustomScrollView(
        controller: _scrollCtrl,
        physics: const AlwaysScrollableScrollPhysics(),
        slivers: [
          // ── App Bar ──────────────────────────────────────────────────────
          SliverAppBar(
            pinned: true,
            backgroundColor: Colors.white,
            surfaceTintColor: Colors.transparent,
            elevation: 0,
            leading: IconButton(
              icon: const Icon(
                Icons.arrow_back_ios_new_rounded,
                size: 18,
                color: AppTheme.textPrimary,
              ),
              onPressed: () => Navigator.pop(context),
            ),
            title: Text(
              college?.name ?? widget.collegeName,
              style: const TextStyle(
                fontSize: 16,
                fontWeight: FontWeight.w700,
                color: AppTheme.textPrimary,
              ),
              maxLines: 1,
              overflow: TextOverflow.ellipsis,
            ),
            bottom: PreferredSize(
              preferredSize: const Size.fromHeight(1),
              child: Container(height: 1, color: AppTheme.divider),
            ),
          ),

          // ── Loading / Error ───────────────────────────────────────────────
          if (loading)
            const SliverFillRemaining(
              child: Center(child: CircularProgressIndicator()),
            )
          else if (error != null)
            SliverFillRemaining(
              child: Center(
                child: Padding(
                  padding: const EdgeInsets.all(32),
                  child: Column(
                    mainAxisSize: MainAxisSize.min,
                    children: [
                      const Icon(
                        Icons.cloud_off_rounded,
                        size: 52,
                        color: AppTheme.textLight,
                      ),
                      const SizedBox(height: 12),
                      Text(
                        error,
                        textAlign: TextAlign.center,
                        style: const TextStyle(
                          color: AppTheme.textSecondary,
                          fontSize: 13,
                        ),
                      ),
                      const SizedBox(height: 20),
                      FilledButton(
                        onPressed: () => ref
                            .read(
                              collegeDetailViewModelProvider(
                                widget.collegeId,
                              ).notifier,
                            )
                            .retry(),
                        child: const Text('Retry'),
                      ),
                    ],
                  ),
                ),
              ),
            )
          else if (state != null) ...[
            // ── College Info Card ───────────────────────────────────────────
            SliverToBoxAdapter(
              child: Padding(
                padding: const EdgeInsets.fromLTRB(16, 16, 16, 0),
                child: _CollegeInfoCard(
                  name: college?.name ?? widget.collegeName,
                  email: college?.contactEmail,
                  address: college?.physicalAddress,
                  communityCount: state.communities.length,
                ),
              ),
            ),

            // ── Communities header ──────────────────────────────────────────
            SliverToBoxAdapter(
              child: Padding(
                padding: const EdgeInsets.fromLTRB(16, 24, 16, 10),
                child: Row(
                  children: [
                    const Icon(
                      Icons.people_rounded,
                      size: 16,
                      color: AppTheme.primary,
                    ),
                    const SizedBox(width: 6),
                    const Text(
                      'Communities',
                      style: TextStyle(
                        fontSize: 15,
                        fontWeight: FontWeight.w700,
                        color: AppTheme.textPrimary,
                      ),
                    ),
                    const SizedBox(width: 8),
                    if (state.communities.isNotEmpty)
                      Container(
                        padding: const EdgeInsets.symmetric(
                          horizontal: 8,
                          vertical: 2,
                        ),
                        decoration: BoxDecoration(
                          color: AppTheme.primary.withOpacity(0.08),
                          borderRadius: BorderRadius.circular(10),
                        ),
                        child: Text(
                          '${state.communities.length}',
                          style: const TextStyle(
                            fontSize: 11,
                            fontWeight: FontWeight.w700,
                            color: AppTheme.primary,
                          ),
                        ),
                      ),
                  ],
                ),
              ),
            ),

            // ── Communities list ────────────────────────────────────────────
            if (state.communities.isEmpty && !state.isLoadingCommunities)
              SliverToBoxAdapter(
                child: Padding(
                  padding: const EdgeInsets.all(32),
                  child: Center(
                    child: Column(
                      mainAxisSize: MainAxisSize.min,
                      children: [
                        Icon(
                          Icons.people_outline,
                          size: 48,
                          color: AppTheme.textLight.withOpacity(0.5),
                        ),
                        const SizedBox(height: 12),
                        const Text(
                          'No communities yet',
                          style: TextStyle(
                            color: AppTheme.textSecondary,
                            fontSize: 13,
                          ),
                        ),
                      ],
                    ),
                  ),
                ),
              )
            else
              SliverPadding(
                padding: const EdgeInsets.fromLTRB(16, 0, 16, 16),
                sliver: SliverList(
                  delegate: SliverChildBuilderDelegate(
                    (context, i) {
                      if (i == state.communities.length) {
                        return const Padding(
                          padding: EdgeInsets.all(16),
                          child: Center(child: CircularProgressIndicator()),
                        );
                      }
                      return _CommunityTile(
                        community: state.communities[i],
                        onJoined: () => ref
                            .read(communityViewModelProvider.notifier)
                            .fetchMyCommunities(),
                      );
                    },
                    childCount:
                        state.communities.length +
                        (state.isLoadingCommunities ? 1 : 0),
                  ),
                ),
              ),

            const SliverToBoxAdapter(child: SizedBox(height: 32)),
          ],
        ],
      ),
    );
  }
}

// ── College Info Card ─────────────────────────────────────────────────────────

class _CollegeInfoCard extends StatelessWidget {
  final String name;
  final String? email;
  final String? address;
  final int communityCount;

  const _CollegeInfoCard({
    required this.name,
    this.email,
    this.address,
    required this.communityCount,
  });

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.all(20),
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(18),
        border: Border.all(color: AppTheme.primary.withOpacity(0.15)),
        boxShadow: [
          BoxShadow(
            color: AppTheme.primary.withOpacity(0.06),
            blurRadius: 16,
            offset: const Offset(0, 4),
          ),
        ],
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          // Icon + name
          Row(
            children: [
              Container(
                width: 56,
                height: 56,
                decoration: BoxDecoration(
                  gradient: const LinearGradient(
                    colors: [AppTheme.primary, AppTheme.primaryLight],
                    begin: Alignment.topLeft,
                    end: Alignment.bottomRight,
                  ),
                  borderRadius: BorderRadius.circular(14),
                ),
                child: const Icon(
                  Icons.school_rounded,
                  color: Colors.white,
                  size: 26,
                ),
              ),
              const SizedBox(width: 14),
              Expanded(
                child: Text(
                  name,
                  style: const TextStyle(
                    fontSize: 16,
                    fontWeight: FontWeight.w800,
                    color: AppTheme.textPrimary,
                  ),
                  maxLines: 2,
                  overflow: TextOverflow.ellipsis,
                ),
              ),
            ],
          ),
          const SizedBox(height: 16),
          // Divider
          const Divider(color: AppTheme.divider, height: 1),
          const SizedBox(height: 14),
          // Details
          if (address != null && address!.isNotEmpty)
            _DetailRow(icon: Icons.location_on_outlined, text: address!),
          if (email != null && email!.isNotEmpty) ...[
            const SizedBox(height: 8),
            _DetailRow(icon: Icons.email_outlined, text: email!),
          ],
          const SizedBox(height: 14),
          // Stats row
          Row(
            children: [
              _StatChip(
                icon: Icons.people_rounded,
                label: '$communityCount communities',
              ),
            ],
          ),
        ],
      ),
    );
  }
}

class _DetailRow extends StatelessWidget {
  final IconData icon;
  final String text;

  const _DetailRow({required this.icon, required this.text});

  @override
  Widget build(BuildContext context) {
    return Row(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Icon(icon, size: 14, color: AppTheme.textLight),
        const SizedBox(width: 8),
        Expanded(
          child: Text(
            text,
            style: const TextStyle(
              fontSize: 12.5,
              color: AppTheme.textSecondary,
            ),
          ),
        ),
      ],
    );
  }
}

class _StatChip extends StatelessWidget {
  final IconData icon;
  final String label;

  const _StatChip({required this.icon, required this.label});

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 6),
      decoration: BoxDecoration(
        color: AppTheme.primary.withOpacity(0.07),
        borderRadius: BorderRadius.circular(20),
      ),
      child: Row(
        mainAxisSize: MainAxisSize.min,
        children: [
          Icon(icon, size: 13, color: AppTheme.primary),
          const SizedBox(width: 5),
          Text(
            label,
            style: const TextStyle(
              fontSize: 12,
              fontWeight: FontWeight.w600,
              color: AppTheme.primary,
            ),
          ),
        ],
      ),
    );
  }
}

// ── Community Tile ────────────────────────────────────────────────────────────

class _CommunityTile extends ConsumerStatefulWidget {
  final Community community;
  final VoidCallback onJoined;

  const _CommunityTile({required this.community, required this.onJoined});

  @override
  ConsumerState<_CommunityTile> createState() => _CommunityTileState();
}

class _CommunityTileState extends ConsumerState<_CommunityTile> {
  bool _loading = false;
  // null = not yet acted, true = joined (member), false = requested (pending)
  bool? _joinResult;

  bool get _isPrivate => widget.community.type == 'PRIVATE';

  Future<void> _join() async {
    if (_loading || _joinResult != null) return;
    setState(() => _loading = true);
    try {
      final result = await ref
          .read(communityViewModelProvider.notifier)
          .joinCommunity(widget.community.id);

      if (mounted) {
        // status='joined' = instant join (PUBLIC); status='requested' = pending (PRIVATE)
        if (result.status == 'joined') {
          setState(() => _joinResult = true);
          widget.onJoined();
          ScaffoldMessenger.of(context).showSnackBar(
            SnackBar(
              content: Text('Joined "${widget.community.name}"'),
              behavior: SnackBarBehavior.floating,
            ),
          );
        } else {
          setState(() => _joinResult = false);
          ScaffoldMessenger.of(context).showSnackBar(
            SnackBar(
              content: Text('Request sent to join "${widget.community.name}"'),
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
                        widget.community.name,
                        style: const TextStyle(
                          fontSize: 13.5,
                          fontWeight: FontWeight.w600,
                          color: AppTheme.textPrimary,
                        ),
                        maxLines: 1,
                        overflow: TextOverflow.ellipsis,
                      ),
                    ),
                    if (_isPrivate)
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
                      '${widget.community.memberCount} member${widget.community.memberCount == 1 ? '' : 's'}',
                      style: const TextStyle(
                        fontSize: 11.5,
                        color: AppTheme.textSecondary,
                      ),
                    ),
                  ],
                ),
              ],
            ),
          ),
          const SizedBox(width: 8),
          // Join / Requested / Joined button
          GestureDetector(
            onTap: _joinResult == null ? _join : null,
            child: _joinResult == true
                // ── Joined ──────────────────────────────────────
                ? Container(
                    padding: const EdgeInsets.symmetric(
                      horizontal: 12,
                      vertical: 6,
                    ),
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
                  )
                : _joinResult == false
                // ── Requested ───────────────────────────────
                ? Container(
                    padding: const EdgeInsets.symmetric(
                      horizontal: 12,
                      vertical: 6,
                    ),
                    decoration: BoxDecoration(
                      color: Colors.orange.withOpacity(0.12),
                      borderRadius: BorderRadius.circular(20),
                      border: Border.all(color: Colors.orange.withOpacity(0.4)),
                    ),
                    child: Row(
                      mainAxisSize: MainAxisSize.min,
                      children: const [
                        Icon(
                          Icons.hourglass_top_rounded,
                          size: 11,
                          color: Colors.orange,
                        ),
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
                  )
                // ── Join ────────────────────────────────────
                : Container(
                    padding: const EdgeInsets.symmetric(
                      horizontal: 12,
                      vertical: 6,
                    ),
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
          ),
        ],
      ),
    );
  }
}
