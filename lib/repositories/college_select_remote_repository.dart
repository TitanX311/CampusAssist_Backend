// repositories/college_select_remote_repository.dart
import 'package:campusassist/core/interceptors/auth_interceptor.dart';
import 'package:campusassist/core/server_constants.dart';
import 'package:campusassist/models/college_model.dart';
import 'package:dio/dio.dart';
import 'package:flutter/foundation.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

final collegeSelectDioProvider = Provider<Dio>((ref) {
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

final collegeSelectRemoteRepositoryProvider =
    Provider<CollegeSelectRemoteRepository>((ref) {
      return CollegeSelectRemoteRepository(ref.watch(collegeSelectDioProvider));
    });

class CollegeSelectRemoteRepository {
  final Dio _dio;
  CollegeSelectRemoteRepository(this._dio);

  Future<List<CollegeModel>> searchColleges(String query) async {
    try {
      debugPrint(
        '[CollegeSelectRepo] GET /api/college query="$query" page=1 page_size=50',
      );
      // The college service only supports pagination — no free-text query param.
      // Fetch up to 50 records and filter client-side when a query is provided.
      final response = await _dio.get<Map<String, dynamic>>(
        '/college',
        queryParameters: {'page': 1, 'page_size': 50},
      );
      debugPrint('[CollegeSelectRepo] response: ${response.data}');
      final data = response.data!;
      final results =
          (data['items'] ??
                  data['results'] ??
                  data['colleges'] ??
                  data['data'] ??
                  [])
              as List<dynamic>;
      final all = results
          .map((e) => CollegeModel.fromMap(e as Map<String, dynamic>))
          .toList();

      if (query.trim().isEmpty) return all;

      // Client-side filter
      final lowerQ = query.trim().toLowerCase();
      return all.where((c) => c.name.toLowerCase().contains(lowerQ)).toList();
    } on DioException catch (e) {
      debugPrint('[CollegeSelectRepo] DioException: ${e.type} ${e.message}');
      throw _mapDioError(e);
    } catch (e) {
      debugPrint('[CollegeSelectRepo] unexpected error: $e');
      rethrow;
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
        return 'Server error (${e.response?.statusCode}). Please try again.';
      default:
        return 'Network error. Please try again.';
    }
  }
}
