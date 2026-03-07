import 'dart:async';

import 'package:campusassist/models/user_model.dart';
import 'package:campusassist/repositories/auth_remote_repository.dart';
import 'package:campusassist/repositories/notification_repository.dart';
import 'package:campusassist/repositories/profile_remote_repository.dart';
import 'package:dio/dio.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../repositories/auth_local_repository.dart';

final authViewModelProvider = AsyncNotifierProvider<AuthViewModel, UserModel?>(
  AuthViewModel.new,
);

class AuthViewModel extends AsyncNotifier<UserModel?> {
  @override
  Future<UserModel?> build() async {
    final local = ref.read(authLocalRepositoryProvider);

    print("Checking refresh token...");

    final token = await local.getRefreshToken();
    print("Refresh token: $token");

    if (token == null) {
      print("No token found");
      return null;
    }

    try {
      print("Refreshing session...");
      final user = await ref
          .read(authRemoteRepositoryProvider)
          .refreshSession(token);

      print("Session refreshed");

      await local.saveTokens(user.accessToken, user.refreshToken);
      await local.saveUserProfile(user);

      print("Session refreshed — userType=${user.userType}");
      return user;
    } on DioException catch (e) {
      final isAuthError =
          e.type == DioExceptionType.badResponse &&
          (e.response?.statusCode == 401 || e.response?.statusCode == 403);

      if (isAuthError) {
        // Refresh token is invalid/expired — force sign-in
        print("Auth error during refresh — clearing tokens");
        await local.clearTokens();
        return null;
      }

      // Server is unreachable (down, no network, timeout) — keep user logged in
      print("Network error during refresh — using cached profile: $e");
      return await local.getCachedUserProfile();
    } catch (e) {
      print("Unexpected error during refresh: $e");
      final cached = await local.getCachedUserProfile();
      if (cached != null) return cached;
      await local.clearTokens();
      return null;
    }
  }

  Future<UserModel?> signIn({
    required String email,
    required String password,
  }) async {
    state = const AsyncLoading();

    final result = await AsyncValue.guard(
      () => ref
          .read(authRemoteRepositoryProvider)
          .signIn(email: email, password: password),
    );

    if (result.hasValue && result.value != null) {
      final local = ref.read(authLocalRepositoryProvider);

      await local.saveTokens(
        result.value!.accessToken,
        result.value!.refreshToken,
      );
      await local.saveUserProfile(result.value!);
    }

    state = result;

    return result.value;
  }

  Future<UserModel?> createAccount({
    required String name,
    required String email,
    required String password,
  }) async {
    state = const AsyncLoading();

    final result = await AsyncValue.guard(
      () => ref
          .read(authRemoteRepositoryProvider)
          .createAccount(name: name, email: email, password: password),
    );

    if (result.hasValue && result.value != null) {
      final local = ref.read(authLocalRepositoryProvider);

      await local.saveTokens(
        result.value!.accessToken,
        result.value!.refreshToken,
      );
      await local.saveUserProfile(result.value!);
    }

    state = result;

    return result.value;
  }

  Future<UserModel?> googleSignIn() async {
    state = const AsyncLoading();

    final result = await AsyncValue.guard(
      () => ref.read(authRemoteRepositoryProvider).googleSignIn(),
    );

    if (result.hasValue && result.value != null) {
      final local = ref.read(authLocalRepositoryProvider);
      await local.saveTokens(
        result.value!.accessToken,
        result.value!.refreshToken,
      );
      await local.saveUserProfile(result.value!);
    }

    state = result;
    return result.value;
  }

  Future<void> updateProfile({String? name, String? picture}) async {
    final local = ref.read(authLocalRepositoryProvider);

    final result = await AsyncValue.guard(() async {
      final updated = await ref
          .read(profileRemoteRepositoryProvider)
          .updateProfile(name: name, picture: picture);

      // Preserve existing tokens if the server didn't return new ones
      final accessToken = updated.accessToken.isNotEmpty
          ? updated.accessToken
          : (await local.getAccessToken() ?? '');
      final refreshToken = updated.refreshToken.isNotEmpty
          ? updated.refreshToken
          : (await local.getRefreshToken() ?? '');

      final merged = updated.copyWith(
        accessToken: accessToken,
        refreshToken: refreshToken,
      );
      await local.saveTokens(accessToken, refreshToken);
      await local.saveUserProfile(merged);
      return merged;
    });

    if (result.hasValue && result.value != null) {
      state = AsyncData(result.value!);
    } else if (result.hasError) {
      throw result.error!;
    }
  }

  Future<void> signOut() async {
    final local = ref.read(authLocalRepositoryProvider);
    final remote = ref.read(authRemoteRepositoryProvider);

    // Unregister FCM token before clearing auth
    await ref.read(notificationRepositoryProvider).unregisterDeviceToken();

    final refreshToken = await local.getRefreshToken();

    if (refreshToken != null) {
      // remote.signOut() never throws — errors are handled inside it
      await remote.signOut(refreshToken);
    }

    await local.clearTokens();
    state = const AsyncData(null);
  }

  Future<void> signOutLocally() async {
    final local = ref.read(authLocalRepositoryProvider);
    await local.clearTokens();
    state = const AsyncData(null);
  }
}
