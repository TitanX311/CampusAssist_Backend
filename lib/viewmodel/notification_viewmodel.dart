// lib/viewmodel/notification_viewmodel.dart
import 'dart:async';

import 'package:campusassist/models/notification_model.dart';
import 'package:campusassist/repositories/notification_repository.dart';
import 'package:campusassist/services/notification_websocket.dart';
import 'package:campusassist/services/push_notification_service.dart';
import 'package:flutter/foundation.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_riverpod/legacy.dart';

// ── Unread badge count ────────────────────────────────────────────────────────

final unreadCountProvider = StateProvider<int>((ref) => 0);

// ── Notification list state ───────────────────────────────────────────────────

class NotificationState {
  final List<AppNotification> items;
  final bool isLoading;
  final bool hasMore;
  final int page;
  final String? error;

  const NotificationState({
    this.items = const [],
    this.isLoading = false,
    this.hasMore = true,
    this.page = 1,
    this.error,
  });

  NotificationState copyWith({
    List<AppNotification>? items,
    bool? isLoading,
    bool? hasMore,
    int? page,
    String? error,
  }) => NotificationState(
    items: items ?? this.items,
    isLoading: isLoading ?? this.isLoading,
    hasMore: hasMore ?? this.hasMore,
    page: page ?? this.page,
    error: error,
  );
}

// ── Provider ──────────────────────────────────────────────────────────────────

final notificationViewModelProvider =
    AsyncNotifierProvider<NotificationViewModel, NotificationState>(
      NotificationViewModel.new,
    );

class NotificationViewModel extends AsyncNotifier<NotificationState> {
  NotificationWebSocket? _ws;
  StreamSubscription? _wsSub;

  /// Local notification service used to surface WS notifications as system
  /// notifications when the app is in the foreground.
  final _push = PushNotificationService();

  NotificationRepository get _repo => ref.read(notificationRepositoryProvider);

  @override
  Future<NotificationState> build() async {
    // Ensure local notification channel is ready
    await _push.init();

    // Wire WebSocket
    _ws = NotificationWebSocket(_repo.getAccessToken);
    await _ws!.connect();
    _wsSub = _ws!.stream.listen(_onWsNotification);

    // Clean up when provider is disposed
    ref.onDispose(() {
      _wsSub?.cancel();
      _ws?.disconnect();
    });

    // Load first page
    return _fetch(page: 1, current: const NotificationState());
  }

  // ── WebSocket ──────────────────────────────────────────────────────────────

  void _onWsNotification(AppNotification n) {
    debugPrint('[NotifVM] WS: ${n.type} — ${n.title}');

    // Show a system notification so the user sees it even when the app is open
    _push.showNotification(
      title: n.title,
      body: n.body,
      id: n.id.hashCode,
      data: {'type': n.type, 'data': n.data},
    );

    state = state.whenData((s) {
      final updated = [n, ...s.items.where((e) => e.id != n.id)];
      ref.read(unreadCountProvider.notifier).update((c) => c + 1);
      return s.copyWith(items: updated);
    });
  }

  // ── REST ───────────────────────────────────────────────────────────────────

  Future<NotificationState> _fetch({
    required int page,
    required NotificationState current,
  }) async {
    try {
      final result = await _repo.list(page: page);
      ref.read(unreadCountProvider.notifier).state = result.unreadCount;

      final merged = page == 1
          ? result.items
          : [...current.items, ...result.items];

      return current.copyWith(
        items: merged,
        page: page,
        isLoading: false,
        hasMore: merged.length < result.total,
        error: null,
      );
    } catch (e) {
      return current.copyWith(isLoading: false, error: e.toString());
    }
  }

  Future<void> refresh() async {
    state = state.whenData((s) => s.copyWith(isLoading: true));
    state = AsyncData(
      await _fetch(page: 1, current: state.value ?? const NotificationState()),
    );
  }

  Future<void> loadMore() async {
    final s = state.value;
    if (s == null || s.isLoading || !s.hasMore) return;
    state = AsyncData(s.copyWith(isLoading: true));
    state = AsyncData(await _fetch(page: s.page + 1, current: s));
  }

  // ── Actions ────────────────────────────────────────────────────────────────

  Future<void> markRead(String id) async {
    await _repo.markRead(id);
    state = state.whenData((s) {
      final updated = s.items.map((n) {
        if (n.id != id || n.read) return n;
        ref
            .read(unreadCountProvider.notifier)
            .update((c) => (c - 1).clamp(0, 999));
        return n.copyWith(read: true);
      }).toList();
      return s.copyWith(items: updated);
    });
  }

  Future<void> markAllRead() async {
    await _repo.markAllRead();
    state = state.whenData(
      (s) => s.copyWith(
        items: s.items.map((n) => n.copyWith(read: true)).toList(),
      ),
    );
    ref.read(unreadCountProvider.notifier).state = 0;
  }

  Future<void> delete(String id) async {
    await _repo.delete(id);
    state = state.whenData(
      (s) => s.copyWith(items: s.items.where((n) => n.id != id).toList()),
    );
  }

  // ── Reconnect after login ──────────────────────────────────────────────────

  Future<void> reconnectWebSocket() async {
    _wsSub?.cancel();
    _ws?.disconnect();
    _ws = NotificationWebSocket(_repo.getAccessToken);
    await _ws!.connect();
    _wsSub = _ws!.stream.listen(_onWsNotification);
  }
}
