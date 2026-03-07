// repositories/auth_local_repository.dart
import 'dart:convert';

import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:shared_preferences/shared_preferences.dart';

import '../models/user_model.dart';

final authLocalRepositoryProvider = Provider((ref) => AuthLocalRepository());

class AuthLocalRepository {
  static const _accessKey = 'access_token';
  static const _refreshKey = 'refresh_token';
  static const _userProfileKey = 'user_profile';

  Future<void> saveTokens(String access, String refresh) async {
    final prefs = await SharedPreferences.getInstance();
    await prefs.setString(_accessKey, access);
    await prefs.setString(_refreshKey, refresh);
  }

  Future<String?> getAccessToken() async {
    final prefs = await SharedPreferences.getInstance();
    return prefs.getString(_accessKey);
  }

  Future<String?> getRefreshToken() async {
    final prefs = await SharedPreferences.getInstance();
    return prefs.getString(_refreshKey);
  }

  Future<void> saveUserProfile(UserModel user) async {
    final prefs = await SharedPreferences.getInstance();
    await prefs.setString(
      _userProfileKey,
      jsonEncode({
        'id': user.id,
        'name': user.name,
        'email': user.email,
        'picture': user.pictureURL,
        'college': user.college,
        'type': user.userType,
      }),
    );
  }

  Future<UserModel?> getCachedUserProfile() async {
    final prefs = await SharedPreferences.getInstance();
    final json = prefs.getString(_userProfileKey);
    final refreshToken = prefs.getString(_refreshKey);
    if (json == null || refreshToken == null) return null;
    final map = jsonDecode(json) as Map<String, dynamic>;
    return UserModel.fromResponse({
      ...map,
      'refresh_token': refreshToken,
      'access_token': prefs.getString(_accessKey) ?? '',
      // 'type' is already in map from the saved profile above
    });
  }

  Future<void> clearTokens() async {
    final prefs = await SharedPreferences.getInstance();
    await prefs.remove(_accessKey);
    await prefs.remove(_refreshKey);
    await prefs.remove(_userProfileKey);
  }
}
