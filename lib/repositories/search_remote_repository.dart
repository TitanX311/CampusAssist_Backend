// lib/repositories/search_remote_repository.dart
import 'package:dio/dio.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../core/server_constants.dart';
import '../models/search_result_model.dart';

final _searchDioProvider = Provider<Dio>((ref) {
  return Dio(
    BaseOptions(
      baseUrl: ServerConstants.baseURL,
      connectTimeout: const Duration(seconds: 10),
      receiveTimeout: const Duration(seconds: 10),
    ),
  );
});

final searchRemoteRepositoryProvider = Provider<SearchRemoteRepository>((ref) {
  return SearchRemoteRepository(ref.watch(_searchDioProvider));
});

class SearchRemoteRepository {
  final Dio _dio;
  SearchRemoteRepository(this._dio);

  /// GET /api/search?q=...&type=...&college_id=...&page=...&page_size=...
  Future<SearchResponse> search({
    required String query,
    String type = 'all', // 'all' | 'college' | 'community'
    String? collegeId,
    int page = 1,
    int pageSize = 20,
  }) async {
    try {
      final response = await _dio.get<Map<String, dynamic>>(
        '/search',
        queryParameters: {
          'q': query,
          'type': type,
          if (collegeId != null) 'college_id': collegeId,
          'page': page,
          'page_size': pageSize,
        },
      );
      return SearchResponse.fromMap(response.data!);
    } on DioException catch (e) {
      throw _mapError(e);
    }
  }

  String _mapError(DioException e) {
    if (e.type == DioExceptionType.connectionError) {
      return 'Could not reach server. Check your network.';
    }
    if (e.type == DioExceptionType.connectionTimeout ||
        e.type == DioExceptionType.receiveTimeout) {
      return 'Request timed out. Please try again.';
    }
    return 'Search failed (${e.response?.statusCode}). Please try again.';
  }
}
