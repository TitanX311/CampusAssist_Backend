// lib/models/attachment_model.dart

class Attachment {
  final String id;
  final String uploaderUserId;
  final String filename;
  final String contentType; // MIME type (e.g. 'image/jpeg')
  final int size; // bytes
  final String bucket;
  final String objectKey;
  final DateTime createdAt;

  const Attachment({
    required this.id,
    this.uploaderUserId = '',
    required this.filename,
    required this.contentType,
    required this.size,
    this.bucket = '',
    this.objectKey = '',
    required this.createdAt,
  });

  /// Convenience getter for backward compatibility
  String get mimeType => contentType;

  factory Attachment.fromJson(Map<String, dynamic> json) => Attachment(
    id: json['id'] as String,
    uploaderUserId: json['uploader_user_id'] as String? ?? '',
    filename: json['filename'] as String? ?? '',
    contentType:
        json['content_type'] as String? ??
        json['mime_type'] as String? ??
        'application/octet-stream',
    size: json['size'] as int? ?? 0,
    bucket: json['bucket'] as String? ?? '',
    objectKey: json['object_key'] as String? ?? '',
    createdAt: DateTime.parse(
      json['created_at'] as String? ??
          json['uploaded_at'] as String? ??
          DateTime.now().toIso8601String(),
    ),
  );

  Map<String, dynamic> toJson() => {
    'id': id,
    'uploader_user_id': uploaderUserId,
    'filename': filename,
    'content_type': contentType,
    'size': size,
    'bucket': bucket,
    'object_key': objectKey,
    'created_at': createdAt.toIso8601String(),
  };
}
