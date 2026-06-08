/// API endpoint constants.
/// Base URL is configurable via dart-define for different environments.
library;

class ApiConstants {
  ApiConstants._();

  // Override via: flutter run --dart-define=API_BASE_URL=http://127.0.0.1:8000
  static const String baseUrl = String.fromEnvironment(
    'API_BASE_URL',
    defaultValue: 'http://127.0.0.1:8000',
  );

  // ── Analysis pipeline ──────────────────────────────────────────────────────
  static const String calibrateEndpoint    = '/api/v1/calibrate';
  static const String processVideoEndpoint = '/api/v1/process-video';
  static const String analyzeEndpoint      = '/api/v1/analyze';
  static const String renderVideoEndpoint  = '/api/v1/render-video';

  // ── Auth ───────────────────────────────────────────────────────────────────
  static const String registerEndpoint = '/auth/register';
  static const String loginEndpoint    = '/auth/login';
  static const String meEndpoint       = '/auth/me';

  // ── System ─────────────────────────────────────────────────────────────────
  static const String healthEndpoint = '/health';
}