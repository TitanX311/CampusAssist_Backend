import 'package:campusassist/models/college_model.dart';
import 'package:campusassist/models/user_model.dart';
import 'package:campusassist/viewmodel/auth_viewmodel.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_riverpod/legacy.dart';

/// Exposes the currently authenticated [UserModel], or `null` when signed out.
///
/// Usage:
///   final user = ref.watch(currentUserProvider);
///
/// Note: This returns `null` while the auth state is still loading.
/// If you need to distinguish loading from signed-out, watch
/// [authViewModelProvider] directly and use `.when(...)`.
final currentUserProvider = Provider<UserModel?>((ref) {
  return ref.watch(authViewModelProvider).value;
});

/// Holds the college the user has selected for their feed.
/// `null` means no college is selected.
final selectedCollegeProvider = StateProvider<CollegeModel?>((ref) => null);
