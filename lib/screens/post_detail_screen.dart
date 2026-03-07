// lib/screens/post_detail_screen.dart
import 'package:flutter/material.dart';
import 'package:flutter_markdown/flutter_markdown.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../models/post_model.dart';
import '../repositories/post_remote_repository.dart';
import '../theme/app_theme.dart';
import '../viewmodel/post_viewmodel.dart';
import '../widgets/skeleton_loaders.dart';
import 'package:timeago/timeago.dart' as timeago;
import 'campus_map_screen.dart';

class PostDetailScreen extends ConsumerStatefulWidget {
  final Post post;
  const PostDetailScreen({super.key, required this.post});

  @override
  ConsumerState<PostDetailScreen> createState() => _PostDetailScreenState();
}

class _PostDetailScreenState extends ConsumerState<PostDetailScreen> {
  late Post _post;
  final _answerCtrl = TextEditingController();
  bool _submitting = false;

  @override
  void initState() {
    super.initState();
    _post = widget.post;
    // Fetch fresh post data so liked_by_me and likes count are accurate.
    // The feed API never returns liked_by_me so hasUpvoted is always false
    // from feeds — we fix it here from the server.
    _refreshPostState();
  }

  Future<void> _refreshPostState() async {
    debugPrint('[PostDetail] ══════ INIT POST STATE ══════');
    debugPrint('[PostDetail] passed-in post:');
    debugPrint('[PostDetail]   id          = ${_post.id}');
    debugPrint('[PostDetail]   likes       = ${_post.upvotes}');
    debugPrint('[PostDetail]   hasUpvoted  = ${_post.hasUpvoted}');
    debugPrint('[PostDetail]   authorAlias = ${_post.authorAlias}');
    debugPrint('[PostDetail]   userId      = ${_post.userId}');
    debugPrint('[PostDetail]   communityId = ${_post.communityId}');
    debugPrint('[PostDetail] ════════════════════════════════');

    // First check session — if user already interacted this session, trust that
    final session = ref.read(sessionLikesProvider);
    debugPrint('[PostDetail] sessionLikes = $session');
    if (session.containsKey(_post.id)) {
      final liked = session[_post.id]!;
      debugPrint(
        '[PostDetail] session override → hasUpvoted=$liked (skipping fetch)',
      );
      if (liked != _post.hasUpvoted) {
        if (mounted) setState(() => _post = _post.copyWith(hasUpvoted: liked));
      }
      return;
    }

    // Otherwise fetch fresh from the server to get liked_by_me
    if (!mounted) return;
    try {
      debugPrint(
        '[PostDetail] fetching fresh post from GET /posts/${_post.id}',
      );
      final fresh = await ref
          .read(postRemoteRepositoryProvider)
          .getPostById(_post.id);
      debugPrint('[PostDetail] ══════ FRESH POST FROM SERVER ══════');
      debugPrint('[PostDetail]   id          = ${fresh.id}');
      debugPrint('[PostDetail]   likes       = ${fresh.upvotes}');
      debugPrint('[PostDetail]   hasUpvoted  = ${fresh.hasUpvoted}');
      debugPrint('[PostDetail]   authorAlias = ${fresh.authorAlias}');
      debugPrint('[PostDetail]   userId      = ${fresh.userId}');
      debugPrint('[PostDetail] ════════════════════════════════════');
      if (mounted) setState(() => _post = fresh);
    } catch (e) {
      debugPrint('[PostDetail] getPostById failed (non-fatal): $e');
    }
  }

  @override
  void dispose() {
    _answerCtrl.dispose();
    super.dispose();
  }

  Future<void> _upvotePost() async {
    // Capture snapshot BEFORE any changes so we can revert cleanly
    final snapshot = _post;
    final wasUpvoted = snapshot.hasUpvoted;

    debugPrint('[PostDetail] ══════ TOGGLE LIKE ══════');
    debugPrint(
      '[PostDetail] post_id=${snapshot.id}  '
      'wasUpvoted=$wasUpvoted  currentLikes=${snapshot.upvotes}',
    );
    debugPrint(
      '[PostDetail] → will call ${wasUpvoted ? 'DELETE' : 'POST'} /posts/${snapshot.id}/like',
    );

    // 1. Optimistic local update
    setState(() {
      _post = snapshot.copyWith(
        upvotes: wasUpvoted ? snapshot.upvotes - 1 : snapshot.upvotes + 1,
        hasUpvoted: !wasUpvoted,
      );
    });

    try {
      // 2. Call API — POST to like, DELETE to unlike
      final result = await ref
          .read(postRemoteRepositoryProvider)
          .likePost(snapshot.id, hasUpvoted: wasUpvoted);

      debugPrint(
        '[PostDetail] server response → likes=${result.likes}  liked=${result.liked}',
      );
      debugPrint('[PostDetail] ════════════════════════');

      // 3. Sync authoritative server values locally
      if (mounted) {
        setState(() {
          _post = _post.copyWith(
            upvotes: result.likes,
            hasUpvoted: result.liked,
          );
        });
      }

      // 4. Propagate to all feed / community lists
      ref
          .read(feedProvider.notifier)
          .syncLike(snapshot.id, result.likes, result.liked);
      ref
          .read(globalFeedProvider.notifier)
          .syncLike(snapshot.id, result.likes, result.liked);
      if (snapshot.communityId.isNotEmpty) {
        ref
            .read(postListProvider(snapshot.communityId).notifier)
            .syncLike(snapshot.id, result.likes, result.liked);
      }
    } catch (_) {
      // 5. Revert to snapshot on failure
      if (mounted) setState(() => _post = snapshot);
    }
  }

  Future<void> _submitAnswer() async {
    final text = _answerCtrl.text.trim();
    if (text.isEmpty) return;
    setState(() => _submitting = true);
    try {
      final key = commentsProvider(
        postId: _post.id,
        communityId: _post.communityId,
      );
      await ref.read(key.notifier).addComment(text);
      _answerCtrl.clear();
      setState(
        () => _post = _post.copyWith(answerCount: _post.answerCount + 1),
      );
      FocusScope.of(context).unfocus();
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text('Failed to post answer: $e'),
            backgroundColor: AppTheme.error,
            behavior: SnackBarBehavior.floating,
          ),
        );
      }
    } finally {
      if (mounted) setState(() => _submitting = false);
    }
  }

  void _openCampusMap() {
    Navigator.push(
      context,
      MaterialPageRoute(
        builder: (_) => CampusMapScreen(
          collegeId: _post.collegeId,
          collegeName: _post.collegeName,
          locationLabel: _post.locationLabel,
          locationLat: _post.locationLat,
          locationLng: _post.locationLng,
          postTitle: _post.content.length > 60
              ? '${_post.content.substring(0, 60)}...'
              : _post.content,
        ),
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    final catColor = AppTheme.categoryColor(_post.category.label);

    final commentsAsync = ref.watch(
      commentsProvider(postId: _post.id, communityId: _post.communityId),
    );

    return Scaffold(
      resizeToAvoidBottomInset: false,
      backgroundColor: AppTheme.surface,
      appBar: AppBar(
        title: Text(_post.category.label),
        leading: IconButton(
          icon: const Icon(Icons.arrow_back_ios_new_rounded),
          onPressed: () => Navigator.pop(context),
        ),
        actions: [
          IconButton(icon: const Icon(Icons.share_rounded), onPressed: () {}),
        ],
      ),
      body: Column(
        children: [
          Expanded(
            child: SingleChildScrollView(
              padding: const EdgeInsets.all(16),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Container(
                    decoration: BoxDecoration(
                      color: AppTheme.cardBg,
                      borderRadius: BorderRadius.circular(16),
                      border: Border.all(color: AppTheme.divider),
                    ),
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Container(
                          padding: const EdgeInsets.symmetric(
                            horizontal: 16,
                            vertical: 12,
                          ),
                          decoration: BoxDecoration(
                            color: catColor.withOpacity(0.07),
                            borderRadius: const BorderRadius.vertical(
                              top: Radius.circular(16),
                            ),
                          ),
                          child: Row(
                            children: [
                              Container(
                                padding: const EdgeInsets.symmetric(
                                  horizontal: 12,
                                  vertical: 5,
                                ),
                                decoration: BoxDecoration(
                                  color: catColor.withOpacity(0.15),
                                  borderRadius: BorderRadius.circular(20),
                                ),
                                child: Row(
                                  mainAxisSize: MainAxisSize.min,
                                  children: [
                                    Icon(
                                      AppTheme.categoryIcon(
                                        _post.category.label,
                                      ),
                                      size: 13,
                                      color: catColor,
                                    ),
                                    const SizedBox(width: 5),
                                    Text(
                                      _post.category.label,
                                      style: TextStyle(
                                        color: catColor,
                                        fontSize: 12,
                                        fontWeight: FontWeight.w600,
                                      ),
                                    ),
                                  ],
                                ),
                              ),
                              const Spacer(),
                              Text(
                                timeago.format(_post.createdAt),
                                style: const TextStyle(
                                  fontSize: 11,
                                  color: AppTheme.textLight,
                                ),
                              ),
                            ],
                          ),
                        ),
                        Padding(
                          padding: const EdgeInsets.all(16),
                          child: Column(
                            crossAxisAlignment: CrossAxisAlignment.start,
                            children: [
                              MarkdownBody(
                                data: _post.content,
                                selectable: true,
                                styleSheet:
                                    MarkdownStyleSheet.fromTheme(
                                      Theme.of(context),
                                    ).copyWith(
                                      p: const TextStyle(
                                        fontSize: 14,
                                        color: AppTheme.textPrimary,
                                        height: 1.55,
                                      ),
                                      strong: const TextStyle(
                                        fontSize: 14,
                                        color: AppTheme.textPrimary,
                                        fontWeight: FontWeight.w700,
                                      ),
                                      em: const TextStyle(
                                        fontSize: 14,
                                        color: AppTheme.textPrimary,
                                        fontStyle: FontStyle.italic,
                                      ),
                                      code: TextStyle(
                                        fontFamily: 'monospace',
                                        fontSize: 12.5,
                                        backgroundColor: AppTheme.surface,
                                        color: AppTheme.primary,
                                      ),
                                      codeblockDecoration: BoxDecoration(
                                        color: AppTheme.surface,
                                        borderRadius: BorderRadius.circular(8),
                                        border: Border.all(
                                          color: AppTheme.divider,
                                        ),
                                      ),
                                      blockquoteDecoration: BoxDecoration(
                                        color: AppTheme.primary.withOpacity(
                                          0.04,
                                        ),
                                        borderRadius: BorderRadius.circular(4),
                                        border: Border(
                                          left: BorderSide(
                                            color: AppTheme.primary.withOpacity(
                                              0.5,
                                            ),
                                            width: 3,
                                          ),
                                        ),
                                      ),
                                    ),
                              ),
                              if (_post.locationLabel != null) ...[
                                const SizedBox(height: 14),
                                _CampusMapBanner(
                                  locationLabel: _post.locationLabel!,
                                  onTap: _openCampusMap,
                                ),
                              ],
                              const SizedBox(height: 14),
                              Row(
                                children: [
                                  const Icon(
                                    Icons.person_outline_rounded,
                                    size: 14,
                                    color: AppTheme.textLight,
                                  ),
                                  const SizedBox(width: 4),
                                  Text(
                                    '@${_post.authorAlias}',
                                    style: const TextStyle(
                                      fontSize: 12,
                                      color: AppTheme.textLight,
                                    ),
                                  ),
                                  const SizedBox(width: 6),
                                  Expanded(
                                    child: Text(
                                      '· ${_post.collegeName}',
                                      style: const TextStyle(
                                        fontSize: 12,
                                        color: AppTheme.textLight,
                                      ),
                                      overflow: TextOverflow.ellipsis,
                                    ),
                                  ),
                                  const SizedBox(width: 8),
                                  GestureDetector(
                                    onTap: _upvotePost,
                                    child: AnimatedContainer(
                                      duration: const Duration(
                                        milliseconds: 200,
                                      ),
                                      padding: const EdgeInsets.symmetric(
                                        horizontal: 14,
                                        vertical: 7,
                                      ),
                                      decoration: BoxDecoration(
                                        color: _post.hasUpvoted
                                            ? AppTheme.primary
                                            : AppTheme.surface,
                                        borderRadius: BorderRadius.circular(20),
                                        border: Border.all(
                                          color: _post.hasUpvoted
                                              ? AppTheme.primary
                                              : AppTheme.divider,
                                        ),
                                      ),
                                      child: Row(
                                        mainAxisSize: MainAxisSize.min,
                                        children: [
                                          Icon(
                                            Icons.arrow_upward_rounded,
                                            size: 15,
                                            color: _post.hasUpvoted
                                                ? AppTheme.textOnPrimary
                                                : AppTheme.textSecondary,
                                          ),
                                          const SizedBox(width: 5),
                                          Text(
                                            '${_post.upvotes}',
                                            style: TextStyle(
                                              fontWeight: FontWeight.w700,
                                              fontSize: 13,
                                              color: _post.hasUpvoted
                                                  ? AppTheme.textOnPrimary
                                                  : AppTheme.textSecondary,
                                            ),
                                          ),
                                          const SizedBox(width: 4),
                                          Text(
                                            'Upvote',
                                            style: TextStyle(
                                              fontSize: 12,
                                              color: _post.hasUpvoted
                                                  ? AppTheme.textOnPrimary
                                                  : AppTheme.textSecondary,
                                            ),
                                          ),
                                        ],
                                      ),
                                    ),
                                  ),
                                ],
                              ),
                            ],
                          ),
                        ),
                      ],
                    ),
                  ),
                  const SizedBox(height: 24),
                  Row(
                    children: [
                      const Text(
                        'Answers',
                        style: TextStyle(
                          fontSize: 17,
                          fontWeight: FontWeight.w800,
                          color: AppTheme.textPrimary,
                        ),
                      ),
                      const SizedBox(width: 8),
                      Container(
                        padding: const EdgeInsets.symmetric(
                          horizontal: 8,
                          vertical: 2,
                        ),
                        decoration: BoxDecoration(
                          color: AppTheme.divider,
                          borderRadius: BorderRadius.circular(10),
                        ),
                        child: Text(
                          '${_post.answerCount}',
                          style: const TextStyle(
                            fontSize: 12,
                            fontWeight: FontWeight.w700,
                            color: AppTheme.textSecondary,
                          ),
                        ),
                      ),
                    ],
                  ),
                  const SizedBox(height: 16),
                  commentsAsync.when(
                    data: (comments) {
                      if (comments.isEmpty) {
                        return Center(
                          child: Padding(
                            padding: const EdgeInsets.symmetric(vertical: 40),
                            child: Column(
                              children: [
                                Icon(
                                  Icons.chat_bubble_outline_rounded,
                                  size: 40,
                                  color: AppTheme.textLight.withOpacity(0.5),
                                ),
                                const SizedBox(height: 12),
                                const Text(
                                  'No answers yet. Be the first!',
                                  style: TextStyle(color: AppTheme.textLight),
                                ),
                              ],
                            ),
                          ),
                        );
                      }
                      return ListView.separated(
                        shrinkWrap: true,
                        physics: const NeverScrollableScrollPhysics(),
                        itemCount: comments.length,
                        separatorBuilder: (c, i) => const SizedBox(height: 12),
                        itemBuilder: (c, i) {
                          final comment = comments[i];
                          return _CommentCard(comment: comment);
                        },
                      );
                    },
                    loading: () => const SkeletonCommentList(),
                    error: (e, s) => Center(child: Text('Error: $e')),
                  ),
                  const SizedBox(height: 100),
                ],
              ),
            ),
          ),
          Container(
            padding: EdgeInsets.fromLTRB(
              16,
              12,
              16,
              12 + MediaQuery.of(context).viewInsets.bottom,
            ),
            decoration: BoxDecoration(
              color: Colors.white,
              boxShadow: [
                BoxShadow(
                  color: Colors.black.withOpacity(0.05),
                  blurRadius: 10,
                  offset: const Offset(0, -5),
                ),
              ],
            ),
            child: Row(
              children: [
                Expanded(
                  child: TextField(
                    controller: _answerCtrl,
                    decoration: InputDecoration(
                      hintText: 'Add an answer...',
                      filled: true,
                      fillColor: AppTheme.surface,
                      contentPadding: const EdgeInsets.symmetric(
                        horizontal: 16,
                        vertical: 10,
                      ),
                      border: OutlineInputBorder(
                        borderRadius: BorderRadius.circular(24),
                        borderSide: BorderSide.none,
                      ),
                    ),
                  ),
                ),
                const SizedBox(width: 8),
                IconButton.filled(
                  onPressed: _submitting ? null : _submitAnswer,
                  icon: _submitting
                      ? const SizedBox(
                          width: 18,
                          height: 18,
                          child: CircularProgressIndicator(
                            strokeWidth: 2,
                            color: Colors.white,
                          ),
                        )
                      : const Icon(Icons.send_rounded),
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }
}

class _CampusMapBanner extends StatelessWidget {
  final String locationLabel;
  final VoidCallback onTap;

  const _CampusMapBanner({required this.locationLabel, required this.onTap});

  @override
  Widget build(BuildContext context) {
    return InkWell(
      onTap: onTap,
      borderRadius: BorderRadius.circular(12),
      child: Container(
        padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 10),
        decoration: BoxDecoration(
          color: AppTheme.primary.withOpacity(0.06),
          borderRadius: BorderRadius.circular(12),
          border: Border.all(color: AppTheme.primary.withOpacity(0.15)),
        ),
        child: Row(
          children: [
            const Icon(
              Icons.location_on_rounded,
              color: AppTheme.primary,
              size: 20,
            ),
            const SizedBox(width: 8),
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  const Text(
                    'Location Tagged',
                    style: TextStyle(
                      fontSize: 11,
                      fontWeight: FontWeight.w600,
                      color: AppTheme.primary,
                    ),
                  ),
                  Text(
                    locationLabel,
                    style: const TextStyle(
                      fontSize: 13,
                      fontWeight: FontWeight.w700,
                      color: AppTheme.textPrimary,
                    ),
                    maxLines: 1,
                    overflow: TextOverflow.ellipsis,
                  ),
                ],
              ),
            ),
            const Icon(Icons.map_outlined, color: AppTheme.primary, size: 18),
          ],
        ),
      ),
    );
  }
}

class _CommentCard extends StatelessWidget {
  final Comment comment;
  const _CommentCard({required this.comment});

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.all(12),
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(12),
        border: Border.all(color: AppTheme.divider),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              Text(
                '@${comment.authorAlias}',
                style: const TextStyle(
                  fontSize: 12,
                  fontWeight: FontWeight.w700,
                  color: AppTheme.textPrimary,
                ),
              ),
              const Spacer(),
              Text(
                timeago.format(comment.createdAt),
                style: const TextStyle(fontSize: 11, color: AppTheme.textLight),
              ),
            ],
          ),
          const SizedBox(height: 6),
          Text(
            comment.body,
            style: const TextStyle(fontSize: 14, color: AppTheme.textPrimary),
          ),
        ],
      ),
    );
  }
}
