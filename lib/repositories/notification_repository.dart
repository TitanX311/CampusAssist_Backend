// lib/repositories/notification_repository.dart
import 'package:campusassist/core/interceptors/auth_interceptor.dart';
import 'package:campusassist/core/server_constants.dart';
import 'package:campusassist/models/notification_model.dart';
import 'package:campusassist/repositories/auth_local_repository.dart';
import 'package:dio/dio.dart';
import 'package:flutter/foundation.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

final notificationRepositoryProvider = Provider<NotificationRepository>((ref) {
  final dio = Dio(
    BaseOptions(baseUrl: '${ServerConstants.baseURL}/notifications'),
  );
  dio.interceptors.add(AuthInterceptor(ref));
  return NotificationRepository(dio, ref.read(authLocalRepositoryProvider));
});

class NotificationRepository {
  final Dio _dio;
  final AuthLocalRepository _local;

  NotificationRepository(this._dio, this._local);

  /// GET /api/notifications
  Future<({List<AppNotification> items, int total, int unreadCount})> list({
    int page = 1,
    int pageSize = 20,
    bool unreadOnly = false,
  }) async {
    try {
      debugPrint(
        '[NotifRepo] GET /notifications page=$page unreadOnly=$unreadOnly',
      );
      final res = await _dio.get<Map<String, dynamic>>(
        '',
        queryParameters: {
          'page': page,
          'page_size': pageSize,
          if (unreadOnly) 'unread_only': true,
        },
      );
      final data = res.data!;
      final items = (data['items'] as List<dynamic>? ?? [])
          .map((e) => AppNotification.fromJson(e as Map<String, dynamic>))
          .toList();
      return (
        items: items,
        total: data['total'] as int? ?? items.length,
        unreadCount: data['unread_count'] as int? ?? 0,
      );
    } on DioException catch (e) {
      throw _mapError(e);
    }
  }

  /// GET /api/notifications/unread-count
  Future<int> unreadCount() async {
    try {
      final res = await _dio.get<Map<String, dynamic>>('/unread-count');
      return res.data!['count'] as int? ?? 0;
    } on DioException catch (e) {
      throw _mapError(e);
    }
  }

  /// POST /api/notifications/{id}/read
  Future<void> markRead(String id) async {
    try {
      debugPrint('[NotifRepo] POST /notifications/$id/read');
      await _dio.post('/$id/read');
    } on DioException catch (e) {
      throw _mapError(e);
    }
  }

  /// POST /api/notifications/read-all
  Future<void> markAllRead() async {
    try {
      debugPrint('[NotifRepo] POST /notifications/read-all');
      await _dio.post('/read-all');
    } on DioException catch (e) {
      throw _mapError(e);
    }
  }

  /// DELETE /api/notifications/{id}
  Future<void> delete(String id) async {
    try {
      debugPrint('[NotifRepo] DELETE /notifications/$id');
      await _dio.delete('/$id');
    } on DioException catch (e) {
      throw _mapError(e);
    }
  }

  /// POST /api/notifications/device-token
  Future<void> registerDeviceToken(String token) async {
    try {
      debugPrint('[NotifRepo] POST /notifications/device-token');
      await _dio.post(
        '/device-token',
        data: {'token': token, 'platform': 'android'},
      );
    } on DioException catch (e) {
      // Non-fatal — log and continue
      debugPrint('[NotifRepo] registerDeviceToken error: $e');
    }
  }

  /// DELETE /api/notifications/device-token
  Future<void> unregisterDeviceToken() async {
    try {
      debugPrint('[NotifRepo] DELETE /notifications/device-token');
      await _dio.delete('/device-token');
    } on DioException catch (e) {
      debugPrint('[NotifRepo] unregisterDeviceToken error: $e');
    }
  }

  /// Returns the stored access token — used by the WebSocket manager.
  Future<String?> getAccessToken() => _local.getAccessToken();

  Exception _mapError(DioException e) {
    final msg =
        (e.response?.data is Map
            ? (e.response!.data as Map)['detail']
            : null) ??
        e.message ??
        'Network error';
    return Exception(msg);
  }
}
