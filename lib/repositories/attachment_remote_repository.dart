// lib/repositories/attachment_remote_repository.dart
import 'package:campusassist/core/interceptors/auth_interceptor.dart';
import 'package:campusassist/core/server_constants.dart';
import 'package:campusassist/models/attachment_model.dart';
import 'package:dio/dio.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:image_picker/image_picker.dart';

final attachmentDioProvider = Provider<Dio>((ref) {
  final dio = Dio(
    BaseOptions(
      baseUrl: ServerConstants.baseURL,
      connectTimeout: const Duration(seconds: 30),
      receiveTimeout: const Duration(seconds: 30),
    ),
  );
  dio.interceptors.add(AuthInterceptor(ref));
  return dio;
});

final attachmentRemoteRepositoryProvider = Provider<AttachmentRemoteRepository>(
  (ref) {
    return AttachmentRemoteRepository(ref.read(attachmentDioProvider));
  },
);

class AttachmentRemoteRepository {
  final Dio _dio;

  AttachmentRemoteRepository(this._dio);

  /// POST /api/attachments/upload
  /// Uploads a single file and returns its metadata.
  /// [onSendProgress] reports bytes sent / total for progress indication.
  Future<Attachment> uploadFile(
    XFile file, {
    ProgressCallback? onSendProgress,
  }) async {
    try {
      final bytes = await file.readAsBytes();
      final filename = file.name.isNotEmpty ? file.name : 'attachment.jpg';

      final formData = FormData.fromMap({
        'file': MultipartFile.fromBytes(bytes, filename: filename),
      });

      final response = await _dio.post<Map<String, dynamic>>(
        '/attachments/upload',
        data: formData,
        onSendProgress: onSendProgress,
      );

      return Attachment.fromJson(response.data!);
    } on DioException catch (e) {
      throw _mapDioError(e);
    }
  }

  /// Uploads multiple files sequentially and returns their metadata.
  /// [onFileProgress] is called with (fileIndex, bytesSent, totalBytes).
  Future<List<Attachment>> uploadFiles(
    List<XFile> files, {
    void Function(int fileIndex, int sent, int total)? onFileProgress,
  }) async {
    final results = <Attachment>[];
    for (int i = 0; i < files.length; i++) {
      final attachment = await uploadFile(
        files[i],
        onSendProgress: onFileProgress != null
            ? (sent, total) => onFileProgress(i, sent, total)
            : null,
      );
      results.add(attachment);
    }
    return results;
  }

  /// GET /api/attachments/my
  Future<List<Attachment>> listMyAttachments() async {
    try {
      final response = await _dio.get<dynamic>('/attachments/my');
      final data = response.data;
      final dataMap = data is Map<String, dynamic> ? data : null;
      final list =
          (data is List
                  ? data
                  : dataMap?['items'] ?? dataMap?['attachments'] ?? [])
              as List<dynamic>;
      return list
          .map((e) => Attachment.fromJson(e as Map<String, dynamic>))
          .toList();
    } on DioException catch (e) {
      throw _mapDioError(e);
    }
  }

  /// GET /api/attachments/{attachment_id}
  Future<Attachment> getAttachment(String attachmentId) async {
    try {
      final response = await _dio.get<Map<String, dynamic>>(
        '/attachments/$attachmentId',
      );
      return Attachment.fromJson(response.data!);
    } on DioException catch (e) {
      throw _mapDioError(e);
    }
  }

  /// DELETE /api/attachments/{attachment_id}
  Future<void> deleteAttachment(String attachmentId) async {
    try {
      await _dio.delete('/attachments/$attachmentId');
    } on DioException catch (e) {
      throw _mapDioError(e);
    }
  }

  /// Returns the streaming download URL for an attachment.
  /// Requests to this URL require a valid Bearer token in the Authorization header.
  String downloadUrl(String attachmentId) =>
      '${ServerConstants.baseURL}/attachments/$attachmentId/download';

  Exception _mapDioError(DioException e) {
    final status = e.response?.statusCode;
    final message =
        (e.response?.data is Map
            ? (e.response!.data as Map)['detail']
            : null) ??
        e.message ??
        'Something went wrong';
    if (status == 404) return Exception('Attachment not found');
    if (status == 401 || status == 403) return Exception('Unauthorized');
    if (status == 413) return Exception('File too large');
    if (e.type == DioExceptionType.connectionTimeout ||
        e.type == DioExceptionType.receiveTimeout ||
        e.type == DioExceptionType.connectionError) {
      return Exception('No internet connection');
    }
    return Exception(message);
  }
}
