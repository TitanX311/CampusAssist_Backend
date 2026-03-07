// lib/viewmodel/community_viewmodel.dart
import 'dart:async';

import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../models/community_model.dart';
import '../repositories/community_remote_repository.dart';

final communityViewModelProvider =
    AsyncNotifierProvider<CommunityViewModel, List<Community>>(
      CommunityViewModel.new,
    );

class CommunityViewModel extends AsyncNotifier<List<Community>> {
  @override
  FutureOr<List<Community>> build() async {
    return _repository.getMyCommunities();
  }

  CommunityRemoteRepository get _repository =>
      ref.read(communityRemoteRepositoryProvider);

  /// Silently refresh the list without triggering AsyncLoading
  Future<void> fetchMyCommunities() async {
    final fresh = await _repository.getMyCommunities();
    state = AsyncValue.data(fresh);
  }

  /// Join a community. Returns a [JoinResult] so callers can check
  /// whether the user joined immediately or is pending approval.
  Future<JoinResult> joinCommunity(String communityId) async {
    final result = await _repository.joinCommunity(communityId);
    await fetchMyCommunities();
    return result;
  }

  /// Leave a community
  Future<void> leaveCommunity(String communityId) async {
    await _repository.leaveCommunity(communityId);
    await fetchMyCommunities();
  }

  /// Create a new community
  Future<void> createCommunity({
    required String name,
    required String type,
    List<String>? parentColleges,
  }) async {
    await _repository.createCommunity(
      name: name,
      type: type,
      parentColleges: parentColleges,
    );
    await fetchMyCommunities();
  }

  /// Get a specific community details
  Future<Community> getCommunityDetails(String communityId) async {
    return _repository.getCommunityById(communityId);
  }
}
