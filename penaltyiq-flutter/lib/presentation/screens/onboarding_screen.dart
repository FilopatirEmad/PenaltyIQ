import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';
import 'package:shared_preferences/shared_preferences.dart';

import '../../core/theme/app_theme.dart';
import '../widgets/piq_widgets.dart';

/// Simple onboarding screen explaining the core value prop.
/// Designed with the Stitch "Performance Lab" aesthetic.
class OnboardingScreen extends StatefulWidget {
  const OnboardingScreen({super.key});

  @override
  State<OnboardingScreen> createState() => _OnboardingScreenState();
}

class _OnboardingScreenState extends State<OnboardingScreen> {
  final PageController _pageController = PageController();
  int _currentPage = 0;

  final List<_OnboardingPageData> _pages = const [
    _OnboardingPageData(
      title: 'WELCOME TO PERFORMANCE LAB',
      subtitle: 'Unlock elite biomechanical insights using just your smartphone camera.',
      icon: Icons.sports_soccer,
    ),
    _OnboardingPageData(
      title: 'RECORD YOUR KICK',
      subtitle: 'Select your target zone and record your penalty kick. Ensure full body visibility.',
      icon: Icons.videocam_rounded,
    ),
    _OnboardingPageData(
      title: 'GET PRO FEEDBACK',
      subtitle: 'Our physics engine and digital twin AI will analyse your biomechanics instantly.',
      icon: Icons.analytics_rounded,
    ),
  ];

  Future<void> _completeOnboarding() async {
    final prefs = await SharedPreferences.getInstance();
    await prefs.setBool('has_seen_onboarding', true);
    if (!mounted) return;
    context.go('/home');
  }

  void _nextPage() {
    if (_currentPage == _pages.length - 1) {
      _completeOnboarding();
    } else {
      _pageController.nextPage(
        duration: const Duration(milliseconds: 300),
        curve: Curves.easeInOut,
      );
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: PiqColors.background,
      body: SafeArea(
        child: Column(
          children: [
            Expanded(
              child: PageView.builder(
                controller: _pageController,
                onPageChanged: (i) => setState(() => _currentPage = i),
                itemCount: _pages.length,
                itemBuilder: (context, i) {
                  final data = _pages[i];
                  return Padding(
                    padding: const EdgeInsets.symmetric(horizontal: 32),
                    child: Column(
                      mainAxisAlignment: MainAxisAlignment.center,
                      children: [
                        Container(
                          width: 120, height: 120,
                          decoration: BoxDecoration(
                            shape: BoxShape.circle,
                            color: PiqColors.primary.withOpacity(0.1),
                            border: Border.all(color: PiqColors.primary.withOpacity(0.3)),
                          ),
                          child: Icon(data.icon, size: 48, color: PiqColors.primary),
                        ),
                        const SizedBox(height: 48),
                        Text(
                          data.title,
                          style: PiqTextStyles.headlineLg.copyWith(color: PiqColors.primary),
                          textAlign: TextAlign.center,
                        ),
                        const SizedBox(height: 16),
                        Text(
                          data.subtitle,
                          style: PiqTextStyles.bodyLg.copyWith(color: PiqColors.onSurfaceVariant),
                          textAlign: TextAlign.center,
                        ),
                      ],
                    ),
                  );
                },
              ),
            ),
            
            // ── Bottom Action ────────────────────────────────────────────────
            Padding(
              padding: const EdgeInsets.all(24),
              child: Column(
                children: [
                  Row(
                    mainAxisAlignment: MainAxisAlignment.center,
                    children: List.generate(
                      _pages.length,
                      (i) => AnimatedContainer(
                        duration: const Duration(milliseconds: 200),
                        margin: const EdgeInsets.symmetric(horizontal: 4),
                        width: _currentPage == i ? 24 : 8,
                        height: 8,
                        decoration: BoxDecoration(
                          color: _currentPage == i ? PiqColors.primary : PiqColors.surfaceVariant,
                          borderRadius: BorderRadius.circular(4),
                        ),
                      ),
                    ),
                  ),
                  const SizedBox(height: 32),
                  PiqPrimaryButton(
                    label: _currentPage == _pages.length - 1 ? 'GET STARTED' : 'NEXT',
                    onPressed: _nextPage,
                  ),
                ],
              ),
            ),
          ],
        ),
      ),
    );
  }
}

class _OnboardingPageData {
  const _OnboardingPageData({
    required this.title,
    required this.subtitle,
    required this.icon,
  });
  final String title;
  final String subtitle;
  final IconData icon;
}
