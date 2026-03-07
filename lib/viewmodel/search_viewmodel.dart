// lib/viewmodel/search_viewmodel.dart
import 'dart:async';

import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_riverpod/legacy.dart';

import '../models/search_result_model.dart';
import '../repositories/search_remote_repository.dart';

// Holds the current search query string
final searchQueryProvider = StateProvider<String>((ref) => '');

// Holds the active type filter: 'all' | 'college' | 'community'
final searchTypeFilterProvider = StateProvider<String>((ref) => 'all');

class SearchState {
  final List<SearchResultItem> items;
  final int total;
  final int page;
  final bool hasMore;
  final bool isLoadingMore;

  const SearchState({
    this.items = const [],
    this.total = 0,
    this.page = 1,
    this.hasMore = false,
    this.isLoadingMore = false,
  });

  SearchState copyWith({
    List<SearchResultItem>? items,
    int? total,
    int? page,
    bool? hasMore,
    bool? isLoadingMore,
  }) {
    return SearchState(
      items: items ?? this.items,
      total: total ?? this.total,
      page: page ?? this.page,
      hasMore: hasMore ?? this.hasMore,
      isLoadingMore: isLoadingMore ?? this.isLoadingMore,
    );
  }
}

final searchViewModelProvider =
    AsyncNotifierProvider<SearchViewModel, SearchState>(SearchViewModel.new);

class SearchViewModel extends AsyncNotifier<SearchState> {
  static const int _pageSize = 20;
  Timer? _debounce;

  @override
  FutureOr<SearchState> build() => const SearchState();

  SearchRemoteRepository get _repo => ref.read(searchRemoteRepositoryProvider);

  void onQueryChanged(String query) {
    ref.read(searchQueryProvider.notifier).state = query;
    _debounce?.cancel();
    if (query.trim().isEmpty) {
      state = const AsyncValue.data(SearchState());
      return;
    }
    _debounce = Timer(const Duration(milliseconds: 400), () {
      search(query: query, reset: true);
    });
  }

  Future<void> search({required String query, bool reset = true}) async {
    if (query.trim().isEmpty) {
      state = const AsyncValue.data(SearchState());
      return;
    }

    final typeFilter = ref.read(searchTypeFilterProvider);

    if (reset) {
      state = const AsyncValue.loading();
    } else {
      // load more — keep existing items, just flag isLoadingMore
      final current = state.value ?? const SearchState();
      state = AsyncValue.data(current.copyWith(isLoadingMore: true));
    }

    try {
      final current = reset
          ? const SearchState()
          : (state.value ?? const SearchState());
      final nextPage = reset ? 1 : current.page + 1;

      final result = await _repo.search(
        query: query,
        type: typeFilter,
        page: nextPage,
        pageSize: _pageSize,
      );

      final merged = reset ? result.items : [...current.items, ...result.items];

      state = AsyncValue.data(
        SearchState(
          items: merged,
          total: result.total,
          page: result.page,
          hasMore: merged.length < result.total,
          isLoadingMore: false,
        ),
      );
    } catch (e, st) {
      state = AsyncValue.error(e, st);
    }
  }

  void setTypeFilter(String type) {
    ref.read(searchTypeFilterProvider.notifier).state = type;
    final q = ref.read(searchQueryProvider);
    final effectiveQuery = q.trim().isEmpty ? 'a' : q.trim();
    search(query: effectiveQuery, reset: true);
  }
}
