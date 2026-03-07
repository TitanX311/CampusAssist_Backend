// lib/viewmodel/post_viewmodel.dart
import 'dart:async';

import 'package:campusassist/models/post_model.dart';
import 'package:campusassist/repositories/community_remote_repository.dart';
import 'package:campusassist/repositories/feed_repository.dart';
import 'package:campusassist/repositories/post_remote_repository.dart';
import 'package:campusassist/viewmodel/auth_viewmodel.dart';
import 'package:flutter/foundation.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_riverpod/legacy.dart';
import 'package:image_picker/image_picker.dart';

// ── Session Likes ─────────────────────────────────────────────────────────────

/// Maps postId -> true (liked) / false (unliked) for this session.
final sessionLikesProvider = StateProvider<Map<String, bool>>((ref) => {});

// ── User Name Cache ───────────────────────────────────────────────────────────

/// Global in-session cache: userId → (name, pictureUrl?)
final _userNameCache = <String, ({String name, String? picture})>{};

/// Ensures real user_name/user_picture are in [_userNameCache] for every
/// post in [posts].  The current user is seeded instantly from [currentUser]
/// with no network call; every other unique userId triggers exactly one
/// GET /api/posts/{id} call (the first post we have for that user).
Future<void> _warmUserCache({
  required List<Post> posts,
  required PostRemoteRepository repo,
  String? currentUserId,
  String? currentUserName,
  String? currentUserPicture,
}) async {
  if (currentUserId != null &&
      currentUserName != null &&
      !_userNameCache.containsKey(currentUserId)) {
    _userNameCache[currentUserId] = (
      name: currentUserName,
      picture: currentUserPicture,
    );
    debugPrint(
      '[UserCache] seeded current user $currentUserId → $currentUserName',
    );
  }

  final Map<String, String> unknownUserIdToPostId = {};
  for (final post in posts) {
    if (post.userId.isEmpty) continue;
    if (_userNameCache.containsKey(post.userId)) continue;
    unknownUserIdToPostId.putIfAbsent(post.userId, () => post.id);
  }

  if (unknownUserIdToPostId.isEmpty) return;

  debugPrint(
    '[UserCache] fetching names for ${unknownUserIdToPostId.length} unknown users',
  );

  await Future.wait(
    unknownUserIdToPostId.entries.map((entry) async {
      try {
        final full = await repo.getPostById(entry.value);
        _userNameCache[entry.key] = (
          name: full.authorAlias,
          picture: full.authorPicture,
        );
        debugPrint('[UserCache] ${entry.key} → ${full.authorAlias}');
      } catch (e) {
        debugPrint('[UserCache] failed for ${entry.key}: $e');
      }
    }),
  );
}

/// Replace UUID-prefix aliases on posts with real names from [_userNameCache].
List<Post> _applyUserCache(List<Post> posts) {
  final uuidPrefixRe = RegExp(r'^[0-9a-f]{8}$');
  return posts.map((p) {
    final cached = _userNameCache[p.userId];
    if (cached == null) return p;
    if (!uuidPrefixRe.hasMatch(p.authorAlias)) return p;
    return Post(
      id: p.id,
      content: p.content,
      attachments: p.attachments,
      authorAlias: cached.name,
      authorPicture: cached.picture ?? p.authorPicture,
      userId: p.userId,
      communityId: p.communityId,
      collegeId: p.collegeId,
      collegeName: p.collegeName,
      category: p.category,
      upvotes: p.upvotes,
      hasUpvoted: p.hasUpvoted,
      answerCount: p.answerCount,
      views: p.views,
      createdAt: p.createdAt,
      locationLabel: p.locationLabel,
      locationLat: p.locationLat,
      locationLng: p.locationLng,
    );
  }).toList();
}

// ── Community post list ───────────────────────────────────────────────────────

final _postListProviderCache =
    <String, AsyncNotifierProvider<PostListNotifier, List<Post>>>{};

AsyncNotifierProvider<PostListNotifier, List<Post>> postListProvider(
  String communityId,
) {
  return _postListProviderCache.putIfAbsent(
    communityId,
    () => AsyncNotifierProvider<PostListNotifier, List<Post>>(
      () => PostListNotifier(communityId),
    ),
  );
}

class PostListNotifier extends AsyncNotifier<List<Post>> {
  final String communityId;
  PostListNotifier(this.communityId);

  PostRemoteRepository get _repo => ref.read(postRemoteRepositoryProvider);

  @override
  Future<List<Post>> build() => _repo.getPostsByCommunity(communityId);

  Future<void> refresh({String? category}) async {
    state = const AsyncLoading();
    state = await AsyncValue.guard(
      () => _repo.getPostsByCommunity(communityId, category: category),
    );
  }

  Future<Post> createPost({
    required String content,
    String category = 'general',
    String? locationLabel,
    double? locationLat,
    double? locationLng,
    List<XFile> attachments = const [],
    void Function(int fileIndex, int sent, int total)? onFileProgress,
  }) async {
    final post = await _repo.createPost(
      communityId: communityId,
      content: content,
      category: category,
      locationLabel: locationLabel,
      locationLat: locationLat,
      locationLng: locationLng,
      attachments: attachments,
      onFileProgress: onFileProgress,
    );
    state = state.whenData((posts) => [post, ...posts]);
    ref.read(feedProvider.notifier).prependPost(post);
    ref.read(globalFeedProvider.notifier).prependPost(post);
    return post;
  }

  Future<void> deletePost(String postId) async {
    await _repo.deletePost(postId);
    state = state.whenData(
      (posts) => posts.where((p) => p.id != postId).toList(),
    );
  }

  Future<void> toggleLike(String postId) async {
    final posts = state.value ?? [];
    final idx = posts.indexWhere((p) => p.id == postId);
    if (idx == -1) return;
    final wasUpvoted = posts[idx].hasUpvoted;
    _applyLike(
      postId,
      likes: wasUpvoted ? posts[idx].upvotes - 1 : posts[idx].upvotes + 1,
      liked: !wasUpvoted,
    );
    try {
      final result = await _repo.likePost(postId, hasUpvoted: wasUpvoted);
      _applyLike(postId, likes: result.likes, liked: result.liked);
      ref
          .read(sessionLikesProvider.notifier)
          .update((m) => {...m, postId: result.liked});
      ref
          .read(feedProvider.notifier)
          .syncLike(postId, result.likes, result.liked);
      ref
          .read(globalFeedProvider.notifier)
          .syncLike(postId, result.likes, result.liked);
    } catch (_) {
      _applyLike(postId, likes: posts[idx].upvotes, liked: wasUpvoted);
    }
  }

  void syncLike(String postId, int likes, bool liked) {
    _applyLike(postId, likes: likes, liked: liked);
    ref
        .read(sessionLikesProvider.notifier)
        .update((m) => {...m, postId: liked});
  }

  void syncLikeFromDetail(
    String postId, {
    required int likes,
    required bool liked,
  }) => syncLike(postId, likes, liked);

  void _applyLike(String postId, {required int likes, required bool liked}) {
    state = state.whenData(
      (posts) => posts
          .map(
            (p) => p.id == postId
                ? p.copyWith(upvotes: likes, hasUpvoted: liked)
                : p,
          )
          .toList(),
    );
  }

  Future<Post> updatePost(String postId, {String? content}) async {
    final updated = await _repo.updatePost(postId, content: content);
    state = state.whenData(
      (posts) => posts.map((p) => p.id == postId ? updated : p).toList(),
    );
    return updated;
  }
}

// ── Feed state ────────────────────────────────────────────────────────────────

class FeedState {
  final List<Post> posts;
  final int? nextCursor;
  final bool isLoadingMore;
  final bool hasMore;

  const FeedState({
    this.posts = const [],
    this.nextCursor,
    this.isLoadingMore = false,
    this.hasMore = true,
  });

  FeedState copyWith({
    List<Post>? posts,
    int? nextCursor,
    bool clearCursor = false,
    bool? isLoadingMore,
    bool? hasMore,
  }) => FeedState(
    posts: posts ?? this.posts,
    nextCursor: clearCursor ? null : (nextCursor ?? this.nextCursor),
    isLoadingMore: isLoadingMore ?? this.isLoadingMore,
    hasMore: hasMore ?? this.hasMore,
  );
}

// ── My Feed (/api/feed/my) ────────────────────────────────────────────────────

final feedProvider = AsyncNotifierProvider<FeedNotifier, FeedState>(
  FeedNotifier.new,
);

class FeedNotifier extends AsyncNotifier<FeedState> {
  FeedRepository get _feedRepo => ref.read(feedRepositoryProvider);
  CommunityRemoteRepository get _communityRepo =>
      ref.read(communityRemoteRepositoryProvider);
  PostRemoteRepository get _postRepo => ref.read(postRemoteRepositoryProvider);

  final _nameCache = <String, String>{};

  String? get _userType => ref.read(authViewModelProvider).value?.userType;

  @override
  Future<FeedState> build() {
    debugPrint('[FeedNotifier] build() userType=$_userType');
    if (_userType != null && _userType != 'USER') {
      return Future.value(const FeedState(hasMore: false));
    }
    return _load(cursor: 0, existing: const FeedState());
  }

  Future<FeedState> _load({
    required int cursor,
    required FeedState existing,
  }) async {
    if (_nameCache.isEmpty) {
      try {
        final communities = await _communityRepo.getMyCommunities();
        for (final c in communities) {
          _nameCache[c.id] = c.name;
        }
      } catch (_) {}
    }

    final page = await _feedRepo.getMyFeed(cursor: cursor, pageSize: 20);
    final sessionLikes = ref.read(sessionLikesProvider);

    debugPrint('[FeedNotifier] ══════ PARSED FEED ITEMS (My Feed) ══════');
    var newPosts = page.items.map((item) {
      final post = item.toPost(
        communityName: _nameCache[item.communityId] ?? '',
      );
      debugPrint(
        '[FeedNotifier]  post_id=${post.id}  '
        'likes=${post.upvotes}  hasUpvoted=${post.hasUpvoted}  '
        'authorAlias=${post.authorAlias}  userId=${post.userId}',
      );
      return post;
    }).toList();
    debugPrint('[FeedNotifier] ══════════════════════════════════════════');

    // Resolve real usernames (1 GET /posts/{id} per unique unknown userId)
    final currentUser = ref.read(authViewModelProvider).value;
    await _warmUserCache(
      posts: newPosts,
      repo: _postRepo,
      currentUserId: currentUser?.id,
      currentUserName: currentUser?.name,
      currentUserPicture: currentUser?.pictureURL,
    );
    newPosts = _applyUserCache(newPosts);

    var merged = cursor == 0 ? newPosts : [...existing.posts, ...newPosts];

    final seenIds = <String>{};
    var deduped = merged.where((p) => seenIds.add(p.id)).toList();

    // Re-apply session liked STATE (server owns count)
    deduped = deduped.map((p) {
      final s = sessionLikes[p.id];
      return s != null ? p.copyWith(hasUpvoted: s) : p;
    }).toList();

    deduped.sort((a, b) => b.upvotes.compareTo(a.upvotes));

    return FeedState(
      posts: deduped,
      nextCursor: page.nextCursor,
      hasMore: page.hasMore,
      isLoadingMore: false,
    );
  }

  Future<void> refresh() async {
    state = const AsyncLoading();
    await _feedRepo.invalidateMyCache();
    state = await AsyncValue.guard(
      () => _load(cursor: 0, existing: const FeedState()),
    );
  }

  Future<void> loadMore() async {
    final s = state.value;
    if (s == null || s.isLoadingMore || !s.hasMore || s.nextCursor == null)
      return;
    state = AsyncData(s.copyWith(isLoadingMore: true));
    try {
      final next = await _load(cursor: s.nextCursor!, existing: s);
      state = AsyncData(next);
    } catch (e) {
      state = AsyncData(s.copyWith(isLoadingMore: false));
    }
  }

  void prependPost(Post post) {
    state = state.whenData((s) {
      if (s.posts.any((p) => p.id == post.id)) return s;
      return s.copyWith(posts: [post, ...s.posts]);
    });
    _feedRepo.invalidateMyCache();
  }

  Future<void> toggleLike(String postId) async {
    final wasUpvoted = _getPost(postId)?.hasUpvoted ?? false;
    final currentUpvotes = _getPost(postId)?.upvotes ?? 0;
    _applyLike(
      postId,
      likes: wasUpvoted ? currentUpvotes - 1 : currentUpvotes + 1,
      liked: !wasUpvoted,
    );
    try {
      final result = await ref
          .read(postRemoteRepositoryProvider)
          .likePost(postId, hasUpvoted: wasUpvoted);
      _applyLike(postId, likes: result.likes, liked: result.liked);
      ref
          .read(sessionLikesProvider.notifier)
          .update((m) => {...m, postId: result.liked});
      ref
          .read(globalFeedProvider.notifier)
          .syncLike(postId, result.likes, result.liked);
    } catch (_) {
      _applyLike(postId, likes: currentUpvotes, liked: wasUpvoted);
    }
  }

  void syncLike(String postId, int likes, bool liked) {
    _applyLike(postId, likes: likes, liked: liked);
    ref
        .read(sessionLikesProvider.notifier)
        .update((m) => {...m, postId: liked});
  }

  void syncLikeFromExternal(String postId, int likes, bool liked) =>
      syncLike(postId, likes, liked);
  void toggleLikeFromDetail(
    String postId, {
    required int likes,
    required bool liked,
  }) => syncLike(postId, likes, liked);

  Post? _getPost(String postId) =>
      state.value?.posts.where((p) => p.id == postId).firstOrNull;

  void _applyLike(String postId, {required int likes, required bool liked}) {
    state = state.whenData((s) {
      final updated =
          s.posts
              .map(
                (p) => p.id == postId
                    ? p.copyWith(upvotes: likes, hasUpvoted: liked)
                    : p,
              )
              .toList()
            ..sort((a, b) => b.upvotes.compareTo(a.upvotes));
      return s.copyWith(posts: updated);
    });
  }
}

// ── Across-India Feed (/api/feed/india) ───────────────────────────────────────

final globalFeedProvider = AsyncNotifierProvider<GlobalFeedNotifier, FeedState>(
  GlobalFeedNotifier.new,
);

class GlobalFeedNotifier extends AsyncNotifier<FeedState> {
  FeedRepository get _feedRepo => ref.read(feedRepositoryProvider);
  PostRemoteRepository get _postRepo => ref.read(postRemoteRepositoryProvider);

  String? get _userType => ref.read(authViewModelProvider).value?.userType;

  @override
  Future<FeedState> build() {
    debugPrint('[GlobalFeedNotifier] build() userType=$_userType');
    if (_userType != null && _userType != 'USER') {
      return Future.value(const FeedState(hasMore: false));
    }
    return _load(cursor: 0, existing: const FeedState());
  }

  Future<FeedState> _load({
    required int cursor,
    required FeedState existing,
  }) async {
    final page = await _feedRepo.getIndiaFeed(cursor: cursor, pageSize: 20);
    final sessionLikes = ref.read(sessionLikesProvider);

    debugPrint('[GlobalFeedNotifier] ══════ PARSED FEED ITEMS (India) ══════');
    var newPosts = page.items.map((item) {
      final post = item.toPost();
      debugPrint(
        '[GlobalFeedNotifier]  post_id=${post.id}  '
        'likes=${post.upvotes}  hasUpvoted=${post.hasUpvoted}  '
        'authorAlias=${post.authorAlias}  userId=${post.userId}',
      );
      return post;
    }).toList();
    debugPrint('[GlobalFeedNotifier] ════════════════════════════════════════');

    // Resolve real usernames
    final currentUser = ref.read(authViewModelProvider).value;
    await _warmUserCache(
      posts: newPosts,
      repo: _postRepo,
      currentUserId: currentUser?.id,
      currentUserName: currentUser?.name,
      currentUserPicture: currentUser?.pictureURL,
    );
    newPosts = _applyUserCache(newPosts);

    var merged = cursor == 0 ? newPosts : [...existing.posts, ...newPosts];

    final seenIds = <String>{};
    var deduped = merged.where((p) => seenIds.add(p.id)).toList();

    deduped = deduped.map((p) {
      final s = sessionLikes[p.id];
      return s != null ? p.copyWith(hasUpvoted: s) : p;
    }).toList();

    deduped.sort((a, b) => b.upvotes.compareTo(a.upvotes));

    return FeedState(
      posts: deduped,
      nextCursor: page.nextCursor,
      hasMore: page.hasMore,
      isLoadingMore: false,
    );
  }

  Future<void> refresh() async {
    state = const AsyncLoading();
    await _feedRepo.invalidateIndiaCache();
    state = await AsyncValue.guard(
      () => _load(cursor: 0, existing: const FeedState()),
    );
  }

  Future<void> loadMore() async {
    final s = state.value;
    if (s == null || s.isLoadingMore || !s.hasMore || s.nextCursor == null)
      return;
    state = AsyncData(s.copyWith(isLoadingMore: true));
    try {
      final next = await _load(cursor: s.nextCursor!, existing: s);
      state = AsyncData(next);
    } catch (e) {
      state = AsyncData(s.copyWith(isLoadingMore: false));
    }
  }

  void prependPost(Post post) {
    state = state.whenData((s) {
      if (s.posts.any((p) => p.id == post.id)) return s;
      return s.copyWith(posts: [post, ...s.posts]);
    });
  }

  Future<void> toggleLike(String postId) async {
    final wasUpvoted = _getPost(postId)?.hasUpvoted ?? false;
    final currentUpvotes = _getPost(postId)?.upvotes ?? 0;
    _applyLike(
      postId,
      likes: wasUpvoted ? currentUpvotes - 1 : currentUpvotes + 1,
      liked: !wasUpvoted,
    );
    try {
      final result = await ref
          .read(postRemoteRepositoryProvider)
          .likePost(postId, hasUpvoted: wasUpvoted);
      _applyLike(postId, likes: result.likes, liked: result.liked);
      ref
          .read(sessionLikesProvider.notifier)
          .update((m) => {...m, postId: result.liked});
      ref
          .read(feedProvider.notifier)
          .syncLike(postId, result.likes, result.liked);
    } catch (_) {
      _applyLike(postId, likes: currentUpvotes, liked: wasUpvoted);
    }
  }

  void syncLike(String postId, int likes, bool liked) {
    _applyLike(postId, likes: likes, liked: liked);
    ref
        .read(sessionLikesProvider.notifier)
        .update((m) => {...m, postId: liked});
  }

  void syncLikeFromExternal(String postId, int likes, bool liked) =>
      syncLike(postId, likes, liked);
  void toggleLikeFromDetail(
    String postId, {
    required int likes,
    required bool liked,
  }) => syncLike(postId, likes, liked);

  Post? _getPost(String postId) =>
      state.value?.posts.where((p) => p.id == postId).firstOrNull;

  void _applyLike(String postId, {required int likes, required bool liked}) {
    state = state.whenData((s) {
      final updated =
          s.posts
              .map(
                (p) => p.id == postId
                    ? p.copyWith(upvotes: likes, hasUpvoted: liked)
                    : p,
              )
              .toList()
            ..sort((a, b) => b.upvotes.compareTo(a.upvotes));
      return s.copyWith(posts: updated);
    });
  }
}

// ── Comments ──────────────────────────────────────────────────────────────────

final _commentsProviderCache =
    <
      (String, String),
      AsyncNotifierProvider<CommentsNotifier, List<Comment>>
    >{};

AsyncNotifierProvider<CommentsNotifier, List<Comment>> commentsProvider({
  required String postId,
  required String communityId,
}) {
  return _commentsProviderCache.putIfAbsent(
    (postId, communityId),
    () => AsyncNotifierProvider<CommentsNotifier, List<Comment>>(
      () => CommentsNotifier(postId: postId, communityId: communityId),
    ),
  );
}

class CommentsNotifier extends AsyncNotifier<List<Comment>> {
  final String postId;
  final String communityId;

  CommentsNotifier({required this.postId, required this.communityId});

  PostRemoteRepository get _repo => ref.read(postRemoteRepositoryProvider);

  @override
  Future<List<Comment>> build() =>
      _repo.getComments(postId, communityId: communityId);

  Future<void> refresh() async {
    state = const AsyncLoading();
    state = await AsyncValue.guard(
      () => _repo.getComments(postId, communityId: communityId),
    );
  }

  Future<Comment> addComment(String body) async {
    final comment = await _repo.addComment(
      postId,
      body,
      communityId: communityId,
    );
    state = state.whenData((list) => [comment, ...list]);
    return comment;
  }

  Future<void> deleteComment(String commentId) async {
    await _repo.deleteComment(postId, commentId);
    state = state.whenData(
      (list) => list.where((c) => c.id != commentId).toList(),
    );
  }
}
