// lib/repositories/profile_remote_repository.dart
import 'package:campusassist/core/interceptors/auth_interceptor.dart';
import 'package:campusassist/core/server_constants.dart';
import 'package:dio/dio.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:image_picker/image_picker.dart';

import '../models/user_model.dart';

final profileDioProvider = Provider<Dio>((ref) {
  final dio = Dio(
    BaseOptions(
      baseUrl: ServerConstants.baseURL,
      connectTimeout: const Duration(seconds: 15),
      receiveTimeout: const Duration(seconds: 15),
    ),
  );
  dio.interceptors.add(AuthInterceptor(ref));
  return dio;
});

final profileRemoteRepositoryProvider = Provider<ProfileRemoteRepository>((
  ref,
) {
  return ProfileRemoteRepository(ref.read(profileDioProvider));
});

class UserStats {
  final int postCount;
  final int answerCount;
  final int totalUpvotes;

  const UserStats({
    this.postCount = 0,
    this.answerCount = 0,
    this.totalUpvotes = 0,
  });

  factory UserStats.fromJson(Map<String, dynamic> json) => UserStats(
    postCount: json['post_count'] as int? ?? 0,
    answerCount: json['answer_count'] as int? ?? 0,
    totalUpvotes: json['total_upvotes'] as int? ?? 0,
  );
}

class ProfileRemoteRepository {
  final Dio _dio;

  ProfileRemoteRepository(this._dio);

  // ── GET /api/auth/me ───────────────────────────────────────────────────────

  /// Fetches the authenticated user's profile from the server.
  /// Tokens are preserved from the local cache by the caller.
  Future<UserModel> getMe() async {
    try {
      final response = await _dio.get<Map<String, dynamic>>('/auth/me');
      final data = response.data!;
      // Response may be the user object directly or nested under 'user'
      final userMap = (data['user'] as Map<String, dynamic>?) ?? data;
      return UserModel.fromResponse({
        ...userMap,
        // Tokens are not returned by GET /auth/me — keep empty so callers
        // preserve the existing ones.
        'access_token': '',
        'refresh_token': '',
      });
    } on DioException catch (e) {
      throw _mapDioError(e);
    }
  }

  // ── PATCH /api/auth/me ─────────────────────────────────────────────────────

  /// Updates the authenticated user's profile (name, picture).
  /// Returns the updated [UserModel] without tokens (caller preserves them).
  Future<UserModel> updateProfile({String? name, String? picture}) async {
    try {
      final response = await _dio.patch<Map<String, dynamic>>(
        '/auth/me',
        data: {
          if (name != null) 'name': name,
          if (picture != null) 'picture': picture,
        },
      );
      final data = response.data!;
      final userMap = (data['user'] as Map<String, dynamic>?) ?? data;
      return UserModel.fromResponse({
        ...userMap,
        'access_token': '',
        'refresh_token': '',
      });
    } on DioException catch (e) {
      throw _mapDioError(e);
    }
  }

  // ── GET /api/auth/admin/users/{user_id} ────────────────────────────────────

  /// Fetches any user's public profile by their ID (admin endpoint).
  Future<UserModel> getUserById(String userId) async {
    try {
      final response = await _dio.get<Map<String, dynamic>>(
        '/auth/admin/users/$userId',
      );
      final data = response.data!;
      final userMap = (data['user'] as Map<String, dynamic>?) ?? data;
      return UserModel.fromResponse({
        ...userMap,
        'access_token': '',
        'refresh_token': '',
      });
    } on DioException catch (e) {
      throw _mapDioError(e);
    }
  }

  // ── Stats (not in API spec — returns empty placeholder) ───────────────────

  Future<UserStats> getMyStats() async {
    // The backend does not expose a user-stats endpoint.
    // Return zeroed stats — callers degrade gracefully.
    return const UserStats();
  }

  // ── POST /api/attachments/upload for avatar ────────────────────────────────

  /// Uploads profile picture via the attachments service, then updates the
  /// profile with the returned download URL.
  Future<String> uploadAvatar(XFile file) async {
    final bytes = await file.readAsBytes();
    final filename = file.name.isNotEmpty ? file.name : 'avatar.jpg';

    final formData = FormData.fromMap({
      'file': MultipartFile.fromBytes(bytes, filename: filename),
    });

    final response = await _dio.post<Map<String, dynamic>>(
      '/attachments/upload',
      data: formData,
    );

    // AttachmentResponse has no 'url' field — build the download URL from the id
    final attachmentId = response.data!['id'] as String? ?? '';
    if (attachmentId.isEmpty) return '';

    final downloadUrl =
        '${ServerConstants.baseURL}/attachments/$attachmentId/download';

    // Update the user's picture field with the download URL
    try {
      await updateProfile(picture: downloadUrl);
    } catch (_) {
      // Non-fatal if the profile update fails
    }

    return downloadUrl;
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
