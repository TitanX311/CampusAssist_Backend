// lib/models/feed_item_model.dart
//
// Maps the /api/feed/my  (FeedItem) and /api/feed/india (IndiaFeedItem)
// responses from the backend.  Both shapes are identical except IndiaFeedItem
// has no `seen` field.
//
// We convert a FeedItem → Post so we can reuse every existing widget (PostCard,
// PostDetailScreen, etc.) unchanged.

import 'package:campusassist/models/post_model.dart';

/// A single entry returned by the feed endpoints.
class FeedItem {
  final String postId;
  final String communityId;
  final String userId;
  final String userName; // user_name from API (display username)
  final String? userPicture; // user_picture from API (avatar URL)
  final String content;
  final int likes;
  final int views;
  final int commentCount;
  final List<String> attachments;
  final double score;
  final DateTime createdAt;
  final bool seen;
  final bool likedByMe;

  const FeedItem({
    required this.postId,
    required this.communityId,
    required this.userId,
    this.userName = '',
    this.userPicture,
    required this.content,
    required this.likes,
    required this.views,
    required this.commentCount,
    required this.attachments,
    required this.score,
    required this.createdAt,
    this.seen = false,
    this.likedByMe = false,
  });

  factory FeedItem.fromJson(Map<String, dynamic> json) {
    final userId = json['user_id'] as String? ?? '';
    // user_name may be absent from the feed API — fall back to first 8 chars of user_id
    final rawUserName = json['user_name'] as String?;
    final userName = (rawUserName != null && rawUserName.isNotEmpty)
        ? rawUserName
        : (userId.length >= 8 ? userId.substring(0, 8) : userId);

    return FeedItem(
      postId: json['post_id'] as String,
      communityId: json['community_id'] as String,
      userId: userId,
      userName: userName,
      userPicture: json['user_picture'] as String?,
      content: json['content'] as String? ?? '',
      likes: json['likes'] as int? ?? 0,
      views: json['views'] as int? ?? 0,
      commentCount: json['comment_count'] as int? ?? 0,
      attachments: (json['attachments'] as List<dynamic>? ?? []).cast<String>(),
      score: (json['score'] as num? ?? 0).toDouble(),
      createdAt: DateTime.parse(json['created_at'] as String),
      seen: json['seen'] as bool? ?? false,
      likedByMe: json['liked_by_me'] as bool? ?? false,
    );
  }

  /// Convert to the Post model used by all UI widgets.
  Post toPost({String communityName = ''}) => Post(
    id: postId,
    content: content,
    attachments: attachments,
    authorAlias: userName,
    authorPicture: userPicture,
    userId: userId,
    communityId: communityId,
    collegeId: '',
    collegeName: communityName,
    category: PostCategory.general,
    upvotes: likes,
    hasUpvoted: likedByMe,
    answerCount: commentCount,
    views: views,
    createdAt: createdAt,
  );
}

/// Paginated response from both feed endpoints.
class FeedPage {
  final List<FeedItem> items;
  final int? nextCursor;
  final int totalInCache;
  final bool builtFresh;

  const FeedPage({
    required this.items,
    this.nextCursor,
    required this.totalInCache,
    required this.builtFresh,
  });

  factory FeedPage.fromJson(Map<String, dynamic> json, {bool isIndia = false}) {
    final rawItems = json['items'] as List<dynamic>? ?? [];
    return FeedPage(
      items: rawItems
          .map((e) => FeedItem.fromJson(e as Map<String, dynamic>))
          .toList(),
      nextCursor: json['next_cursor'] != null
          ? int.tryParse(json['next_cursor'].toString())
          : null,
      totalInCache: json['total_in_cache'] as int? ?? 0,
      builtFresh: json['built_fresh'] as bool? ?? false,
    );
  }

  bool get hasMore => nextCursor != null;
}
