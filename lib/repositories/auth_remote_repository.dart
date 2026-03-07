// /repositories/auth_remote_repository.dart
import 'package:campusassist/core/server_constants.dart';
import 'package:campusassist/models/user_model.dart';
import 'package:dio/dio.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:google_sign_in/google_sign_in.dart';

import '../core/interceptors/auth_interceptor.dart';

final authDioProvider = Provider<Dio>((ref) {
  final dio = Dio(
    BaseOptions(
      baseUrl: '${ServerConstants.baseURL}/auth',
      connectTimeout: const Duration(seconds: 10),
      receiveTimeout: const Duration(seconds: 10),
    ),
  );

  dio.interceptors.add(AuthInterceptor(ref));

  return dio;
});

final authRemoteRepositoryProvider = Provider<AuthRemoteRepository>((ref) {
  return AuthRemoteRepository(ref.read(authDioProvider));
});

class AuthRemoteRepository {
  final Dio _dio;
  final GoogleSignIn _googleSignIn = GoogleSignIn.instance;

  AuthRemoteRepository(this._dio);

  Future<void> initGoogleSignIn() async {
    await _googleSignIn.initialize(
      clientId:
          '919964734589-qc4hujusfk752sv3lcs58dol2e068gao.apps.googleusercontent.com',
      serverClientId:
          '919964734589-89ak0sbj80p8574tra349f7desihkb84.apps.googleusercontent.com',
    );
  }

  // Future<String?> getIdToken() async {
  //   final GoogleSignInAccount account = await _googleSignIn.authenticate();
  //   final GoogleSignInAuthentication auth = account.authentication;
  //   print(auth.idToken);
  //   return auth.idToken;
  // }

  Future<UserModel> signIn({
    required String email,
    required String password,
  }) async {
    try {
      final response = await _dio.post(
        '/login',
        data: {'email': email, 'password': password},
      );
      print("SERVER RESPONSE: ${response.data}");

      final userMap = response.data['user'];
      final refreshToken = response.data['refresh_token'];
      final accessToken = response.data['access_token'];

      return UserModel.fromResponse({
        ...userMap,
        'refresh_token': refreshToken,
        'access_token': accessToken,
      });
    } on DioException catch (e) {
      print("DIO ERROR:");
      print(e.response?.data);
      print(e.message);
      rethrow;
    } catch (e) {
      print("UNKNOWN ERROR: $e");
      rethrow;
    }
  }

  Future<UserModel> createAccount({
    required String name,
    required String email,
    required String password,
  }) async {
    try {
      final response = await _dio.post(
        '/register',
        data: {'name': name, 'email': email, 'password': password},
      );
      print("SERVER RESPONSE: ${response.data}");
      final userMap = response.data['user'];
      final refreshToken = response.data['refresh_token'];
      final accessToken = response.data['access_token'];

      return UserModel.fromResponse({
        ...userMap,
        'refresh_token': refreshToken,
        'access_token': accessToken,
      });
    } on DioException catch (e) {
      print("DIO ERROR:");
      print(e.response?.data);
      print(e.message);
      rethrow;
    } catch (e) {
      print("UNKNOWN ERROR: $e");
      rethrow;
    }
  }

  Future<UserModel> googleSignIn() async {
    try {
      await initGoogleSignIn();

      final GoogleSignInAccount account = await _googleSignIn.authenticate();
      final GoogleSignInAuthentication auth = account.authentication;

      final idToken = auth.idToken;
      // print("ID TOKEN: $idToken");
      // print("Sending Google token to backend...");

      final response = await _dio.post('/google', data: {'id_token': idToken});

      // print("SERVER RESPONSE: ${response.data}");

      final userMap = response.data['user'];
      final refreshToken = response.data['refresh_token'];
      final accessToken = response.data['access_token'];

      return UserModel.fromResponse({
        ...userMap,
        'refresh_token': refreshToken,
        'access_token': accessToken,
      });
    } on DioException {
      rethrow;
    } catch (e) {
      print("UNKNOWN ERROR: $e");
      rethrow;
    }
  }

  Future<UserModel> refreshSession(String refreshToken) async {
    try {
      // print("REFRESH API CALL STARTED");

      final response = await _dio.post(
        '/refresh',
        data: {'refresh_token': refreshToken},
      );

      // print("REFRESH RESPONSE → ${response.data}");
      final userMap = response.data['user'];

      return UserModel.fromResponse({
        ...userMap,
        'access_token': response.data['access_token'],
        'refresh_token': response.data['refresh_token'],
      });
    } on DioException catch (e) {
      throw Exception(e.response?.data ?? e.message);
    } catch (e) {
      throw Exception(e.toString());
    }
  }

  Future<void> signOut(String refreshToken) async {
    try {
      await _dio.post('/logout', data: {'refresh_token': refreshToken});
      print("User signed out from server successfully");
    } on DioException catch (e) {
      // Server unreachable or error — log and continue with local sign-out
      print("LOGOUT SERVER ERROR (ignored): ${e.response?.data ?? e.message}");
    } catch (e) {
      print("UNKNOWN LOGOUT ERROR (ignored): $e");
    }

    // Always attempt Google sign-out locally regardless of server result
    try {
      await _googleSignIn.signOut();
    } catch (e) {
      print("Google sign-out error (ignored): $e");
    }
  }
}
