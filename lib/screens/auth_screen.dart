// lib/screens/auth_gate.dart
import 'package:campusassist/repositories/auth_remote_repository.dart';
import 'package:campusassist/screens/main_screen.dart';
import 'package:campusassist/viewmodel/auth_viewmodel.dart';
import 'package:campusassist/widgets/app_logo_icon.dart';
import 'package:dio/dio.dart';
import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../theme/app_theme.dart';
import '../widgets/social_button.dart';

class AuthScreen extends ConsumerStatefulWidget {
  const AuthScreen({super.key});

  @override
  ConsumerState<AuthScreen> createState() => _AuthScreenState();
}

class _AuthScreenState extends ConsumerState<AuthScreen>
    with SingleTickerProviderStateMixin {
  late AnimationController _animCtrl;
  late Animation<double> _fadeIn;
  late Animation<Offset> _slideUp;

  bool _isLogin = true;
  bool _loading = false;
  bool _obscurePassword = true;

  final _emailCtrl = TextEditingController();
  final _passwordCtrl = TextEditingController();
  final _nameCtrl = TextEditingController();

  final _formKey = GlobalKey<FormState>();

  @override
  void initState() {
    super.initState();
    _animCtrl = AnimationController(
      vsync: this,
      duration: const Duration(milliseconds: 900),
    );
    _fadeIn = CurvedAnimation(parent: _animCtrl, curve: Curves.easeOut);
    _slideUp = Tween<Offset>(
      begin: const Offset(0, 0.12),
      end: Offset.zero,
    ).animate(CurvedAnimation(parent: _animCtrl, curve: Curves.easeOutCubic));
    _animCtrl.forward();
  }

  @override
  void dispose() {
    _animCtrl.dispose();
    _emailCtrl.dispose();
    _passwordCtrl.dispose();
    _nameCtrl.dispose();
    super.dispose();
  }

  Future<void> _signIn() async {
    if (!_formKey.currentState!.validate()) return;

    setState(() => _loading = true);

    try {
      await ref
          .read(authViewModelProvider.notifier)
          .signIn(
            email: _emailCtrl.text.trim(),
            password: _passwordCtrl.text.trim(),
          );
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text(e.toString()), backgroundColor: Colors.red),
        );
      }
    }

    if (mounted) {
      setState(() => _loading = false);
    }
  }

  Future<void> _createAccount() async {
    if (!_formKey.currentState!.validate()) return;

    setState(() => _loading = true);

    try {
      await ref
          .read(authViewModelProvider.notifier)
          .createAccount(
            name: _nameCtrl.text.trim(),
            email: _emailCtrl.text.trim(),
            password: _passwordCtrl.text.trim(),
          );
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text(e.toString()), backgroundColor: Colors.red),
        );
      }
    }

    if (mounted) {
      setState(() => _loading = false);
    }
  }

  Future<void> _submit() async {
    if (_isLogin) {
      await _signIn();
    } else {
      await _createAccount();
    }
  }

  void _switchMode() {
    _animCtrl.reset();
    setState(() => _isLogin = !_isLogin);
    _animCtrl.forward();
  }

  @override
  Widget build(BuildContext context) {
    final size = MediaQuery.of(context).size;

    // // React to auth state changes from Google Sign-In
    // ref.listen<AsyncValue<dynamic>>(authViewModelProvider, (previous, next) {
    //   next.whenOrNull(
    //     data: (user) {
    //       if (user != null && mounted) {
    //         Navigator.of(context).pushAndRemoveUntil(
    //           MaterialPageRoute(builder: (_) => const CollegeSelectScreen()),
    //           (route) => false,
    //         );
    //       }
    //     },
    //     error: (err, _) {
    //       if (mounted) {
    //         ScaffoldMessenger.of(context).showSnackBar(
    //           SnackBar(
    //             content: Text(err.toString()),
    //             backgroundColor: Colors.red,
    //           ),
    //         );
    //       }
    //     },
    //   );
    // });

    return Scaffold(
      backgroundColor: AppTheme.surface,
      body: AnnotatedRegion<SystemUiOverlayStyle>(
        value: const SystemUiOverlayStyle(
          statusBarColor: Colors.transparent,
          statusBarIconBrightness: Brightness.dark,
        ),
        child: Stack(
          children: [
            // ── Decorative top blob ──────────────────────────────────────
            Positioned(
              top: -60,
              right: -60,
              child: Container(
                width: 240,
                height: 240,
                decoration: BoxDecoration(
                  shape: BoxShape.circle,
                  gradient: RadialGradient(
                    colors: [
                      AppTheme.primaryLight.withOpacity(0.35),
                      AppTheme.primary.withOpacity(0.0),
                    ],
                  ),
                ),
              ),
            ),
            Positioned(
              top: 40,
              left: -80,
              child: Container(
                width: 200,
                height: 200,
                decoration: BoxDecoration(
                  shape: BoxShape.circle,
                  gradient: RadialGradient(
                    colors: [
                      AppTheme.accent.withOpacity(0.18),
                      AppTheme.accent.withOpacity(0.0),
                    ],
                  ),
                ),
              ),
            ),

            // ── Main content ─────────────────────────────────────────────
            SafeArea(
              child: SingleChildScrollView(
                padding: const EdgeInsets.symmetric(horizontal: 24),
                child: FadeTransition(
                  opacity: _fadeIn,
                  child: SlideTransition(
                    position: _slideUp,
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        const SizedBox(height: 40),

                        // ── Logo ─────────────────────────────────────────
                        Center(
                          child: Column(
                            children: [
                              const AppLogoIcon.large(),
                              const SizedBox(height: 14),
                              const Text(
                                'CampusAssist',
                                style: TextStyle(
                                  fontSize: 27,
                                  fontWeight: FontWeight.w800,
                                  color: AppTheme.textPrimary,
                                  letterSpacing: -0.6,
                                ),
                              ),
                              const SizedBox(height: 4),
                              const Text(
                                'Community Driven College Help',
                                style: TextStyle(
                                  fontSize: 13,
                                  color: AppTheme.textSecondary,
                                  fontWeight: FontWeight.w400,
                                ),
                              ),
                            ],
                          ),
                        ),

                        const SizedBox(height: 36),

                        // ── Tab switcher ──────────────────────────────────
                        Container(
                          decoration: BoxDecoration(
                            color: AppTheme.divider.withOpacity(0.6),
                            borderRadius: BorderRadius.circular(14),
                          ),
                          padding: const EdgeInsets.all(4),
                          child: Row(
                            children: [
                              _TabButton(
                                label: 'Sign In',
                                selected: _isLogin,
                                onTap: () {
                                  if (!_isLogin) _switchMode();
                                },
                              ),
                              _TabButton(
                                label: 'Create Account',
                                selected: !_isLogin,
                                onTap: () {
                                  if (_isLogin) _switchMode();
                                },
                              ),
                            ],
                          ),
                        ),

                        const SizedBox(height: 28),

                        // ── Form card ─────────────────────────────────────
                        Container(
                          decoration: BoxDecoration(
                            color: Colors.white,
                            borderRadius: BorderRadius.circular(20),
                            border: Border.all(color: AppTheme.divider),
                            boxShadow: [
                              BoxShadow(
                                color: Colors.black.withOpacity(0.05),
                                blurRadius: 20,
                                offset: const Offset(0, 4),
                              ),
                            ],
                          ),
                          padding: const EdgeInsets.all(24),
                          child: Form(
                            key: _formKey,
                            child: Column(
                              crossAxisAlignment: CrossAxisAlignment.start,
                              children: [
                                Text(
                                  _isLogin
                                      ? 'Welcome back 👋'
                                      : 'Join your campus 🎓',
                                  style: const TextStyle(
                                    fontSize: 20,
                                    fontWeight: FontWeight.w700,
                                    color: AppTheme.textPrimary,
                                  ),
                                ),
                                const SizedBox(height: 4),
                                Text(
                                  _isLogin
                                      ? 'Sign in to access your campus feed'
                                      : 'Create a free anonymous account',
                                  style: const TextStyle(
                                    fontSize: 13,
                                    color: AppTheme.textSecondary,
                                  ),
                                ),
                                const SizedBox(height: 24),

                                // Name field (sign up only)
                                if (!_isLogin) ...[
                                  _FieldLabel('Display Name'),
                                  const SizedBox(height: 6),
                                  TextFormField(
                                    controller: _nameCtrl,
                                    textInputAction: TextInputAction.next,
                                    decoration: InputDecoration(
                                      hintText: 'Your display name',
                                      prefixIcon: const Icon(
                                        Icons.badge_outlined,
                                        color: AppTheme.textLight,
                                        size: 20,
                                      ),
                                      suffixIcon: Tooltip(
                                        message:
                                            'This is the name others will see',
                                        child: Icon(
                                          Icons.info_outline_rounded,
                                          size: 18,
                                          color: AppTheme.textLight,
                                        ),
                                      ),
                                    ),
                                    validator: (v) =>
                                        (!_isLogin &&
                                            (v == null || v.trim().isEmpty))
                                        ? 'Name is required'
                                        : null,
                                  ),
                                  const SizedBox(height: 16),
                                ],

                                // Email
                                _FieldLabel('Email'),
                                const SizedBox(height: 6),
                                TextFormField(
                                  controller: _emailCtrl,
                                  keyboardType: TextInputType.emailAddress,
                                  textInputAction: TextInputAction.next,
                                  decoration: const InputDecoration(
                                    hintText: 'xyz@email.com',
                                    prefixIcon: Icon(
                                      Icons.email_outlined,
                                      color: AppTheme.textLight,
                                      size: 20,
                                    ),
                                  ),
                                  validator: (v) {
                                    if (v == null || v.trim().isEmpty) {
                                      return 'Email is required';
                                    }
                                    if (!v.contains('@')) {
                                      return 'Enter a valid email';
                                    }
                                    return null;
                                  },
                                ),
                                const SizedBox(height: 16),

                                // Password
                                _FieldLabel('Password'),
                                const SizedBox(height: 6),
                                TextFormField(
                                  controller: _passwordCtrl,
                                  obscureText: _obscurePassword,
                                  textInputAction: TextInputAction.done,
                                  onFieldSubmitted: (_) => _submit(),
                                  decoration: InputDecoration(
                                    hintText: _isLogin
                                        ? 'Enter your password'
                                        : 'Create a strong password',
                                    prefixIcon: const Icon(
                                      Icons.lock_outline_rounded,
                                      color: AppTheme.textLight,
                                      size: 20,
                                    ),
                                    suffixIcon: GestureDetector(
                                      onTap: () => setState(
                                        () => _obscurePassword =
                                            !_obscurePassword,
                                      ),
                                      child: Icon(
                                        _obscurePassword
                                            ? Icons.visibility_off_outlined
                                            : Icons.visibility_outlined,
                                        size: 20,
                                        color: AppTheme.textLight,
                                      ),
                                    ),
                                  ),
                                  validator: (v) {
                                    if (v == null || v.isEmpty) {
                                      return 'Password is required';
                                    }
                                    if (!_isLogin && v.length < 8) {
                                      return 'Must be at least 8 characters';
                                    }
                                    return null;
                                  },
                                ),

                                // Forgot password
                                if (_isLogin) ...[
                                  const SizedBox(height: 10),
                                  Align(
                                    alignment: Alignment.centerRight,
                                    child: GestureDetector(
                                      onTap: () {
                                        // TODO: Forgot password flow
                                      },
                                      child: const Text(
                                        'Forgot password?',
                                        style: TextStyle(
                                          fontSize: 12,
                                          color: AppTheme.primary,
                                          fontWeight: FontWeight.w600,
                                        ),
                                      ),
                                    ),
                                  ),
                                ],

                                const SizedBox(height: 24),

                                // Submit button
                                SizedBox(
                                  width: double.infinity,
                                  child: ElevatedButton(
                                    onPressed: _loading
                                        ? null
                                        : (_isLogin ? _signIn : _createAccount),
                                    style: ElevatedButton.styleFrom(
                                      padding: const EdgeInsets.symmetric(
                                        vertical: 16,
                                      ),
                                    ),
                                    child: _loading
                                        ? const SizedBox(
                                            width: 20,
                                            height: 20,
                                            child: CircularProgressIndicator(
                                              color: Colors.white,
                                              strokeWidth: 2.5,
                                            ),
                                          )
                                        : Text(
                                            _isLogin
                                                ? 'Sign In →'
                                                : 'Create Account →',
                                            style: const TextStyle(
                                              fontSize: 15,
                                              fontWeight: FontWeight.w700,
                                            ),
                                          ),
                                  ),
                                ),

                                const SizedBox(height: 20),

                                // Divider
                                Row(
                                  children: [
                                    const Expanded(
                                      child: Divider(
                                        color: AppTheme.divider,
                                        thickness: 1,
                                      ),
                                    ),
                                    Padding(
                                      padding: const EdgeInsets.symmetric(
                                        horizontal: 12,
                                      ),
                                      child: Text(
                                        'or continue with',
                                        style: TextStyle(
                                          fontSize: 12,
                                          color: AppTheme.textLight,
                                        ),
                                      ),
                                    ),
                                    const Expanded(
                                      child: Divider(
                                        color: AppTheme.divider,
                                        thickness: 1,
                                      ),
                                    ),
                                  ],
                                ),

                                const SizedBox(height: 16),

                                // Google SSO button
                                Consumer(
                                  builder: (context, ref, _) {
                                    final authState = ref.watch(
                                      authViewModelProvider,
                                    );
                                    final isLoading = authState is AsyncLoading;
                                    return SocialButton(
                                      label: isLoading
                                          ? 'Signing in...'
                                          : 'Continue with Google',
                                      iconPath: Icons.g_mobiledata_rounded,
                                      onTap: isLoading
                                          ? () {}
                                          : () async {
                                              final result = await ref
                                                  .read(
                                                    authViewModelProvider
                                                        .notifier,
                                                  )
                                                  .googleSignIn();

                                              if (!mounted) return;

                                              Navigator.of(
                                                context,
                                              ).pushReplacement(
                                                MaterialPageRoute(
                                                  builder: (_) =>
                                                      const MainScreen(),
                                                ),
                                              );
                                            },
                                    );
                                  },
                                ),
                              ],
                            ),
                          ),
                        ),

                        const SizedBox(height: 24),

                        // ── Privacy note ──────────────────────────────────
                        Center(
                          child: Padding(
                            padding: const EdgeInsets.symmetric(horizontal: 12),
                            child: RichText(
                              textAlign: TextAlign.center,
                              text: const TextSpan(
                                style: TextStyle(
                                  fontSize: 11.5,
                                  color: AppTheme.textLight,
                                  height: 1.6,
                                ),
                                children: [
                                  TextSpan(
                                    text: 'By continuing, you agree to our ',
                                  ),
                                  TextSpan(
                                    text: 'Terms of Service',
                                    style: TextStyle(
                                      color: AppTheme.primary,
                                      fontWeight: FontWeight.w600,
                                    ),
                                  ),
                                  TextSpan(text: ' and '),
                                  TextSpan(
                                    text: 'Privacy Policy',
                                    style: TextStyle(
                                      color: AppTheme.primary,
                                      fontWeight: FontWeight.w600,
                                    ),
                                  ),
                                  TextSpan(
                                    text:
                                        '.\nYour posts are always anonymous by default.',
                                  ),
                                ],
                              ),
                            ),
                          ),
                        ),

                        // ── Anonymity shield badge ────────────────────────
                        const SizedBox(height: 16),
                        Center(
                          child: Container(
                            padding: const EdgeInsets.symmetric(
                              horizontal: 14,
                              vertical: 8,
                            ),
                            decoration: BoxDecoration(
                              color: AppTheme.success.withOpacity(0.08),
                              borderRadius: BorderRadius.circular(24),
                              border: Border.all(
                                color: AppTheme.success.withOpacity(0.25),
                              ),
                            ),
                            child: const Row(
                              mainAxisSize: MainAxisSize.min,
                              children: [
                                Icon(
                                  Icons.shield_rounded,
                                  size: 15,
                                  color: AppTheme.success,
                                ),
                                SizedBox(width: 6),
                                Text(
                                  '100% Anonymous Posting',
                                  style: TextStyle(
                                    fontSize: 12,
                                    color: AppTheme.success,
                                    fontWeight: FontWeight.w600,
                                  ),
                                ),
                              ],
                            ),
                          ),
                        ),
                        const SizedBox(height: 40),
                      ],
                    ),
                  ),
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }
}

// ── Helper Widgets ─────────────────────────────────────────────────────────────

class _FieldLabel extends StatelessWidget {
  final String text;

  const _FieldLabel(this.text);

  @override
  Widget build(BuildContext context) {
    return Text(
      text,
      style: const TextStyle(
        fontSize: 13,
        fontWeight: FontWeight.w600,
        color: AppTheme.textPrimary,
      ),
    );
  }
}

class _TabButton extends StatelessWidget {
  final String label;
  final bool selected;
  final VoidCallback onTap;

  const _TabButton({
    required this.label,
    required this.selected,
    required this.onTap,
  });

  @override
  Widget build(BuildContext context) {
    return Expanded(
      child: GestureDetector(
        onTap: onTap,
        child: AnimatedContainer(
          duration: const Duration(milliseconds: 220),
          padding: const EdgeInsets.symmetric(vertical: 11),
          decoration: BoxDecoration(
            color: selected ? Colors.white : Colors.transparent,
            borderRadius: BorderRadius.circular(10),
            boxShadow: selected
                ? [
                    BoxShadow(
                      color: Colors.black.withOpacity(0.07),
                      blurRadius: 8,
                      offset: const Offset(0, 2),
                    ),
                  ]
                : [],
          ),
          child: Center(
            child: Text(
              label,
              style: TextStyle(
                fontSize: 13,
                fontWeight: FontWeight.w600,
                color: selected ? AppTheme.primary : AppTheme.textSecondary,
              ),
            ),
          ),
        ),
      ),
    );
  }
}
