import 'package:dio/dio.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../repositories/auth_local_repository.dart';
import '../../repositories/auth_remote_repository.dart';

class AuthInterceptor extends Interceptor {
  final Ref ref;

  AuthInterceptor(this.ref);

  @override
  void onRequest(
    RequestOptions options,
    RequestInterceptorHandler handler,
  ) async {
    print("REQUEST → ${options.method} ${options.path}");
    print("FULL URL → ${options.uri}");

    final local = ref.read(authLocalRepositoryProvider);
    final accessToken = await local.getAccessToken();

    print("ACCESS TOKEN → $accessToken");

    if (accessToken != null) {
      options.headers['Authorization'] = 'Bearer $accessToken';
    }

    handler.next(options);
  }

  @override
  void onError(DioException err, ErrorInterceptorHandler handler) async {
    print(
      "ERROR → status=${err.response?.statusCode} type=${err.type} msg=${err.message}",
    );
    print("FAILED URL → ${err.requestOptions.uri}");
    if (err.error != null) print("UNDERLYING ERROR → ${err.error}");

    if (err.response?.statusCode == 401) {
      print("401 detected → attempting refresh");

      try {
        final local = ref.read(authLocalRepositoryProvider);
        final refreshToken = await local.getRefreshToken();

        print("REFRESH TOKEN → $refreshToken");

        if (refreshToken == null) {
          handler.next(err);
          return;
        }

        final authRepo = ref.read(authRemoteRepositoryProvider);

        print("Calling refreshSession()");

        final newUser = await authRepo.refreshSession(refreshToken);

        print("Refresh successful");

        await local.saveTokens(newUser.accessToken, newUser.refreshToken);

        final request = err.requestOptions;
        request.headers['Authorization'] = 'Bearer ${newUser.accessToken}';

        final dio = ref.read(authDioProvider);

        final response = await dio.fetch(request);

        handler.resolve(response);
      } catch (e) {
        print("Refresh failed → $e");

        // Only clear tokens if the server explicitly rejected the refresh token
        // (401/403). For network errors (server down), keep the user logged in.
        final isAuthError =
            e is DioException &&
            e.type == DioExceptionType.badResponse &&
            (e.response?.statusCode == 401 || e.response?.statusCode == 403);

        if (isAuthError) {
          await ref.read(authLocalRepositoryProvider).clearTokens();
        }

        handler.next(err);
      }
    } else {
      handler.next(err);
    }
  }
}
