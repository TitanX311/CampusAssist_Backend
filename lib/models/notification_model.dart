// lib/models/notification_model.dart

enum NotificationType {
  likePost,
  commentPost,
  likeComment,
  replyComment,
  joinRequest,
  joinAccepted,
  newPost,
  unknown;

  static NotificationType fromString(String v) => switch (v) {
    'LIKE_POST' => likePost,
    'COMMENT_POST' => commentPost,
    'LIKE_COMMENT' => likeComment,
    'REPLY_COMMENT' => replyComment,
    'JOIN_REQUEST' => joinRequest,
    'JOIN_ACCEPTED' => joinAccepted,
    'NEW_POST' => newPost,
    _ => unknown,
  };

  String get label => switch (this) {
    likePost => 'Liked your post',
    commentPost => 'Commented on your post',
    likeComment => 'Liked your answer',
    replyComment => 'Replied to your answer',
    joinRequest => 'Join request',
    joinAccepted => 'Join accepted',
    newPost => 'New post',
    unknown => 'Notification',
  };
}

class AppNotification {
  final String id;
  final String userId;
  final NotificationType type;
  final String title;
  final String body;
  final Map<String, dynamic>? data;
  final bool read;
  final DateTime createdAt;

  const AppNotification({
    required this.id,
    required this.userId,
    required this.type,
    required this.title,
    required this.body,
    this.data,
    required this.read,
    required this.createdAt,
  });

  AppNotification copyWith({bool? read}) => AppNotification(
    id: id,
    userId: userId,
    type: type,
    title: title,
    body: body,
    data: data,
    read: read ?? this.read,
    createdAt: createdAt,
  );

  factory AppNotification.fromJson(Map<String, dynamic> json) =>
      AppNotification(
        id: json['id'] as String,
        userId: json['user_id'] as String? ?? '',
        type: NotificationType.fromString(json['type'] as String? ?? ''),
        title: json['title'] as String? ?? '',
        body: json['body'] as String? ?? '',
        data: json['data'] as Map<String, dynamic>?,
        read: json['read'] as bool? ?? false,
        createdAt: DateTime.parse(json['created_at'] as String),
      );

  Map<String, dynamic> toJson() => {
    'id': id,
    'user_id': userId,
    'type': type.name,
    'title': title,
    'body': body,
    'data': data,
    'read': read,
    'created_at': createdAt.toIso8601String(),
  };
}
