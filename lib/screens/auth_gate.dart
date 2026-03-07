// lib/screens/auth_gate.dart
import 'package:campusassist/screens/auth_screen.dart';
import 'package:campusassist/services/push_notification_service.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../viewmodel/auth_viewmodel.dart';
import 'main_screen.dart';

class AuthGate extends ConsumerStatefulWidget {
  const AuthGate({super.key});

  @override
  ConsumerState<AuthGate> createState() => _AuthGateState();
}

class _AuthGateState extends ConsumerState<AuthGate> {
  final _push = PushNotificationService();

  @override
  void initState() {
    super.initState();
    // Initialise local notification channel / permissions
    _push.init();
  }

  @override
  Widget build(BuildContext context) {
    final authState = ref.watch(authViewModelProvider);

    return authState.when(
      loading: () =>
          const Scaffold(body: Center(child: CircularProgressIndicator())),
      error: (_, __) => const AuthScreen(),
      data: (user) => user != null ? const MainScreen() : const AuthScreen(),
    );
  }
}
