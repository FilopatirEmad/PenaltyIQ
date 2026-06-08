import 'package:dio/dio.dart';
import 'package:dio_smart_retry/dio_smart_retry.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import 'package:flutter/foundation.dart';

import '../../core/constants/api_constants.dart';
import '../../core/constants/app_constants.dart';
import '../../core/errors/app_exception.dart';
import '../../core/utils/logger.dart';

/// Dio HTTP client factory.
///
/// Configures:
///   - Base URL, timeouts
///   - Auth token interceptor (reads from [authTokenProvider])
///   - Request/response logging (debug mode only)
///   - Typed error transformation
class ApiService {
  ApiService._();

  static Dio createDio({String? authToken}) {
    final dio = Dio(
      BaseOptions(
        baseUrl: ApiConstants.baseUrl,
        connectTimeout: Duration(seconds: AppConstants.apiTimeoutS),
        receiveTimeout: Duration(seconds: AppConstants.videoProcessingTimeoutS),
        sendTimeout: Duration(seconds: AppConstants.videoProcessingTimeoutS),
        headers: {
          'Accept': 'application/json',
        },
      ),
    );

    // ── Auth interceptor ───────────────────────────────────────────────────
    // Adds Authorization: Bearer <token> to every request when a token exists.
    // When REQUIRE_AUTH=false on backend, this header is ignored safely.
    dio.interceptors.add(
      InterceptorsWrapper(
        onRequest: (options, handler) {
          if (authToken != null && authToken.isNotEmpty) {
            options.headers['Authorization'] = 'Bearer $authToken';
          }
          handler.next(options);
        },
      ),
    );

    // ── Logging interceptor (debug only) ──────────────────────────────────
    if (kDebugMode) {
      dio.interceptors.add(
        LogInterceptor(
          requestBody: false,   // Suppress large frame payloads in logs
          responseBody: false,  // Suppress large analysis JSON payloads preventing DartWorker crash
          requestHeader: true,
          responseHeader: false,
          error: true,
          logPrint: (obj) => AppLogger.debug('[ApiService] $obj'),
        ),
      );
    }

    // ── Retry interceptor ──────────────────────────────────────────────────
    dio.interceptors.add(
      RetryInterceptor(
        dio: dio,
        logPrint: kDebugMode ? (message) => AppLogger.warning('[Retry] $message') : print,
        retries: 1, // 1 retry max
        retryDelays: const [
          Duration(seconds: 1), // wait 1s before first retry
        ],
      ),
    );

    // ── Error transformation interceptor ──────────────────────────────────
    dio.interceptors.add(
      InterceptorsWrapper(
        onError: (DioException error, ErrorInterceptorHandler handler) {
          final appException = _transformDioError(error);
          AppLogger.error('API Error: ${appException.message}', error);
          handler.reject(
            DioException(
              requestOptions: error.requestOptions,
              error: appException,
              message: appException.message,
              type: error.type,
            ),
          );
        },
      ),
    );

    return dio;
  }

  /// Transform DioException into a typed AppException.
  static AppException _transformDioError(DioException error) {
    switch (error.type) {
      case DioExceptionType.connectionTimeout:
      case DioExceptionType.sendTimeout:
      case DioExceptionType.receiveTimeout:
        return const NetworkTimeoutException(
          'Connection to PenaltyIQ server timed out. '
          'Ensure the backend is running and your network connection is stable.',
        );

      case DioExceptionType.connectionError:
        return NetworkConnectionException(
          'Cannot reach PenaltyIQ server at ${ApiConstants.baseUrl}. '
          'Check that the backend is running.',
        );

      case DioExceptionType.badResponse:
        final statusCode = error.response?.statusCode ?? 0;
        final detail = _extractErrorDetail(error.response?.data);

        return switch (statusCode) {
          400 => ApiValidationException('Bad request: $detail'),
          401 => ApiServerException('Unauthorised: $detail'),
          403 => ApiServerException('Forbidden: $detail'),
          409 => ApiValidationException(detail),
          422 => ApiValidationException('Validation error: $detail'),
          429 => ApiServerException(
              'Too many requests. Please wait a moment and try again.'),
          500 => ApiServerException('Server error: $detail'),
          _   => ApiServerException('HTTP $statusCode: $detail'),
        };

      case DioExceptionType.cancel:
        return const RequestCancelledException('Request was cancelled.');

      default:
        return ApiServerException(
          'Unexpected network error: ${error.message ?? "unknown"}',
        );
    }
  }

  /// Extracts a human-readable error message from the backend response body.
  /// Handles both standard envelope `{error: ...}` and legacy `{detail: ...}`.
  static String _extractErrorDetail(dynamic data) {
    if (data == null) return 'No details provided.';
    if (data is Map) {
      if (data.containsKey('error') && data['error'] != null) {
        return data['error'].toString();
      }
      if (data.containsKey('detail') && data['detail'] != null) {
        return data['detail'].toString();
      }
    }
    return data.toString();
  }
}

/// Riverpod provider for the JWT auth token.
///
/// Start null (unauthenticated). Set via [authTokenProvider.notifier].
/// Used by [dioProvider] to inject the Authorization header on every request.
final authTokenProvider = StateProvider<String?>((ref) => null);

/// Riverpod provider for the Dio instance.
/// Rebuilds whenever the auth token changes.
final dioProvider = Provider<Dio>((ref) {
  final token = ref.watch(authTokenProvider);
  return ApiService.createDio(authToken: token);
});