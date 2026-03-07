// lib/viewmodel/college_select_viewmodel.dart
import 'dart:async';
import 'package:campusassist/models/college_model.dart';
import 'package:flutter/foundation.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../repositories/college_select_remote_repository.dart';

final collegeSelectViewModelProvider =
    AsyncNotifierProvider<CollegeSelectViewModel, List<CollegeModel>>(
      CollegeSelectViewModel.new,
    );

class CollegeSelectViewModel extends AsyncNotifier<List<CollegeModel>> {
  @override
  FutureOr<List<CollegeModel>> build() async {
    debugPrint('[CollegeSelectViewModel] build: fetching initial college list');
    final results = await ref
        .read(collegeSelectRemoteRepositoryProvider)
        .searchColleges('');
    debugPrint(
      '[CollegeSelectViewModel] build: loaded ${results.length} colleges',
    );
    return results;
  }

  Future<void> searchColleges(String query) async {
    debugPrint('[CollegeSelectViewModel] searchColleges: query="$query"');
    state = const AsyncLoading();
    state = await AsyncValue.guard(() async {
      final results = await ref
          .read(collegeSelectRemoteRepositoryProvider)
          .searchColleges(query);
      debugPrint(
        '[CollegeSelectViewModel] searchColleges: got ${results.length} results for "$query"',
      );
      return results;
    });
    if (state.hasError) {
      debugPrint(
        '[CollegeSelectViewModel] searchColleges: error — ${state.error}',
      );
    }
  }
}
