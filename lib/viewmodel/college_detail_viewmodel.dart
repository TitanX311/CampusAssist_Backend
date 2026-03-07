// lib/viewmodel/college_detail_viewmodel.dart
import 'dart:async';

import 'package:campusassist/models/college_model.dart';
import 'package:campusassist/models/community_model.dart';
import 'package:campusassist/repositories/college_detail_remote_repository.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

// ── State ─────────────────────────────────────────────────────────────────────

class CollegeDetailState {
  final CollegeModel? college;
  final List<Community> communities;
  final bool isLoadingCommunities;
  final bool hasMoreCommunities;
  final int communitiesPage;
  final String? communitiesError;

  const CollegeDetailState({
    this.college,
    this.communities = const [],
    this.isLoadingCommunities = false,
    this.hasMoreCommunities = false,
    this.communitiesPage = 1,
    this.communitiesError,
  });

  CollegeDetailState copyWith({
    CollegeModel? college,
    List<Community>? communities,
    bool? isLoadingCommunities,
    bool? hasMoreCommunities,
    int? communitiesPage,
    String? communitiesError,
  }) {
    return CollegeDetailState(
      college: college ?? this.college,
      communities: communities ?? this.communities,
      isLoadingCommunities: isLoadingCommunities ?? this.isLoadingCommunities,
      hasMoreCommunities: hasMoreCommunities ?? this.hasMoreCommunities,
      communitiesPage: communitiesPage ?? this.communitiesPage,
      communitiesError: communitiesError,
    );
  }
}

// ── Provider ──────────────────────────────────────────────────────────────────

final collegeDetailViewModelProvider = AsyncNotifierProvider.autoDispose
    .family<CollegeDetailViewModel, CollegeDetailState, String>(
      CollegeDetailViewModel.new,
    );

class CollegeDetailViewModel extends AsyncNotifier<CollegeDetailState> {
  CollegeDetailViewModel(this.collegeId);
  final String collegeId;

  static const int _pageSize = 20;

  CollegeDetailRemoteRepository get _repo =>
      ref.read(collegeDetailRemoteRepositoryProvider);

  @override
  FutureOr<CollegeDetailState> build() async {
    final college = await _repo.getCollege(collegeId);
    final communities = await _repo.getCollegeCommunities(
      collegeId,
      page: 1,
      pageSize: _pageSize,
    );
    return CollegeDetailState(
      college: college,
      communities: communities,
      hasMoreCommunities: communities.length == _pageSize,
      communitiesPage: 1,
    );
  }

  Future<void> retry() async {
    state = const AsyncLoading();
    state = await AsyncValue.guard(() async => await build());
  }

  /// Silent refresh (pull-to-refresh) – keeps current data visible while reloading.
  Future<void> refresh() async {
    final college = await _repo.getCollege(collegeId);
    final communities = await _repo.getCollegeCommunities(
      collegeId,
      page: 1,
      pageSize: _pageSize,
    );
    state = AsyncData(
      CollegeDetailState(
        college: college,
        communities: communities,
        hasMoreCommunities: communities.length == _pageSize,
        communitiesPage: 1,
      ),
    );
  }

  Future<void> loadMoreCommunities() async {
    final current = state.value;
    if (current == null ||
        current.isLoadingCommunities ||
        !current.hasMoreCommunities)
      return;

    state = AsyncData(current.copyWith(isLoadingCommunities: true));
    try {
      final nextPage = current.communitiesPage + 1;
      final more = await _repo.getCollegeCommunities(
        collegeId,
        page: nextPage,
        pageSize: _pageSize,
      );
      final merged = [...current.communities, ...more];
      state = AsyncData(
        current.copyWith(
          communities: merged,
          isLoadingCommunities: false,
          hasMoreCommunities: more.length == _pageSize,
          communitiesPage: nextPage,
        ),
      );
    } catch (e) {
      state = AsyncData(
        current.copyWith(
          isLoadingCommunities: false,
          communitiesError: e.toString(),
        ),
      );
    }
  }
}
