// lib/services/push_notification_service.dart
//
// Pure local-notification service — no Firebase.
// Notifications arrive via the backend WebSocket; this service renders them
// as Android / iOS system notifications while the app is in the foreground.

import 'dart:convert';

import 'package:flutter/foundation.dart';
import 'package:flutter_local_notifications/flutter_local_notifications.dart';

class PushNotificationService {
  static const _channelId = 'campus_assist_channel';
  static const _channelName = 'CampusAssist';
  static const _channelDesc = 'CampusAssist notifications';

  final FlutterLocalNotificationsPlugin _localNotif =
      FlutterLocalNotificationsPlugin();

  /// Callback fired when the user taps a notification (carries the payload map).
  void Function(Map<String, dynamic> data)? onNotificationTap;

  bool _initialized = false;

  Future<void> init() async {
    if (_initialized) return;
    _initialized = true;

    const androidInit = AndroidInitializationSettings('@mipmap/ic_launcher');
    const iosInit = DarwinInitializationSettings(
      requestAlertPermission: true,
      requestBadgePermission: true,
      requestSoundPermission: true,
    );

    // flutter_local_notifications ≥ 17 uses named params
    await _localNotif.initialize(
      settings: const InitializationSettings(
        android: androidInit,
        iOS: iosInit,
      ),
      onDidReceiveNotificationResponse: _onLocalTap,
    );

    // Create Android notification channel
    await _localNotif
        .resolvePlatformSpecificImplementation<
          AndroidFlutterLocalNotificationsPlugin
        >()
        ?.createNotificationChannel(
          const AndroidNotificationChannel(
            _channelId,
            _channelName,
            description: _channelDesc,
            importance: Importance.high,
          ),
        );

    // Request permission on Android 13+
    await _localNotif
        .resolvePlatformSpecificImplementation<
          AndroidFlutterLocalNotificationsPlugin
        >()
        ?.requestNotificationsPermission();

    debugPrint('[PushNotif] Initialized (local-only, no Firebase)');
  }

  /// Show a local notification. Call this when a WebSocket message arrives.
  Future<void> showNotification({
    required String title,
    required String body,
    Map<String, dynamic>? data,
    int id = 0,
  }) async {
    await _localNotif.show(
      id: id,
      title: title,
      body: body,
      notificationDetails: NotificationDetails(
        android: const AndroidNotificationDetails(
          _channelId,
          _channelName,
          channelDescription: _channelDesc,
          importance: Importance.high,
          priority: Priority.high,
          icon: '@mipmap/ic_launcher',
        ),
        iOS: const DarwinNotificationDetails(),
      ),
      payload: data != null ? jsonEncode(data) : null,
    );
  }

  void _onLocalTap(NotificationResponse response) {
    if (response.payload == null) return;
    try {
      final data = jsonDecode(response.payload!) as Map<String, dynamic>;
      onNotificationTap?.call(data);
    } catch (_) {}
  }
}
