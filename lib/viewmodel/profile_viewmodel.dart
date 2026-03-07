// lib/viewmodel/profile_viewmodel.dart
import 'package:campusassist/repositories/profile_remote_repository.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:image_picker/image_picker.dart';

import '../models/user_model.dart';
import '../repositories/auth_local_repository.dart';
import '../viewmodel/auth_viewmodel.dart';

// ─── GET /api/users/me ─────────────────────────────────────────────────────────

final currentProfileProvider =
    AsyncNotifierProvider<CurrentProfileNotifier, UserModel?>(
      CurrentProfileNotifier.new,
    );

class CurrentProfileNotifier extends AsyncNotifier<UserModel?> {
  @override
  Future<UserModel?> build() async {
    final cached = ref.watch(authViewModelProvider).value;
    if (cached == null) return null;
    return _fetchAndMerge(cached);
  }

  Future<UserModel?> _fetchAndMerge(UserModel cached) async {
    try {
      final fresh = await ref.read(profileRemoteRepositoryProvider).getMe();
      final local = ref.read(authLocalRepositoryProvider);
      final accessToken = await local.getAccessToken() ?? cached.accessToken;
      final refreshToken = await local.getRefreshToken() ?? cached.refreshToken;
      final merged = fresh.copyWith(
        accessToken: accessToken,
        refreshToken: refreshToken,
      );
      await local.saveUserProfile(merged);
      return merged;
    } catch (_) {
      return cached;
    }
  }

  Future<void> refresh() async {
    final cached = ref.read(authViewModelProvider).value;
    if (cached == null) return;
    state = const AsyncLoading();
    state = await AsyncValue.guard(() => _fetchAndMerge(cached));
  }
}

// ─── GET /api/users/{user_id} ──────────────────────────────────────────────────

final userByIdProvider = AsyncNotifierProvider.autoDispose
    .family<UserByIdNotifier, UserModel?, String>(UserByIdNotifier.new);

class UserByIdNotifier extends AsyncNotifier<UserModel?> {
  UserByIdNotifier(this.userId);
  final String userId;

  @override
  Future<UserModel?> build() async {
    if (userId.isEmpty) return null;
    return ref.read(profileRemoteRepositoryProvider).getUserById(userId);
  }

  Future<void> refresh() async {
    state = const AsyncLoading();
    state = await AsyncValue.guard(
      () => ref.read(profileRemoteRepositoryProvider).getUserById(userId),
    );
  }
}

// ─── Stats Provider ────────────────────────────────────────────────────────────

final userStatsProvider = AsyncNotifierProvider<UserStatsNotifier, UserStats>(
  UserStatsNotifier.new,
);

class UserStatsNotifier extends AsyncNotifier<UserStats> {
  @override
  Future<UserStats> build() async {
    return ref.read(profileRemoteRepositoryProvider).getMyStats();
  }

  Future<void> refresh() async {
    state = const AsyncLoading();
    state = await AsyncValue.guard(
      () => ref.read(profileRemoteRepositoryProvider).getMyStats(),
    );
  }
}

// ─── PATCH /api/auth/me ────────────────────────────────────────────────────────

final profileEditProvider =
    AsyncNotifierProvider<ProfileEditNotifier, UserModel?>(
      ProfileEditNotifier.new,
    );

class ProfileEditNotifier extends AsyncNotifier<UserModel?> {
  @override
  Future<UserModel?> build() async {
    return ref.watch(authViewModelProvider).value;
  }

  Future<void> updateProfile({String? name, String? picture}) async {
    state = const AsyncLoading();
    state = await AsyncValue.guard(() async {
      final repo = ref.read(profileRemoteRepositoryProvider);
      final updated = await repo.updateProfile(name: name, picture: picture);

      final local = ref.read(authLocalRepositoryProvider);
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

      ref.invalidate(authViewModelProvider);
      ref.invalidate(currentProfileProvider);

      return merged;
    });
  }

  Future<String?> uploadAvatar(XFile file) async {
    try {
      final repo = ref.read(profileRemoteRepositoryProvider);
      final url = await repo.uploadAvatar(file);
      if (url.isNotEmpty) {
        final local = ref.read(authLocalRepositoryProvider);
        final cached = await local.getCachedUserProfile();
        if (cached != null) {
          await local.saveUserProfile(cached.copyWith(pictureURL: url));
        }
        ref.invalidate(authViewModelProvider);
        ref.invalidate(currentProfileProvider);
      }
      return url;
    } catch (e) {
      return null;
    }
  }
}
