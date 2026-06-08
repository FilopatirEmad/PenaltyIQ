import 'dart:typed_data';

import 'package:dio/dio.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:path/path.dart' as p;

import '../../core/constants/api_constants.dart';
import '../../core/errors/app_exception.dart';
import '../models/calibration_response.dart';
import '../models/analysis_response.dart';
import '../services/api_service.dart';

/// Data repository for all PenaltyIQ backend communication.
///
/// ## Standard Response Envelope
/// Every backend endpoint now returns:
///   ```json
///   { "success": true,  "data": <payload>, "message": "" }
///   { "success": false, "error": "<msg>",  "data": null  }
///   ```
/// The [_unwrap] helper validates and extracts `data` from this envelope.
///
/// Responsibilities:
///   1. Serialize request payloads into JSON.
///   2. Execute Dio HTTP calls.
///   3. Unwrap the standard response envelope.
///   4. Deserialize `data` into typed Freezed models.
///   5. Re-throw [AppException] subclasses for provider error handling.
class PenaltyIqRepository {
  const PenaltyIqRepository(this._dio);

  final Dio _dio;

  // ── Envelope Unwrapper ────────────────────────────────────────────────────

  /// Validates and extracts `data` from the standard backend envelope.
  ///
  /// Throws [ApiServerException] when:
  ///   - The response body is null.
  ///   - `success == false` (returns `error` field as message).
  ///   - `data` is null even on a success response.
  static Map<String, dynamic> _unwrap(Map<String, dynamic>? body) {
    if (body == null) {
      throw const ApiServerException('Empty response body from server.');
    }
    final success = body['success'];
    if (success == false) {
      final error = body['error']?.toString() ?? 'Unknown server error.';
      throw ApiServerException(error);
    }
    final data = body['data'];
    if (data == null) {
      throw const ApiServerException(
          'Server returned success but data was null.');
    }
    return data as Map<String, dynamic>;
  }

  // ── POST /process-video ────────────────────────────────────────────────────

  /// Upload a user-selected local video and request backend frame extraction.
  ///
  /// Returns the raw `data` map from the standard envelope, which contains:
  ///   - `session_id`, `fps`, `contact_frame_index`
  ///   - `calibration` (with `scale_m_per_px`, `segments_m`, `gate_passed`)
  ///   - `analysis_frames` (list of frame maps)
  ///   - `input_quality`, `warnings`
  Future<Map<String, dynamic>> processVideo({
    String? videoPath,
    Uint8List? videoBytes,
    String? fileName,
    required String sessionId,
    required String goalZone,
    String mode = 'full',
  }) async {
    try {
      final hasPath = videoPath != null && videoPath.isNotEmpty;
      final hasBytes = videoBytes != null && videoBytes.isNotEmpty;
      if (!hasPath && !hasBytes) {
        throw const ApiValidationException(
          'No video data provided. Select a video and try again.',
        );
      }

      final uploadFile = hasPath
          ? await MultipartFile.fromFile(
              videoPath,
              filename: fileName ?? p.basename(videoPath),
            )
          : MultipartFile.fromBytes(
              videoBytes!,
              filename: fileName ?? 'upload.mp4',
            );

      final formData = FormData.fromMap({
        'video': uploadFile,
        'session_id': sessionId,
        'goal_zone': goalZone,
        'mode': mode,
      });

      final response = await _dio.post<Map<String, dynamic>>(
        ApiConstants.processVideoEndpoint,
        data: formData,
        options: Options(
          contentType: 'multipart/form-data',
          headers: const {'Accept': 'application/json'},
        ),
      );

      return _unwrap(response.data);
    } on DioException catch (e) {
      final appEx = e.error;
      if (appEx is AppException) throw appEx;
      throw ApiServerException(e.message ?? 'Unknown process-video error.');
    }
  }

  // ── POST /calibrate ─────────────────────────────────────────────────────────

  /// Submit T-pose calibration frames to the backend stability gate.
  ///
  /// [SPEC §1.6.1]: Backend applies 2-second stability criterion.
  /// Returns [CalibrationResponse] with status "LOCKED", "FAILED", or
  /// "INSUFFICIENT_DATA".
  Future<CalibrationResponse> calibrate({
    required String sessionId,
    required List<Map<String, dynamic>> frames,
  }) async {
    try {
      final response = await _dio.post<Map<String, dynamic>>(
        ApiConstants.calibrateEndpoint,
        data: {
          'session_id': sessionId,
          'frames': frames,
        },
      );

      return CalibrationResponse.fromJson(_unwrap(response.data));
    } on DioException catch (e) {
      final appEx = e.error;
      if (appEx is AppException) throw appEx;
      throw ApiServerException(e.message ?? 'Unknown calibration error.');
    }
  }

  // ── POST /analyze ───────────────────────────────────────────────────────────

  /// Submit kick video frames for full biomechanical analysis.
  ///
  /// Pipeline triggered on backend:
  ///   signal_proc → physics_engine → ik_solver → digital_twin → coaching
  Future<AnalysisResponse> analyze({
    required String sessionId,
    required String goalZone,
    required Map<String, dynamic> calibration,
    required List<Map<String, dynamic>> frames,
    double fps = 60.0,
    int? contactFrameIndex,
  }) async {
    try {
      final response = await _dio.post<Map<String, dynamic>>(
        ApiConstants.analyzeEndpoint,
        data: {
          'session_id': sessionId,
          'goal_zone': goalZone,
          'calibration': calibration,
          'frames': frames,
          'fps': fps,
          if (contactFrameIndex != null)
            'contact_frame_index': contactFrameIndex,
        },
      );

      return AnalysisResponse.fromJson(_unwrap(response.data));
    } on DioException catch (e) {
      final appEx = e.error;
      if (appEx is AppException) throw appEx;
      throw ApiServerException(e.message ?? 'Unknown analysis error.');
    }
  }

  // ── POST /render-video ──────────────────────────────────────────────────────

  /// Submit the raw video and analysis results to generate an overlay video.
  /// Returns the raw bytes of the rendered MP4 file.
  Future<Uint8List> renderVideo({
    String? videoPath,
    Uint8List? videoBytes,
    required String analysisDataJson,
    required double scaleMPerPx,
  }) async {
    try {
      final hasPath = videoPath != null && videoPath.isNotEmpty;
      final hasBytes = videoBytes != null && videoBytes.isNotEmpty;
      if (!hasPath && !hasBytes) {
        throw const ApiValidationException('No video data provided.');
      }

      final uploadFile = hasPath
          ? await MultipartFile.fromFile(videoPath, filename: p.basename(videoPath))
          : MultipartFile.fromBytes(videoBytes!, filename: 'upload.mp4');

      final formData = FormData.fromMap({
        'video': uploadFile,
        'analysis_data': analysisDataJson,
        'scale_m_per_px': scaleMPerPx.toString(),
      });

      final response = await _dio.post<List<int>>(
        ApiConstants.renderVideoEndpoint,
        data: formData,
        options: Options(
          responseType: ResponseType.bytes,
          contentType: 'multipart/form-data',
        ),
      );

      if (response.data == null) {
        throw const ApiServerException('Empty response from render server.');
      }
      return Uint8List.fromList(response.data!);
    } on DioException catch (e) {
      final appEx = e.error;
      if (appEx is AppException) throw appEx;
      throw ApiServerException(e.message ?? 'Unknown render-video error.');
    }
  }

  // ── POST /auth/register ─────────────────────────────────────────────────────

  /// Register a new account. Returns JWT token and user info.
  Future<Map<String, dynamic>> register({
    required String name,
    required String email,
    required String password,
  }) async {
    try {
      final response = await _dio.post<Map<String, dynamic>>(
        ApiConstants.registerEndpoint,
        data: {'name': name, 'email': email, 'password': password},
      );
      return _unwrap(response.data);
    } on DioException catch (e) {
      final appEx = e.error;
      if (appEx is AppException) throw appEx;
      throw ApiServerException(e.message ?? 'Registration failed.');
    }
  }

  // ── POST /auth/login ────────────────────────────────────────────────────────

  /// Authenticate and return a JWT token.
  Future<Map<String, dynamic>> login({
    required String email,
    required String password,
  }) async {
    try {
      final response = await _dio.post<Map<String, dynamic>>(
        ApiConstants.loginEndpoint,
        data: {'email': email, 'password': password},
      );
      return _unwrap(response.data);
    } on DioException catch (e) {
      final appEx = e.error;
      if (appEx is AppException) throw appEx;
      throw ApiServerException(e.message ?? 'Login failed.');
    }
  }

  // ── GET /health ─────────────────────────────────────────────────────────────

  /// Health check — verify backend connectivity.
  Future<bool> checkHealth() async {
    try {
      final response = await _dio.get<Map<String, dynamic>>(
        ApiConstants.healthEndpoint,
      );
      return response.statusCode == 200 &&
          response.data?['status'] == 'ok';
    } catch (_) {
      return false;
    }
  }
}

/// Riverpod provider for the repository.
final penaltyIqRepositoryProvider = Provider<PenaltyIqRepository>((ref) {
  final dio = ref.watch(dioProvider);
  return PenaltyIqRepository(dio);
});