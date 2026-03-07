// lib/models/post_model.dart

enum PostCategory {
  academics,
  hostel,
  facilities,
  food,
  career,
  events,
  general,
}

extension PostCategoryExtension on PostCategory {
  String get label {
    switch (this) {
      case PostCategory.academics:
        return 'Academics';
      case PostCategory.hostel:
        return 'Hostel';
      case PostCategory.facilities:
        return 'Facilities';
      case PostCategory.food:
        return 'Food';
      case PostCategory.career:
        return 'Career';
      case PostCategory.events:
        return 'Events';
      case PostCategory.general:
        return 'General';
    }
  }
}

class Post {
  final String id;
  final String content;
  final List<String> attachments; // attachment UUIDs
  final String authorAlias; // user_name from API (or anonymized handle)
  final String? authorPicture; // user_picture from API
  final String userId; // user_id from API
  final String communityId;
  final String collegeId;
  final String collegeName;
  final PostCategory category;
  final int upvotes; // maps to 'likes' in API
  final bool hasUpvoted; // maps to 'liked_by_me' in API
  final int answerCount; // maps to 'comment_count' in API
  final int views;
  final DateTime createdAt;
  final String? locationLabel; // selected campus landmark label
  final double? locationLat; // latitude of the picked location
  final double? locationLng; // longitude of the picked location

  const Post({
    required this.id,
    required this.content,
    this.attachments = const [],
    required this.authorAlias,
    this.authorPicture,
    this.userId = '',
    this.communityId = '',
    this.collegeId = '',
    this.collegeName = '',
    required this.category,
    this.upvotes = 0,
    this.hasUpvoted = false,
    this.answerCount = 0,
    this.views = 0,
    required this.createdAt,
    this.locationLabel,
    this.locationLat,
    this.locationLng,
  });

  Post copyWith({
    int? upvotes,
    bool? hasUpvoted,
    int? answerCount,
    int? views,
  }) => Post(
    id: id,
    content: content,
    attachments: attachments,
    authorAlias: authorAlias,
    authorPicture: authorPicture,
    userId: userId,
    communityId: communityId,
    collegeId: collegeId,
    collegeName: collegeName,
    category: category,
    upvotes: upvotes ?? this.upvotes,
    hasUpvoted: hasUpvoted ?? this.hasUpvoted,
    answerCount: answerCount ?? this.answerCount,
    views: views ?? this.views,
    createdAt: createdAt,
    locationLabel: locationLabel,
    locationLat: locationLat,
    locationLng: locationLng,
  );

  factory Post.fromJson(Map<String, dynamic> json) => Post(
    id: json['id'] as String,
    content: json['content'] as String? ?? '',
    // attachments is a list of UUIDs from the API
    attachments: (json['attachments'] as List<dynamic>? ?? []).cast<String>(),
    // API returns user_name; fall back to user_id prefix for anonymous display
    authorAlias:
        json['user_name'] as String? ??
        (json['user_id'] as String? ?? '').substring(
          0,
          8.clamp(0, (json['user_id'] as String? ?? '').length),
        ),
    authorPicture: json['user_picture'] as String?,
    userId: json['user_id'] as String? ?? '',
    communityId: json['community_id'] as String? ?? '',
    // college_id / college_name not in PostResponse — keep defaults
    collegeId: json['college_id'] as String? ?? '',
    collegeName: json['college_name'] as String? ?? '',
    category: PostCategory.values.firstWhere(
      (e) => e.name == (json['category'] as String?),
      orElse: () => PostCategory.general,
    ),
    upvotes: json['likes'] as int? ?? json['upvotes'] as int? ?? 0,
    hasUpvoted:
        json['liked_by_me'] as bool? ?? json['has_upvoted'] as bool? ?? false,
    answerCount:
        json['comment_count'] as int? ?? json['answer_count'] as int? ?? 0,
    views: json['views'] as int? ?? 0,
    createdAt: DateTime.parse(json['created_at'] as String),
    locationLabel: json['location_label'] as String?,
    locationLat: (json['location_lat'] as num?)?.toDouble(),
    locationLng: (json['location_lng'] as num?)?.toDouble(),
  );

  Map<String, dynamic> toJson() => {
    'id': id,
    'content': content,
    'attachments': attachments,
    'user_name': authorAlias,
    'user_picture': authorPicture,
    'user_id': userId,
    'community_id': communityId,
    'college_id': collegeId,
    'college_name': collegeName,
    'category': category.name,
    'likes': upvotes,
    'liked_by_me': hasUpvoted,
    'comment_count': answerCount,
    'views': views,
    'created_at': createdAt.toIso8601String(),
    'location_label': locationLabel,
    if (locationLat != null) 'location_lat': locationLat,
    if (locationLng != null) 'location_lng': locationLng,
  };
}

class Answer {
  final String id;
  final String postId;
  final String body;
  final String authorAlias;
  final int upvotes;
  final bool hasUpvoted;
  final DateTime createdAt;

  const Answer({
    required this.id,
    required this.postId,
    required this.body,
    required this.authorAlias,
    this.upvotes = 0,
    this.hasUpvoted = false,
    required this.createdAt,
  });

  Answer copyWith({int? upvotes, bool? hasUpvoted}) => Answer(
    id: id,
    postId: postId,
    body: body,
    authorAlias: authorAlias,
    upvotes: upvotes ?? this.upvotes,
    hasUpvoted: hasUpvoted ?? this.hasUpvoted,
    createdAt: createdAt,
  );
}

/// Maps to the API comment shape for /api/comments
class Comment {
  final String id;
  final String postId;
  final String userId;
  final String communityId;
  final String? parentId;
  final String body; // maps to 'content' in API
  final String authorAlias; // maps to 'user_name' in API
  final String? authorPicture; // maps to 'user_picture' in API
  final int likes;
  final bool likedByMe;
  final int replyCount;
  final DateTime createdAt;

  const Comment({
    required this.id,
    required this.postId,
    this.userId = '',
    this.communityId = '',
    this.parentId,
    required this.body,
    this.authorAlias = '',
    this.authorPicture,
    this.likes = 0,
    this.likedByMe = false,
    this.replyCount = 0,
    required this.createdAt,
  });

  Comment copyWith({int? likes, bool? likedByMe}) => Comment(
    id: id,
    postId: postId,
    userId: userId,
    communityId: communityId,
    parentId: parentId,
    body: body,
    authorAlias: authorAlias,
    authorPicture: authorPicture,
    likes: likes ?? this.likes,
    likedByMe: likedByMe ?? this.likedByMe,
    replyCount: replyCount,
    createdAt: createdAt,
  );

  factory Comment.fromJson(Map<String, dynamic> json) => Comment(
    id: json['id'] as String,
    postId: json['post_id'] as String? ?? '',
    userId: json['user_id'] as String? ?? '',
    communityId: json['community_id'] as String? ?? '',
    parentId: json['parent_id'] as String?,
    body: json['content'] as String? ?? json['body'] as String? ?? '',
    authorAlias:
        json['user_name'] as String? ?? json['author_alias'] as String? ?? '',
    authorPicture: json['user_picture'] as String?,
    likes: json['likes'] as int? ?? 0,
    likedByMe: json['liked_by_me'] as bool? ?? false,
    replyCount: json['reply_count'] as int? ?? 0,
    createdAt: DateTime.parse(json['created_at'] as String),
  );

  Map<String, dynamic> toJson() => {
    'id': id,
    'post_id': postId,
    'user_id': userId,
    'community_id': communityId,
    'parent_id': parentId,
    'content': body,
    'user_name': authorAlias,
    'user_picture': authorPicture,
    'likes': likes,
    'liked_by_me': likedByMe,
    'reply_count': replyCount,
    'created_at': createdAt.toIso8601String(),
  };
}
