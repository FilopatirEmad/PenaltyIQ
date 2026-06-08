import 'dart:typed_data';

import 'package:file_picker/file_picker.dart';
import 'package:flutter/foundation.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:uuid/uuid.dart';

import '../../core/theme/app_theme.dart';
import '../../core/errors/app_exception.dart';
import '../../data/repositories/penaltyiq_repository.dart';
import '../../domain/providers/analysis_provider.dart';
import '../../domain/providers/calibration_provider.dart';
import '../widgets/piq_app_bar.dart';
import '../widgets/piq_widgets.dart';

/// Recording / Upload Screen — Stitch "Source Input" design.
///
/// Three-step flow visualised as numbered cards:
///   1. SELECT VIDEO  → file picker
///   2. PROCESS       → upload to backend
///   3. ANALYZE       → run biomechanical pipeline
///
/// All existing logic (processVideo, analyzeProcessedVideo) is preserved.
class RecordingScreen extends ConsumerStatefulWidget {
  const RecordingScreen({super.key, required this.goalZone});

  final String goalZone;

  @override
  ConsumerState<RecordingScreen> createState() => _RecordingScreenState();
}

class _RecordingScreenState extends ConsumerState<RecordingScreen> {
  bool _isProcessing = false;
  String? _errorMessage;
  String? _selectedVideoPath;
  Uint8List? _selectedVideoBytes;
  String? _selectedVideoName;
  Map<String, dynamic>? _processedPayload;
  String? _flowMessage;

  // ── Step tracking ──────────────────────────────────────────────────────────
  int get _currentStep {
    if (_processedPayload != null) return 3;
    if (_selectedVideoPath != null || _selectedVideoBytes != null) return 2;
    return 1;
  }

  // ── Handlers (identical logic to original) ─────────────────────────────────

  Future<void> _pickLocalVideo() async {
    setState(() {
      _errorMessage = null;
      _flowMessage = null;
    });

    final result = await FilePicker.platform.pickFiles(
      type: FileType.video,
      allowMultiple: false,
      withData: true,
    );

    if (result == null || result.files.isEmpty) {
      setState(() => _flowMessage = 'No video selected.');
      return;
    }

    final file = result.files.single;
    final hasPath = !kIsWeb && file.path != null && file.path!.isNotEmpty;
    final hasBytes = file.bytes != null && file.bytes!.isNotEmpty;
    if (!hasPath && !hasBytes) {
      setState(() => _flowMessage = 'Selected file is empty or inaccessible.');
      return;
    }

    setState(() {
      _selectedVideoPath = hasPath ? file.path : null;
      _selectedVideoBytes = file.bytes;
      _selectedVideoName = file.name;
      _processedPayload = null;
      _flowMessage = null;
    });
  }

  Future<void> _processSelectedVideo() async {
    final path  = _selectedVideoPath;
    final bytes = _selectedVideoBytes;
    if (path == null && (bytes == null || bytes.isEmpty)) {
      setState(() => _errorMessage = 'Select a local video first.');
      return;
    }

    setState(() {
      _isProcessing = true;
      _errorMessage = null;
      _flowMessage  = 'Uploading & extracting pose data…';
    });

    try {
      final sessionId = const Uuid().v4();
      final repo = ref.read(penaltyIqRepositoryProvider);
      final response = await repo.processVideo(
        videoPath:  path,
        videoBytes: bytes,
        fileName:   _selectedVideoName,
        sessionId:  sessionId,
        goalZone:   widget.goalZone,
      );

      setState(() {
        _processedPayload = response;
        _isProcessing     = false;
        _flowMessage      = 'Extraction complete. Ready to analyse.';
      });
    } catch (e) {
      setState(() {
        _isProcessing = false;
        _errorMessage = e is AppException ? e.message : e.toString();
      });
    }
  }

  Future<void> _analyzeProcessedVideo() async {
    final payload = _processedPayload;
    if (payload == null) {
      setState(() => _errorMessage = 'Process a video first.');
      return;
    }

    setState(() {
      _isProcessing = true;
      _errorMessage = null;
      _flowMessage  = 'Running biomechanical analysis…';
    });

    await ref.read(analysisProvider.notifier).submitFromProcessedPayload(
      processedPayload: payload,
      goalZone: widget.goalZone,
    );

    final state = ref.read(analysisProvider);
    if (!mounted) return;

    setState(() => _isProcessing = false);

    if (state is AnalysisSuccess) {
      context.go('/results');
      return;
    }
    if (state is AnalysisError) {
      setState(() => _errorMessage = state.message);
    }
  }

  // ── Build ──────────────────────────────────────────────────────────────────

  @override
  Widget build(BuildContext context) {
    if (_isProcessing) return _ProcessingOverlay(message: _flowMessage);

    return Scaffold(
      backgroundColor: PiqColors.background,
      appBar: PiqAppBar(
        title: 'SOURCE INPUT',
        showBack: true,
        trailing: _ZoneBadge(zone: widget.goalZone),
      ),
      body: SafeArea(
        top: false,
        child: SingleChildScrollView(
          padding: const EdgeInsets.fromLTRB(20, 24, 20, 120),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              // ── Header ────────────────────────────────────────────────
              Text('RECORD A NEW MOVEMENT', style: PiqTextStyles.labelCaps.copyWith(
                  color: PiqColors.primary, letterSpacing: 2)),
              const SizedBox(height: 4),
              Text(
                'Upload a pre-recorded video for analysis.',
                style: PiqTextStyles.bodyLg.copyWith(color: PiqColors.onSurfaceVariant),
              ),
              const SizedBox(height: 24),

              // ── Step cards ────────────────────────────────────────────
              _SourceCard(
                step: 1,
                isActive: _currentStep == 1,
                isDone: _currentStep > 1,
                title: 'Upload Video',
                subtitle: _selectedVideoName != null
                    ? 'Selected: $_selectedVideoName'
                    : 'Select an existing file from your device gallery.',
                icon: Icons.video_library_rounded,
                accentColor: PiqColors.primary,
                onTap: _pickLocalVideo,
              ),
              const SizedBox(height: 12),

              _SourceCard(
                step: 2,
                isActive: _currentStep == 2,
                isDone: _currentStep > 2,
                title: 'Process Video',
                subtitle: _currentStep > 1
                    ? (_processedPayload != null
                        ? 'Frames extracted. Ready to analyse.'
                        : 'Extract pose + ball data from the video.')
                    : 'Select a video first.',
                icon: Icons.cloud_upload_rounded,
                accentColor: PiqColors.secondary,
                onTap: _currentStep >= 2 && _processedPayload == null
                    ? _processSelectedVideo
                    : null,
              ),
              const SizedBox(height: 12),

              _SourceCard(
                step: 3,
                isActive: _currentStep == 3,
                isDone: false,
                title: 'Run Analysis',
                subtitle: _currentStep == 3
                    ? 'Activate physics engine + IK solver.'
                    : 'Process video first.',
                icon: Icons.analytics_rounded,
                accentColor: PiqColors.tertiary,
                onTap: _currentStep == 3 ? _analyzeProcessedVideo : null,
              ),

              // ── Feedback messages ──────────────────────────────────────
              if (_flowMessage != null) ...[
                const SizedBox(height: 20),
                _FlowMessage(message: _flowMessage!, isError: false),
              ],
              if (_errorMessage != null) ...[
                const SizedBox(height: 20),
                _FlowMessage(message: _errorMessage!, isError: true),
              ],
            ],
          ),
        ),
      ),
      bottomNavigationBar: _ActionBar(
        currentStep: _currentStep,
        processedPayload: _processedPayload,
        selectedName: _selectedVideoName,
        onPick:    _pickLocalVideo,
        onProcess: _processSelectedVideo,
        onAnalyze: _analyzeProcessedVideo,
      ),
    );
  }
}

// ─────────────────────────────────────────────────────────────────────────────
// Source Input Card (Stitch upload/record card style)
// ─────────────────────────────────────────────────────────────────────────────

class _SourceCard extends StatelessWidget {
  const _SourceCard({
    required this.step,
    required this.isActive,
    required this.isDone,
    required this.title,
    required this.subtitle,
    required this.icon,
    required this.accentColor,
    this.onTap,
  });

  final int step;
  final bool isActive;
  final bool isDone;
  final String title;
  final String subtitle;
  final IconData icon;
  final Color accentColor;
  final VoidCallback? onTap;

  @override
  Widget build(BuildContext context) {
    final enabled = onTap != null;
    return GestureDetector(
      onTap: onTap,
      child: AnimatedContainer(
        duration: const Duration(milliseconds: 200),
        padding: const EdgeInsets.all(20),
        decoration: BoxDecoration(
          color: isActive
              ? accentColor.withOpacity(0.07)
              : PiqColors.surfaceContainer,
          borderRadius: PiqRadius.borderXl,
          border: Border.all(
            color: isDone
                ? PiqColors.primary.withOpacity(0.5)
                : isActive
                    ? accentColor
                    : PiqColors.outlineVariant,
            width: isActive ? 1.5 : 1,
          ),
        ),
        child: Row(
          children: [
            // Step badge + icon
            Column(
              children: [
                Container(
                  width: 52, height: 52,
                  decoration: BoxDecoration(
                    shape: BoxShape.circle,
                    color: isDone
                        ? PiqColors.primary
                        : isActive
                            ? accentColor.withOpacity(0.15)
                            : PiqColors.surfaceContainerHigh,
                  ),
                  child: Icon(
                    isDone ? Icons.check : icon,
                    color: isDone
                        ? PiqColors.onPrimary
                        : isActive
                            ? accentColor
                            : PiqColors.onSurfaceVariant,
                    size: 24,
                  ),
                ),
              ],
            ),
            const SizedBox(width: 16),
            // Text
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    'STEP $step',
                    style: PiqTextStyles.labelCaps.copyWith(
                      color: isActive ? accentColor : PiqColors.onSurfaceVariant,
                    ),
                  ),
                  const SizedBox(height: 2),
                  Text(
                    title,
                    style: PiqTextStyles.headlineMd.copyWith(
                      fontSize: 18,
                      color: enabled || isDone
                          ? PiqColors.onSurface
                          : PiqColors.onSurfaceVariant,
                    ),
                  ),
                  const SizedBox(height: 4),
                  Text(
                    subtitle,
                    style: PiqTextStyles.bodyMd.copyWith(
                      color: PiqColors.onSurfaceVariant,
                      fontSize: 13,
                    ),
                  ),
                ],
              ),
            ),
            if (enabled)
              Icon(Icons.chevron_right, color: accentColor),
          ],
        ),
      ),
    );
  }
}

// ─────────────────────────────────────────────────────────────────────────────
// Bottom Action Bar
// ─────────────────────────────────────────────────────────────────────────────

class _ActionBar extends StatelessWidget {
  const _ActionBar({
    required this.currentStep,
    required this.processedPayload,
    required this.selectedName,
    required this.onPick,
    required this.onProcess,
    required this.onAnalyze,
  });

  final int currentStep;
  final Map<String, dynamic>? processedPayload;
  final String? selectedName;
  final VoidCallback onPick;
  final VoidCallback onProcess;
  final VoidCallback onAnalyze;

  @override
  Widget build(BuildContext context) {
    return Container(
      color: PiqColors.background,
      padding: EdgeInsets.fromLTRB(
          20, 12, 20, 12 + MediaQuery.of(context).padding.bottom),
      child: currentStep == 3
          ? PiqPrimaryButton(
              label: 'RUN ANALYSIS',
              icon: Icons.bolt,
              onPressed: onAnalyze,
            )
          : currentStep == 2
              ? PiqPrimaryButton(
                  label: 'PROCESS VIDEO',
                  icon: Icons.cloud_upload_rounded,
                  onPressed: onProcess,
                )
              : PiqPrimaryButton(
                  label: 'SELECT VIDEO',
                  icon: Icons.video_library_rounded,
                  onPressed: onPick,
                ),
    );
  }
}

// ─────────────────────────────────────────────────────────────────────────────
// Supporting widgets
// ─────────────────────────────────────────────────────────────────────────────

class _ZoneBadge extends StatelessWidget {
  const _ZoneBadge({required this.zone});
  final String zone;

  @override
  Widget build(BuildContext context) => PiqChip('Zone $zone');
}

class _FlowMessage extends StatelessWidget {
  const _FlowMessage({required this.message, required this.isError});
  final String message;
  final bool isError;

  @override
  Widget build(BuildContext context) {
    final color = isError ? PiqColors.error : PiqColors.primary;
    return Container(
      padding: const EdgeInsets.all(12),
      decoration: BoxDecoration(
        color: color.withOpacity(0.08),
        borderRadius: PiqRadius.borderLg,
        border: Border.all(color: color.withOpacity(0.3)),
      ),
      child: Row(
        children: [
          Icon(
            isError ? Icons.error_outline : Icons.check_circle_outline,
            color: color, size: 16,
          ),
          const SizedBox(width: 8),
          Expanded(
            child: Text(message,
                style: PiqTextStyles.bodyMd.copyWith(
                  color: color, fontSize: 13)),
          ),
        ],
      ),
    );
  }
}

class _ProcessingOverlay extends StatelessWidget {
  const _ProcessingOverlay({this.message});
  final String? message;

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: PiqColors.background,
      body: Center(
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            const SizedBox(
              width: 52, height: 52,
              child: CircularProgressIndicator(
                strokeWidth: 2.5,
                valueColor: AlwaysStoppedAnimation<Color>(PiqColors.primary),
              ),
            ),
            const SizedBox(height: 28),
            Text(
              'PROCESSING',
              style: PiqTextStyles.headlineMd.copyWith(
                fontFamily: 'SpaceGrotesk',
                color: PiqColors.primary,
                letterSpacing: 2,
              ),
            ),
            const SizedBox(height: 8),
            Text(
              message ?? 'Running pose estimation…',
              style: PiqTextStyles.bodyMd.copyWith(
                  color: PiqColors.onSurfaceVariant),
              textAlign: TextAlign.center,
            ),
          ],
        ),
      ),
    );
  }
}
