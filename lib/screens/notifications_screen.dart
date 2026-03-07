// lib/screens/notifications_screen.dart
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:timeago/timeago.dart' as timeago;

import '../models/notification_model.dart';
import '../theme/app_theme.dart';
import '../viewmodel/notification_viewmodel.dart';
import '../widgets/skeleton_loaders.dart';

class NotificationsScreen extends ConsumerWidget {
  const NotificationsScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final nAsync = ref.watch(notificationViewModelProvider);

    return Scaffold(
      backgroundColor: AppTheme.surface,
      appBar: AppBar(
        backgroundColor: AppTheme.cardBg,
        elevation: 0,
        title: const Text(
          'Notifications',
          style: TextStyle(
            fontSize: 17,
            fontWeight: FontWeight.w800,
            color: AppTheme.textPrimary,
          ),
        ),
        actions: [
          nAsync.whenOrNull(
                data: (s) => s.items.any((n) => !n.read)
                    ? TextButton(
                        onPressed: () => ref
                            .read(notificationViewModelProvider.notifier)
                            .markAllRead(),
                        child: const Text(
                          'Mark all read',
                          style: TextStyle(
                            color: AppTheme.primary,
                            fontWeight: FontWeight.w600,
                            fontSize: 13,
                          ),
                        ),
                      )
                    : const SizedBox.shrink(),
              ) ??
              const SizedBox.shrink(),
          const SizedBox(width: 8),
        ],
      ),
      body: nAsync.when(
        loading: () => const _SkeletonNotificationList(),
        error: (e, _) => Center(
          child: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              const Icon(
                Icons.cloud_off_rounded,
                size: 48,
                color: AppTheme.textLight,
              ),
              const SizedBox(height: 12),
              Text(
                e.toString().replaceFirst('Exception: ', ''),
                textAlign: TextAlign.center,
                style: const TextStyle(
                  color: AppTheme.textSecondary,
                  fontSize: 13,
                ),
              ),
              const SizedBox(height: 16),
              TextButton.icon(
                onPressed: () =>
                    ref.read(notificationViewModelProvider.notifier).refresh(),
                icon: const Icon(Icons.refresh_rounded),
                label: const Text('Retry'),
              ),
            ],
          ),
        ),
        data: (state) {
          if (state.items.isEmpty) {
            return Center(
              child: Column(
                mainAxisAlignment: MainAxisAlignment.center,
                children: [
                  Icon(
                    Icons.notifications_none_rounded,
                    size: 64,
                    color: AppTheme.textLight.withOpacity(0.4),
                  ),
                  const SizedBox(height: 16),
                  const Text(
                    'No notifications yet',
                    style: TextStyle(
                      fontWeight: FontWeight.w600,
                      color: AppTheme.textSecondary,
                      fontSize: 16,
                    ),
                  ),
                  const SizedBox(height: 6),
                  const Text(
                    'You\'ll be notified when something happens.',
                    style: TextStyle(color: AppTheme.textLight, fontSize: 13),
                  ),
                ],
              ),
            );
          }

          return RefreshIndicator(
            color: AppTheme.primary,
            onRefresh: () =>
                ref.read(notificationViewModelProvider.notifier).refresh(),
            child: ListView.builder(
              padding: const EdgeInsets.symmetric(vertical: 8),
              itemCount: state.items.length + (state.hasMore ? 1 : 0),
              itemBuilder: (context, i) {
                if (i == state.items.length) {
                  // Load-more trigger
                  ref.read(notificationViewModelProvider.notifier).loadMore();
                  return const Padding(
                    padding: EdgeInsets.all(16),
                    child: Center(
                      child: CircularProgressIndicator(
                        strokeWidth: 2,
                        color: AppTheme.primary,
                      ),
                    ),
                  );
                }

                final n = state.items[i];
                return _NotificationTile(
                  notification: n,
                  onTap: () {
                    if (!n.read) {
                      ref
                          .read(notificationViewModelProvider.notifier)
                          .markRead(n.id);
                    }
                  },
                  onDelete: () => ref
                      .read(notificationViewModelProvider.notifier)
                      .delete(n.id),
                );
              },
            ),
          );
        },
      ),
    );
  }
}

// ── Notification Tile ─────────────────────────────────────────────────────────

class _NotificationTile extends StatelessWidget {
  final AppNotification notification;
  final VoidCallback onTap;
  final VoidCallback onDelete;

  const _NotificationTile({
    required this.notification,
    required this.onTap,
    required this.onDelete,
  });

  IconData get _icon => switch (notification.type) {
    NotificationType.likePost => Icons.arrow_upward_rounded,
    NotificationType.commentPost => Icons.chat_bubble_outline_rounded,
    NotificationType.likeComment => Icons.thumb_up_alt_outlined,
    NotificationType.replyComment => Icons.reply_rounded,
    NotificationType.joinRequest => Icons.person_add_outlined,
    NotificationType.joinAccepted => Icons.check_circle_outline_rounded,
    NotificationType.newPost => Icons.article_outlined,
    NotificationType.unknown => Icons.notifications_outlined,
  };

  Color get _iconColor => switch (notification.type) {
    NotificationType.likePost ||
    NotificationType.likeComment => AppTheme.accent,
    NotificationType.commentPost ||
    NotificationType.replyComment => AppTheme.primary,
    NotificationType.joinRequest ||
    NotificationType.joinAccepted => AppTheme.secondary,
    NotificationType.newPost => AppTheme.info,
    NotificationType.unknown => AppTheme.textSecondary,
  };

  @override
  Widget build(BuildContext context) {
    final unread = !notification.read;
    return Dismissible(
      key: ValueKey(notification.id),
      direction: DismissDirection.endToStart,
      background: Container(
        alignment: Alignment.centerRight,
        padding: const EdgeInsets.only(right: 20),
        color: AppTheme.error.withOpacity(0.1),
        child: const Icon(Icons.delete_outline_rounded, color: AppTheme.error),
      ),
      onDismissed: (_) => onDelete(),
      child: InkWell(
        onTap: onTap,
        child: Container(
          padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 14),
          decoration: BoxDecoration(
            color: unread
                ? AppTheme.primary.withOpacity(0.05)
                : AppTheme.cardBg,
            border: Border(
              bottom: BorderSide(color: AppTheme.divider, width: 0.5),
            ),
          ),
          child: Row(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              // Icon badge
              Container(
                width: 42,
                height: 42,
                decoration: BoxDecoration(
                  color: _iconColor.withOpacity(0.12),
                  shape: BoxShape.circle,
                ),
                child: Icon(_icon, size: 20, color: _iconColor),
              ),
              const SizedBox(width: 12),
              // Content
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      notification.title,
                      style: TextStyle(
                        fontSize: 14,
                        fontWeight: unread ? FontWeight.w700 : FontWeight.w500,
                        color: AppTheme.textPrimary,
                      ),
                    ),
                    const SizedBox(height: 3),
                    Text(
                      notification.body,
                      style: const TextStyle(
                        fontSize: 13,
                        color: AppTheme.textSecondary,
                        height: 1.4,
                      ),
                    ),
                    const SizedBox(height: 6),
                    Text(
                      timeago.format(notification.createdAt),
                      style: const TextStyle(
                        fontSize: 11,
                        color: AppTheme.textLight,
                      ),
                    ),
                  ],
                ),
              ),
              // Unread dot
              if (unread)
                Container(
                  width: 8,
                  height: 8,
                  margin: const EdgeInsets.only(top: 4),
                  decoration: const BoxDecoration(
                    color: AppTheme.primary,
                    shape: BoxShape.circle,
                  ),
                ),
            ],
          ),
        ),
      ),
    );
  }
}

// ── Skeleton ──────────────────────────────────────────────────────────────────

class _SkeletonNotificationList extends StatelessWidget {
  const _SkeletonNotificationList();

  @override
  Widget build(BuildContext context) {
    return ListView.builder(
      padding: const EdgeInsets.symmetric(vertical: 8),
      itemCount: 6,
      itemBuilder: (_, __) => const _SkeletonNotificationTile(),
    );
  }
}

class _SkeletonNotificationTile extends StatelessWidget {
  const _SkeletonNotificationTile();

  @override
  Widget build(BuildContext context) {
    return Shimmer(
      child: Container(
        padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 14),
        decoration: BoxDecoration(
          color: AppTheme.cardBg,
          border: Border(
            bottom: BorderSide(color: AppTheme.divider, width: 0.5),
          ),
        ),
        child: Row(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Container(
              width: 42,
              height: 42,
              decoration: const BoxDecoration(
                color: AppTheme.divider,
                shape: BoxShape.circle,
              ),
            ),
            const SizedBox(width: 12),
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: const [
                  _Bone(width: 140, height: 12),
                  SizedBox(height: 8),
                  _Bone(width: double.infinity, height: 11),
                  SizedBox(height: 5),
                  _Bone(width: 200, height: 11),
                  SizedBox(height: 8),
                  _Bone(width: 60, height: 10),
                ],
              ),
            ),
          ],
        ),
      ),
    );
  }
}

// Re-export the private _Bone from skeleton_loaders via a local copy
class _Bone extends StatelessWidget {
  final double width;
  final double height;

  const _Bone({required this.width, required this.height});

  @override
  Widget build(BuildContext context) => Container(
    width: width,
    height: height,
    decoration: BoxDecoration(
      color: AppTheme.divider,
      borderRadius: BorderRadius.circular(6),
    ),
  );
}
