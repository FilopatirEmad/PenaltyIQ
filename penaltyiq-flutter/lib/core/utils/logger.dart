import 'package:logger/logger.dart';

/// Centralized logging utility.
/// Wraps the `logger` package to provide consistent formatting
/// and integration points for remote crash reporting (e.g. Sentry/Crashlytics) in the future.
class AppLogger {
  AppLogger._();

  static final Logger _logger = Logger(
    printer: PrettyPrinter(
      methodCount: 0,
      errorMethodCount: 5,
      lineLength: 80,
      colors: true,
      printEmojis: true,
      dateTimeFormat: DateTimeFormat.dateAndTime,
    ),
  );

  /// Log a purely informational event (e.g. user action, navigation).
  static void info(String message) {
    _logger.i(message);
  }

  /// Log a warning (e.g. network retry, invalid state recovery).
  static void warning(String message, [dynamic error, StackTrace? stackTrace]) {
    _logger.w(message, error: error, stackTrace: stackTrace);
  }

  /// Log an error (e.g. crash, API failure, unhandled exception).
  /// In a production app, this is where you'd forward to Crashlytics/Sentry.
  static void error(String message, [dynamic error, StackTrace? stackTrace]) {
    _logger.e(message, error: error, stackTrace: stackTrace);
    // TODO: Send to remote crash reporting system (Crashlytics, Sentry, etc.)
  }

  /// Log debug data.
  static void debug(String message) {
    _logger.d(message);
  }
}
