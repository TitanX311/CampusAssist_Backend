// lib/repositories/feed_repository.dart
import 'package:campusassist/core/interceptors/auth_interceptor.dart';
import 'package:campusassist/core/server_constants.dart';
import 'package:campusassist/models/feed_item_model.dart';
import 'package:dio/dio.dart';
import 'package:flutter/foundation.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

final feedRepositoryProvider = Provider<FeedRepository>((ref) {
  // Trailing slash is required so Dio appends paths correctly:
  // baseUrl = "http://host/api/"  +  "feed/my"  → "http://host/api/feed/my"
  final dio = Dio(
    BaseOptions(
      baseUrl: '${ServerConstants.baseURL}/',
      connectTimeout: const Duration(seconds: 15),
      // Feed endpoint builds a Redis cache on first call — can take 30-60 s
      receiveTimeout: const Duration(seconds: 60),
    ),
  );
  dio.interceptors.add(AuthInterceptor(ref));
  return FeedRepository(dio);
});

class FeedRepository {
  final Dio _dio;

  FeedRepository(this._dio);

  /// GET /api/feed/my — personalised feed (cursor-based)
  Future<FeedPage> getMyFeed({int cursor = 0, int pageSize = 20}) async {
    try {
      debugPrint('[FeedRepo] baseUrl=${_dio.options.baseUrl}');
      debugPrint('[FeedRepo] GET /feed/my cursor=$cursor pageSize=$pageSize');
      final res = await _dio.get<Map<String, dynamic>>(
        'feed/my',
        queryParameters: {'cursor': cursor, 'page_size': pageSize},
      );

      // ── RAW RESPONSE DUMP ─────────────────────────────────────────────────
      debugPrint('[FeedRepo:my] ══════════════ RAW RESPONSE ══════════════');
      debugPrint('[FeedRepo:my] top-level keys: ${res.data?.keys.toList()}');
      debugPrint(
        '[FeedRepo:my] next_cursor=${res.data?['next_cursor']}  '
        'total_in_cache=${res.data?['total_in_cache']}  '
        'built_fresh=${res.data?['built_fresh']}',
      );
      final rawItems = res.data?['items'] as List<dynamic>? ?? [];
      debugPrint('[FeedRepo:my] item count: ${rawItems.length}');
      for (var i = 0; i < rawItems.length; i++) {
        final item = rawItems[i] as Map<String, dynamic>;
        debugPrint('[FeedRepo:my] ── item[$i] ──────────────────────────────');
        debugPrint('[FeedRepo:my]   post_id      = ${item['post_id']}');
        debugPrint('[FeedRepo:my]   community_id = ${item['community_id']}');
        debugPrint('[FeedRepo:my]   user_id      = ${item['user_id']}');
        debugPrint(
          '[FeedRepo:my]   user_name    = ${item['user_name']}  '
          '(present=${item.containsKey('user_name')})',
        );
        debugPrint(
          '[FeedRepo:my]   user_picture = ${item['user_picture']}  '
          '(present=${item.containsKey('user_picture')})',
        );
        debugPrint('[FeedRepo:my]   likes        = ${item['likes']}');
        debugPrint(
          '[FeedRepo:my]   liked_by_me  = ${item['liked_by_me']}  '
          '(present=${item.containsKey('liked_by_me')})',
        );
        debugPrint('[FeedRepo:my]   views        = ${item['views']}');
        debugPrint('[FeedRepo:my]   comment_count= ${item['comment_count']}');
        debugPrint('[FeedRepo:my]   score        = ${item['score']}');
        debugPrint('[FeedRepo:my]   seen         = ${item['seen']}');
        debugPrint(
          '[FeedRepo:my]   content      = '
          '${(item['content'] as String? ?? '').substring(0, ((item['content'] as String? ?? '').length).clamp(0, 80))}…',
        );
        debugPrint('[FeedRepo:my]   ALL KEYS     = ${item.keys.toList()}');
      }
      debugPrint('[FeedRepo:my] ════════════════════════════════════════════');
      // ─────────────────────────────────────────────────────────────────────

      return FeedPage.fromJson(res.data!, isIndia: false);
    } on DioException catch (e) {
      throw _mapError(e);
    }
  }

  /// GET /api/feed/india — across-India trending feed (cursor-based)
  Future<FeedPage> getIndiaFeed({int cursor = 0, int pageSize = 20}) async {
    try {
      debugPrint('[FeedRepo] baseUrl=${_dio.options.baseUrl}');
      debugPrint(
        '[FeedRepo] GET /feed/india cursor=$cursor pageSize=$pageSize',
      );
      final res = await _dio.get<Map<String, dynamic>>(
        'feed/india',
        queryParameters: {'cursor': cursor, 'page_size': pageSize},
      );

      // ── RAW RESPONSE DUMP ─────────────────────────────────────────────────
      debugPrint('[FeedRepo:india] ══════════════ RAW RESPONSE ══════════════');
      debugPrint('[FeedRepo:india] top-level keys: ${res.data?.keys.toList()}');
      debugPrint(
        '[FeedRepo:india] next_cursor=${res.data?['next_cursor']}  '
        'total_in_cache=${res.data?['total_in_cache']}  '
        'built_fresh=${res.data?['built_fresh']}',
      );
      final rawItemsIndia = res.data?['items'] as List<dynamic>? ?? [];
      debugPrint('[FeedRepo:india] item count: ${rawItemsIndia.length}');
      for (var i = 0; i < rawItemsIndia.length; i++) {
        final item = rawItemsIndia[i] as Map<String, dynamic>;
        debugPrint('[FeedRepo:india] ── item[$i] ───────────────────────────');
        debugPrint('[FeedRepo:india]   post_id      = ${item['post_id']}');
        debugPrint('[FeedRepo:india]   community_id = ${item['community_id']}');
        debugPrint('[FeedRepo:india]   user_id      = ${item['user_id']}');
        debugPrint(
          '[FeedRepo:india]   user_name    = ${item['user_name']}  '
          '(present=${item.containsKey('user_name')})',
        );
        debugPrint(
          '[FeedRepo:india]   user_picture = ${item['user_picture']}  '
          '(present=${item.containsKey('user_picture')})',
        );
        debugPrint('[FeedRepo:india]   likes        = ${item['likes']}');
        debugPrint(
          '[FeedRepo:india]   liked_by_me  = ${item['liked_by_me']}  '
          '(present=${item.containsKey('liked_by_me')})',
        );
        debugPrint('[FeedRepo:india]   views        = ${item['views']}');
        debugPrint(
          '[FeedRepo:india]   comment_count= ${item['comment_count']}',
        );
        debugPrint('[FeedRepo:india]   score        = ${item['score']}');
        debugPrint('[FeedRepo:india]   ALL KEYS     = ${item.keys.toList()}');
      }
      debugPrint(
        '[FeedRepo:india] ════════════════════════════════════════════',
      );
      // ─────────────────────────────────────────────────────────────────────

      return FeedPage.fromJson(res.data!, isIndia: true);
    } on DioException catch (e) {
      throw _mapError(e);
    }
  }

  /// POST /api/feed/seen/{post_id}
  Future<void> markSeen(String postId) async {
    try {
      debugPrint('[FeedRepo] POST /feed/seen/$postId');
      await _dio.post<void>('feed/seen/$postId');
    } on DioException catch (e) {
      debugPrint('[FeedRepo] markSeen error: $e');
    }
  }

  /// DELETE /api/feed/cache — invalidate my-feed cache
  Future<void> invalidateMyCache() async {
    try {
      debugPrint('[FeedRepo] DELETE /feed/cache');
      await _dio.delete<void>('feed/cache');
    } on DioException catch (e) {
      debugPrint('[FeedRepo] invalidateMyCache error: $e');
    }
  }

  /// DELETE /api/feed/india/cache
  Future<void> invalidateIndiaCache() async {
    try {
      debugPrint('[FeedRepo] DELETE /feed/india/cache');
      await _dio.delete<void>('feed/india/cache');
    } on DioException catch (e) {
      debugPrint('[FeedRepo] invalidateIndiaCache error: $e');
    }
  }

  Exception _mapError(DioException e) {
    debugPrint(
      '[FeedRepo] DioException type=${e.type} status=${e.response?.statusCode} msg=${e.message} error=${e.error}',
    );
    if (e.type == DioExceptionType.connectionError ||
        e.type == DioExceptionType.unknown) {
      return Exception(
        'Cannot reach server (${e.requestOptions.uri.host}:${e.requestOptions.uri.port}). '
        'Check that the backend is running and the device is on the same network.',
      );
    }
    if (e.type == DioExceptionType.receiveTimeout ||
        e.type == DioExceptionType.sendTimeout ||
        e.type == DioExceptionType.connectionTimeout) {
      return Exception(
        'Server is taking too long to respond — it may be building the feed cache. '
        'Pull down to retry in a moment.',
      );
    }
    final msg =
        (e.response?.data is Map
            ? (e.response!.data as Map)['detail']
            : null) ??
        e.message ??
        'Network error';
    return Exception(msg);
  }
}
