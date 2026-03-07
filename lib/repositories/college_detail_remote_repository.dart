// lib/repositories/college_detail_remote_repository.dart
import 'package:campusassist/core/interceptors/auth_interceptor.dart';
import 'package:campusassist/core/server_constants.dart';
import 'package:campusassist/models/college_model.dart';
import 'package:campusassist/models/community_model.dart';
import 'package:dio/dio.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

final collegeDetailDioProvider = Provider<Dio>((ref) {
  final dio = Dio(
    BaseOptions(
      baseUrl: ServerConstants.baseURL,
      connectTimeout: const Duration(seconds: 8),
      receiveTimeout: const Duration(seconds: 8),
    ),
  );
  dio.interceptors.add(AuthInterceptor(ref));
  return dio;
});

final collegeDetailRemoteRepositoryProvider =
    Provider<CollegeDetailRemoteRepository>((ref) {
      return CollegeDetailRemoteRepository(ref.watch(collegeDetailDioProvider));
    });

class CollegeDetailRemoteRepository {
  final Dio _dio;
  CollegeDetailRemoteRepository(this._dio);

  /// GET /api/college/{college_id}
  Future<CollegeModel> getCollege(String collegeId) async {
    try {
      final response = await _dio.get<Map<String, dynamic>>(
        '/college/$collegeId',
      );
      return CollegeModel.fromMap(response.data!);
    } on DioException catch (e) {
      throw _mapDioError(e);
    }
  }

  /// GET /api/community/college/{college_id}
  /// Uses the community service to get communities belonging to a college.
  Future<List<Community>> getCollegeCommunities(
    String collegeId, {
    int page = 1,
    int pageSize = 20,
  }) async {
    try {
      final response = await _dio.get<Map<String, dynamic>>(
        '/community/college/$collegeId',
        queryParameters: {'page': page, 'page_size': pageSize},
      );
      final data = response.data!;
      final raw =
          (data['items'] ??
                  data['communities'] ??
                  data['results'] ??
                  data['data'] ??
                  [])
              as List<dynamic>;
      return raw
          .map((e) => Community.fromMap(e as Map<String, dynamic>))
          .toList();
    } on DioException catch (e) {
      throw _mapDioError(e);
    }
  }

  String _mapDioError(DioException e) {
    switch (e.type) {
      case DioExceptionType.connectionTimeout:
      case DioExceptionType.receiveTimeout:
        return 'Connection timed out. Check your network.';
      case DioExceptionType.connectionError:
        return 'Could not reach server. Is it running?';
      case DioExceptionType.badResponse:
        final status = e.response?.statusCode;
        if (status == 404) return 'College not found.';
        if (status == 401) return 'Unauthorized. Please log in again.';
        return 'Server error ($status). Please try again.';
      default:
        return 'Network error. Please try again.';
    }
  }
}
