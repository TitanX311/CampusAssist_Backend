// lib/screens/home_screen.dart
import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../models/post_model.dart';
import '../theme/app_theme.dart';
import '../widgets/post_card.dart';
import '../widgets/skeleton_loaders.dart';
import '../viewmodel/post_viewmodel.dart';
import '../viewmodel/auth_viewmodel.dart';
import '../viewmodel/notification_viewmodel.dart';
import 'package:campusassist/screens/post_detail_screen.dart';
import 'package:campusassist/screens/notifications_screen.dart';

class HomeScreen extends ConsumerStatefulWidget {
  const HomeScreen({super.key});

  @override
  ConsumerState<HomeScreen> createState() => _HomeScreenState();
}

class _HomeScreenState extends ConsumerState<HomeScreen>
    with SingleTickerProviderStateMixin {
  late TabController _tabCtrl;

  @override
  void initState() {
    super.initState();
    _tabCtrl = TabController(length: 2, vsync: this);
  }

  @override
  void dispose() {
    _tabCtrl.dispose();
    super.dispose();
  }

  void _openPost(Post post) {
    Navigator.push(
      context,
      MaterialPageRoute(builder: (_) => PostDetailScreen(post: post)),
    );
  }

  @override
  Widget build(BuildContext context) {
    final myFeedAsync = ref.watch(feedProvider);
    final globalAsync = ref.watch(globalFeedProvider);
    final unread = ref.watch(unreadCountProvider);
    final user = ref.watch(authViewModelProvider).value;

    return AnnotatedRegion<SystemUiOverlayStyle>(
      value: SystemUiOverlayStyle.dark,
      child: Scaffold(
        backgroundColor: const Color(0xFFF3F2EF), // LinkedIn background
        body: NestedScrollView(
          headerSliverBuilder: (_, innerScrolled) => [
            SliverAppBar(
              floating: true,
              snap: true,
              pinned: false,
              backgroundColor: Colors.white,
              surfaceTintColor: Colors.transparent,
              elevation: innerScrolled ? 0.5 : 0,
              shadowColor: Colors.black12,
              toolbarHeight: 56,
              titleSpacing: 0,
              title: Padding(
                padding: const EdgeInsets.symmetric(horizontal: 16),
                child: Row(
                  children: [
                    // Avatar
                    _Avatar(
                      name: user?.name ?? '',
                      pictureUrl: user?.pictureURL,
                    ),
                    const SizedBox(width: 10),
                    // Search bar (placeholder)
                    Expanded(
                      child: Container(
                        height: 36,
                        decoration: BoxDecoration(
                          color: const Color(0xFFF3F2EF),
                          borderRadius: BorderRadius.circular(4),
                          border: Border.all(
                            color: const Color(0xFFB0B7C3),
                            width: 1,
                          ),
                        ),
                        padding: const EdgeInsets.symmetric(horizontal: 12),
                        child: const Row(
                          children: [
                            Icon(
                              Icons.search_rounded,
                              size: 18,
                              color: AppTheme.textSecondary,
                            ),
                            SizedBox(width: 8),
                            Text(
                              'Search',
                              style: TextStyle(
                                fontSize: 14,
                                color: AppTheme.textSecondary,
                              ),
                            ),
                          ],
                        ),
                      ),
                    ),
                    const SizedBox(width: 4),
                    // Notifications
                    _IconBtn(
                      icon: unread > 0
                          ? Icons.notifications_rounded
                          : Icons.notifications_outlined,
                      badge: unread,
                      color: unread > 0 ? AppTheme.primary : null,
                      onTap: () => Navigator.push(
                        context,
                        MaterialPageRoute(
                          builder: (_) => const NotificationsScreen(),
                        ),
                      ),
                    ),
                  ],
                ),
              ),
              bottom: PreferredSize(
                preferredSize: const Size.fromHeight(46),
                child: _LinkedInTabBar(controller: _tabCtrl),
              ),
            ),
          ],
          body: TabBarView(
            controller: _tabCtrl,
            children: [
              _FeedList(
                feedAsync: myFeedAsync,
                emptyTitle: 'Your feed is empty',
                emptyMessage:
                    'Join communities and follow topics you care about.',
                emptyIcon: Icons.dynamic_feed_rounded,
                onRefresh: () => ref.read(feedProvider.notifier).refresh(),
                onLoadMore: () => ref.read(feedProvider.notifier).loadMore(),
                onUpvote: (id) =>
                    ref.read(feedProvider.notifier).toggleLike(id),
                onTap: _openPost,
              ),
              _FeedList(
                feedAsync: globalAsync,
                emptyTitle: 'Nothing trending yet',
                emptyMessage: 'Check back soon for posts from across India.',
                emptyIcon: Icons.travel_explore_rounded,
                onRefresh: () =>
                    ref.read(globalFeedProvider.notifier).refresh(),
                onLoadMore: () =>
                    ref.read(globalFeedProvider.notifier).loadMore(),
                onUpvote: (id) =>
                    ref.read(globalFeedProvider.notifier).toggleLike(id),
                onTap: _openPost,
              ),
            ],
          ),
        ),
      ),
    );
  }
}

// ── Avatar ────────────────────────────────────────────────────────────────────

class _Avatar extends StatelessWidget {
  final String name;
  final String? pictureUrl;
  const _Avatar({required this.name, this.pictureUrl});

  @override
  Widget build(BuildContext context) {
    return CircleAvatar(
      radius: 18,
      backgroundColor: AppTheme.primary,
      backgroundImage: pictureUrl != null ? NetworkImage(pictureUrl!) : null,
      child: pictureUrl == null
          ? Text(
              name.isNotEmpty ? name[0].toUpperCase() : 'S',
              style: const TextStyle(
                color: Colors.white,
                fontWeight: FontWeight.w700,
                fontSize: 14,
              ),
            )
          : null,
    );
  }
}

// ── Small icon button ─────────────────────────────────────────────────────────

class _IconBtn extends StatelessWidget {
  final IconData icon;
  final int badge;
  final Color? color;
  final VoidCallback onTap;

  const _IconBtn({
    required this.icon,
    this.badge = 0,
    this.color,
    required this.onTap,
  });

  @override
  Widget build(BuildContext context) {
    return GestureDetector(
      onTap: onTap,
      child: SizedBox(
        width: 40,
        height: 40,
        child: Stack(
          alignment: Alignment.center,
          children: [
            Icon(icon, size: 24, color: color ?? AppTheme.textSecondary),
            if (badge > 0)
              Positioned(
                top: 6,
                right: 6,
                child: Container(
                  width: 8,
                  height: 8,
                  decoration: const BoxDecoration(
                    color: AppTheme.error,
                    shape: BoxShape.circle,
                  ),
                ),
              ),
          ],
        ),
      ),
    );
  }
}

// ── LinkedIn-style tab bar ────────────────────────────────────────────────────

class _LinkedInTabBar extends StatelessWidget {
  final TabController controller;
  const _LinkedInTabBar({required this.controller});

  @override
  Widget build(BuildContext context) {
    return Container(
      color: Colors.white,
      child: Column(
        mainAxisSize: MainAxisSize.min,
        children: [
          const Divider(height: 1, thickness: 0.5, color: Color(0xFFE0E0E0)),
          TabBar(
            controller: controller,
            labelColor: AppTheme.textPrimary,
            unselectedLabelColor: AppTheme.textSecondary,
            labelStyle: const TextStyle(
              fontWeight: FontWeight.w600,
              fontSize: 13,
            ),
            unselectedLabelStyle: const TextStyle(
              fontWeight: FontWeight.w400,
              fontSize: 13,
            ),
            indicator: const UnderlineTabIndicator(
              borderSide: BorderSide(color: AppTheme.primary, width: 2.5),
              insets: EdgeInsets.symmetric(horizontal: 24),
            ),
            dividerColor: Colors.transparent,
            tabs: const [
              Tab(text: 'My Feed'),
              Tab(text: 'Across India'),
            ],
          ),
        ],
      ),
    );
  }
}

// ── Feed list ─────────────────────────────────────────────────────────────────

class _FeedList extends StatefulWidget {
  final AsyncValue<FeedState> feedAsync;
  final String emptyTitle;
  final String emptyMessage;
  final IconData emptyIcon;
  final Future<void> Function() onRefresh;
  final Future<void> Function() onLoadMore;
  final Future<void> Function(String id) onUpvote;
  final void Function(Post) onTap;

  const _FeedList({
    required this.feedAsync,
    required this.emptyTitle,
    required this.emptyMessage,
    required this.emptyIcon,
    required this.onRefresh,
    required this.onLoadMore,
    required this.onUpvote,
    required this.onTap,
  });

  @override
  State<_FeedList> createState() => _FeedListState();
}

class _FeedListState extends State<_FeedList> {
  final _scrollCtrl = ScrollController();

  @override
  void initState() {
    super.initState();
    _scrollCtrl.addListener(_onScroll);
  }

  @override
  void dispose() {
    _scrollCtrl.removeListener(_onScroll);
    _scrollCtrl.dispose();
    super.dispose();
  }

  void _onScroll() {
    if (_scrollCtrl.position.pixels >=
        _scrollCtrl.position.maxScrollExtent - 300) {
      widget.onLoadMore();
    }
  }

  @override
  Widget build(BuildContext context) {
    return widget.feedAsync.when(
      loading: () => const SkeletonPostList(count: 4),
      error: (e, _) => _ErrorState(
        message: e.toString().replaceFirst('Exception: ', ''),
        onRetry: widget.onRefresh,
      ),
      data: (feedState) {
        final posts = feedState.posts;
        if (posts.isEmpty) {
          return _EmptyState(
            icon: widget.emptyIcon,
            title: widget.emptyTitle,
            message: widget.emptyMessage,
            onRefresh: widget.onRefresh,
          );
        }

        return RefreshIndicator(
          color: AppTheme.primary,
          strokeWidth: 2,
          onRefresh: widget.onRefresh,
          child: ListView.builder(
            controller: _scrollCtrl,
            // No horizontal padding — cards go full width like LinkedIn
            padding: const EdgeInsets.only(top: 8, bottom: 100),
            itemCount: posts.length + (feedState.isLoadingMore ? 1 : 0),
            itemBuilder: (_, i) {
              if (i == posts.length) {
                return const Padding(
                  padding: EdgeInsets.symmetric(vertical: 24),
                  child: Center(
                    child: SizedBox(
                      width: 22,
                      height: 22,
                      child: CircularProgressIndicator(
                        strokeWidth: 2,
                        color: AppTheme.primary,
                      ),
                    ),
                  ),
                );
              }
              return PostCard(
                post: posts[i],
                onTap: () => widget.onTap(posts[i]),
                onUpvote: widget.onUpvote,
              );
            },
          ),
        );
      },
    );
  }
}

// ── Empty state ───────────────────────────────────────────────────────────────

class _EmptyState extends StatelessWidget {
  final IconData icon;
  final String title;
  final String message;
  final Future<void> Function() onRefresh;

  const _EmptyState({
    required this.icon,
    required this.title,
    required this.message,
    required this.onRefresh,
  });

  @override
  Widget build(BuildContext context) {
    return RefreshIndicator(
      color: AppTheme.primary,
      strokeWidth: 2,
      onRefresh: onRefresh,
      child: ListView(
        children: [
          SizedBox(
            height: MediaQuery.of(context).size.height * 0.6,
            child: Column(
              mainAxisAlignment: MainAxisAlignment.center,
              children: [
                Icon(icon, size: 48, color: const Color(0xFFB0B7C3)),
                const SizedBox(height: 16),
                Text(
                  title,
                  style: const TextStyle(
                    fontSize: 16,
                    fontWeight: FontWeight.w600,
                    color: AppTheme.textPrimary,
                  ),
                ),
                const SizedBox(height: 8),
                Padding(
                  padding: const EdgeInsets.symmetric(horizontal: 48),
                  child: Text(
                    message,
                    textAlign: TextAlign.center,
                    style: const TextStyle(
                      fontSize: 13,
                      color: AppTheme.textSecondary,
                      height: 1.5,
                    ),
                  ),
                ),
                const SizedBox(height: 24),
                OutlinedButton(
                  onPressed: onRefresh,
                  style: OutlinedButton.styleFrom(
                    foregroundColor: AppTheme.primary,
                    side: const BorderSide(color: AppTheme.primary, width: 1.5),
                    shape: RoundedRectangleBorder(
                      borderRadius: BorderRadius.circular(24),
                    ),
                    padding: const EdgeInsets.symmetric(
                      horizontal: 28,
                      vertical: 10,
                    ),
                  ),
                  child: const Text(
                    'Refresh',
                    style: TextStyle(fontWeight: FontWeight.w600, fontSize: 14),
                  ),
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }
}

// ── Error state ───────────────────────────────────────────────────────────────

class _ErrorState extends StatelessWidget {
  final String message;
  final Future<void> Function() onRetry;

  const _ErrorState({required this.message, required this.onRetry});

  @override
  Widget build(BuildContext context) {
    return Center(
      child: Padding(
        padding: const EdgeInsets.all(40),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            const Icon(
              Icons.cloud_off_rounded,
              size: 40,
              color: Color(0xFFB0B7C3),
            ),
            const SizedBox(height: 16),
            const Text(
              'Could not load feed',
              style: TextStyle(
                fontSize: 15,
                fontWeight: FontWeight.w600,
                color: AppTheme.textPrimary,
              ),
            ),
            const SizedBox(height: 6),
            Text(
              message,
              textAlign: TextAlign.center,
              style: const TextStyle(
                color: AppTheme.textSecondary,
                fontSize: 13,
                height: 1.4,
              ),
            ),
            const SizedBox(height: 20),
            OutlinedButton(
              onPressed: onRetry,
              style: OutlinedButton.styleFrom(
                foregroundColor: AppTheme.primary,
                side: const BorderSide(color: AppTheme.primary, width: 1.5),
                shape: RoundedRectangleBorder(
                  borderRadius: BorderRadius.circular(24),
                ),
                padding: const EdgeInsets.symmetric(
                  horizontal: 28,
                  vertical: 10,
                ),
              ),
              child: const Text(
                'Try Again',
                style: TextStyle(fontWeight: FontWeight.w600, fontSize: 14),
              ),
            ),
          ],
        ),
      ),
    );
  }
}
