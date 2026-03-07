import 'package:campusassist/core/interceptors/auth_interceptor.dart';
import 'package:campusassist/core/server_constants.dart';
import 'package:campusassist/models/post_model.dart';
import 'package:campusassist/repositories/attachment_remote_repository.dart';
import 'package:dio/dio.dart';
import 'package:flutter/foundation.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:image_picker/image_picker.dart';

final postDioProvider = Provider<Dio>((ref) {
  final dio = Dio(
    BaseOptions(
      baseUrl: ServerConstants.baseURL,
      connectTimeout: const Duration(seconds: 10),
      receiveTimeout: const Duration(seconds: 10),
    ),
  );
  dio.interceptors.add(AuthInterceptor(ref));
  return dio;
});

final postRemoteRepositoryProvider = Provider<PostRemoteRepository>((ref) {
  return PostRemoteRepository(
    ref.read(postDioProvider),
    ref.read(attachmentRemoteRepositoryProvider),
  );
});

class PostRemoteRepository {
  final Dio _dio;
  final AttachmentRemoteRepository _attachmentRepo;

  PostRemoteRepository(this._dio, this._attachmentRepo);

  /// GET /api/posts/community/{community_id}
  Future<List<Post>> getPostsByCommunity(
    String communityId, {
    int page = 1,
    int pageSize = 20,
    String? category,
  }) async {
    try {
      debugPrint('[PostRepo] GET /posts/community/$communityId page=$page');
      final response = await _dio.get<Map<String, dynamic>>(
        '/posts/community/$communityId',
        queryParameters: {'page': page, 'page_size': pageSize},
      );
      final raw = response.data!;
      final posts =
          (raw['items'] ?? raw['posts'] ?? raw['data'] ?? []) as List<dynamic>;
      debugPrint('[PostRepo] getPostsByCommunity → ${posts.length} posts');
      return posts
          .map((e) => Post.fromJson(e as Map<String, dynamic>))
          .toList();
    } on DioException catch (e) {
      throw _mapDioError(e);
    }
  }

  /// GET /api/posts/community/{community_id} — used as a fallback feed.
  /// The API has no global feed endpoint; this returns the most recent posts
  /// from the first community the user belongs to, or an empty list.
  Future<List<Post>> getFeed({
    int page = 1,
    int pageSize = 20,
    String? category,
  }) async {
    // The Post service has no /api/posts/feed endpoint.
    // Return empty list — callers show the "No posts yet" empty state.
    return [];
  }

  /// GET /api/posts/{post_id}
  Future<Post> getPostById(String postId) async {
    try {
      final response = await _dio.get<Map<String, dynamic>>('/posts/$postId');
      return Post.fromJson(response.data!);
    } on DioException catch (e) {
      throw _mapDioError(e);
    }
  }

  /// GET /api/comments/post/{post_id}?community_id=...
  Future<List<Comment>> getComments(
    String postId, {
    String communityId = '',
  }) async {
    try {
      debugPrint(
        '[PostRepo] GET /comments/post/$postId communityId=$communityId',
      );
      final response = await _dio.get<Map<String, dynamic>>(
        '/comments/post/$postId',
        queryParameters: {
          if (communityId.isNotEmpty) 'community_id': communityId,
        },
      );
      final raw = response.data!;
      debugPrint('[PostRepo] getComments raw response: $raw');
      final comments =
          (raw['items'] ?? raw['comments'] ?? raw['data'] ?? [])
              as List<dynamic>;
      debugPrint('[PostRepo] getComments → ${comments.length} comments');
      return comments
          .map((e) => Comment.fromJson(e as Map<String, dynamic>))
          .toList();
    } on DioException catch (e) {
      throw _mapDioError(e);
    }
  }

  /// POST /api/posts
  /// Step 1: Upload each [XFile] via POST /api/attachments/upload.
  /// Step 2: POST /api/posts with the returned attachment IDs.
  ///
  /// [onFileProgress] is called with (fileIndex, bytesSent, totalBytes)
  /// so callers can show per-file upload progress.
  Future<Post> createPost({
    required String communityId,
    required String content,
    String category = 'general',
    String? locationLabel,
    double? locationLat,
    double? locationLng,
    List<XFile> attachments = const [],
    void Function(int fileIndex, int sent, int total)? onFileProgress,
  }) async {
    try {
      // Step 1 — upload files and collect their IDs.
      List<String> attachmentIds = [];
      if (attachments.isNotEmpty) {
        final uploaded = await _attachmentRepo.uploadFiles(
          attachments,
          onFileProgress: onFileProgress,
        );
        attachmentIds = uploaded.map((a) => a.id).toList();
      }

      // Step 2 — create the post.
      // The API only accepts community_id, content, attachments.
      debugPrint(
        '[PostRepo] POST /posts communityId=$communityId attachments=${attachmentIds.length}',
      );
      final response = await _dio.post<Map<String, dynamic>>(
        '/posts',
        data: {
          'community_id': communityId,
          'content': content,
          if (attachmentIds.isNotEmpty) 'attachments': attachmentIds,
          if (locationLabel != null) 'location_label': locationLabel,
          if (locationLat != null) 'location_lat': locationLat,
          if (locationLng != null) 'location_lng': locationLng,
        },
      );
      debugPrint('[PostRepo] createPost → id=${response.data!['id']}');
      return Post.fromJson(response.data!);
    } on DioException catch (e) {
      if (e.type == DioExceptionType.badResponse &&
          e.response?.statusCode == 403) {
        throw Exception('You must be a member of this community to post.');
      }
      throw _mapDioError(e);
    }
  }

  /// PATCH /api/posts/{post_id}
  Future<Post> updatePost(String postId, {String? content}) async {
    try {
      final response = await _dio.patch<Map<String, dynamic>>(
        '/posts/$postId',
        data: {if (content != null) 'content': content},
      );
      return Post.fromJson(response.data!);
    } on DioException catch (e) {
      throw _mapDioError(e);
    }
  }

  /// DELETE /api/posts/{post_id}
  Future<void> deletePost(String postId) async {
    try {
      await _dio.delete('/posts/$postId');
    } on DioException catch (e) {
      throw _mapDioError(e);
    }
  }

  /// POST /api/posts/{post_id}/like — idempotent (add like)
  /// DELETE /api/posts/{post_id}/like — idempotent (remove like)
  /// [hasUpvoted] is the CURRENT state before the toggle.
  /// Returns (likes, liked) from the server's LikePostResponse.
  Future<({int likes, bool liked})> likePost(
    String postId, {
    bool hasUpvoted = false,
  }) async {
    try {
      late Response<Map<String, dynamic>> response;
      if (hasUpvoted) {
        debugPrint('[PostRepo] DELETE /posts/$postId/like (unlike)');
        response = await _dio.delete('/posts/$postId/like');
      } else {
        debugPrint('[PostRepo] POST /posts/$postId/like (like)');
        response = await _dio.post('/posts/$postId/like');
      }
      final data = response.data ?? {};
      final likes = data['likes'] as int? ?? data['like_count'] as int? ?? 0;
      // Server may return 'liked', 'liked_by_me', or nothing
      final bool liked;
      if (data.containsKey('liked')) {
        liked = data['liked'] as bool? ?? !hasUpvoted;
      } else if (data.containsKey('liked_by_me')) {
        liked = data['liked_by_me'] as bool? ?? !hasUpvoted;
      } else {
        // No liked field — derive from the action we just took
        liked = !hasUpvoted;
      }
      debugPrint('[PostRepo] likePost → likes=$likes liked=$liked');
      return (likes: likes, liked: liked);
    } on DioException catch (e) {
      throw _mapDioError(e);
    }
  }

  /// POST /api/comments — create a comment on a post.
  Future<Comment> addComment(
    String postId,
    String body, {
    String communityId = '',
  }) async {
    try {
      debugPrint(
        '[PostRepo] POST /comments postId=$postId communityId=$communityId',
      );
      final response = await _dio.post<Map<String, dynamic>>(
        '/comments',
        data: {
          'post_id': postId,
          if (communityId.isNotEmpty) 'community_id': communityId,
          'content': body,
        },
      );
      return Comment.fromJson(response.data!);
    } on DioException catch (e) {
      throw _mapDioError(e);
    }
  }

  /// DELETE /api/comments/{comment_id}
  Future<void> deleteComment(String postId, String commentId) async {
    try {
      debugPrint('[PostRepo] DELETE /comments/$commentId');
      await _dio.delete('/comments/$commentId');
    } on DioException catch (e) {
      throw _mapDioError(e);
    }
  }

  Exception _mapDioError(DioException e) {
    final status = e.response?.statusCode;
    final message =
        (e.response?.data is Map
            ? (e.response!.data as Map)['detail']
            : null) ??
        e.message ??
        'Something went wrong';
    if (status == 404) return Exception('Not found');
    if (status == 401 || status == 403) return Exception('Unauthorized');
    if (e.type == DioExceptionType.connectionTimeout ||
        e.type == DioExceptionType.receiveTimeout ||
        e.type == DioExceptionType.connectionError) {
      return Exception('No internet connection');
    }
    return Exception(message);
  }
}
