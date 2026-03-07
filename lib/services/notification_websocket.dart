// lib/services/notification_websocket.dart
import 'dart:async';
import 'dart:convert';

import 'package:campusassist/core/server_constants.dart';
import 'package:campusassist/models/notification_model.dart';
import 'package:flutter/foundation.dart';
import 'package:web_socket_channel/web_socket_channel.dart';

/// Manages the WebSocket connection to
/// ws://host/api/notifications/ws?token=<jwt>
///
/// Reconnects automatically with exponential back-off (1s → 30s).
class NotificationWebSocket {
  static final _wsBase = ServerConstants.baseURL
      .replaceFirst('http://', 'ws://')
      .replaceFirst('https://', 'wss://');

  final Future<String?> Function() _tokenProvider;

  WebSocketChannel? _channel;
  StreamSubscription? _sub;
  Timer? _reconnectTimer;
  Duration _backoff = const Duration(seconds: 1);
  bool _disposed = false;

  final _controller = StreamController<AppNotification>.broadcast();

  /// Fires every time a notification arrives over the socket.
  Stream<AppNotification> get stream => _controller.stream;

  NotificationWebSocket(this._tokenProvider);

  Future<void> connect() async {
    if (_disposed) return;
    _sub?.cancel();
    _channel?.sink.close();

    final token = await _tokenProvider();
    if (token == null) {
      debugPrint('[WS] No token — skipping WebSocket connect');
      return;
    }

    final uri = Uri.parse('$_wsBase/api/notifications/ws?token=$token');
    debugPrint('[WS] Connecting → $uri');

    try {
      _channel = WebSocketChannel.connect(uri);
      await _channel!.ready;
      _backoff = const Duration(seconds: 1); // reset on success
      debugPrint('[WS] Connected');

      _sub = _channel!.stream.listen(
        _onMessage,
        onError: (e) {
          debugPrint('[WS] Error: $e');
          _scheduleReconnect();
        },
        onDone: () {
          debugPrint('[WS] Closed');
          if (!_disposed) _scheduleReconnect();
        },
      );
    } catch (e) {
      debugPrint('[WS] Connect failed: $e');
      _scheduleReconnect();
    }
  }

  void _onMessage(dynamic raw) {
    try {
      final json = jsonDecode(raw as String) as Map<String, dynamic>;
      final notification = AppNotification.fromJson(json);
      debugPrint('[WS] Received: ${notification.type} — ${notification.title}');
      _controller.add(notification);
    } catch (e) {
      debugPrint('[WS] Could not parse message: $e');
    }
  }

  void _scheduleReconnect() {
    if (_disposed) return;
    debugPrint('[WS] Reconnect in ${_backoff.inSeconds}s');
    _reconnectTimer?.cancel();
    _reconnectTimer = Timer(_backoff, () {
      _backoff = Duration(seconds: (_backoff.inSeconds * 2).clamp(1, 30));
      connect();
    });
  }

  void disconnect() {
    _disposed = true;
    _reconnectTimer?.cancel();
    _sub?.cancel();
    _channel?.sink.close();
    _controller.close();
    debugPrint('[WS] Disconnected');
  }
}
