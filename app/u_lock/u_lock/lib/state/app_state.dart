import 'dart:async';

import 'package:flutter/foundation.dart';

import '../core/constants.dart';
import '../core/format.dart';
import '../models/weather.dart';
import '../services/ble_service.dart';
import '../services/mock_umbrella_link.dart';
import '../services/umbrella_link.dart';
import '../services/weather_service.dart';

class AppState extends ChangeNotifier {
  AppState({UmbrellaLink? link, WeatherService? weatherService})
      : link = link ?? (kUseSimulator ? MockUmbrellaLink() : BleService()),
        _weatherService = weatherService ?? WeatherService();

  final UmbrellaLink link;
  final WeatherService _weatherService;

  BleStatus status = BleStatus.idle;
  LockState lock = LockState.unknown;
  int? battery;
  bool pending = false;
  String? message;
  WeatherSnapshot? weather;
  String locationName = 'Locating…';
  WeatherCondition? _demo;

  final _subs = <StreamSubscription<dynamic>>[];
  Timer? _weatherTimer;
  Timer? _ackTimer;
  Timer? _messageTimer;

  // ------------------------------------------------------------ derived UI

  WeatherCondition get condition => _demo ?? weather?.condition ?? WeatherCondition.cloudy;
  bool get isDemo => _demo != null;
  bool get connected => status == BleStatus.connected;

  bool get severeWarning =>
      condition == WeatherCondition.thunderstorm || (!isDemo && (weather?.windKmh ?? 0) >= 50);

  bool get showRainReminder =>
      condition == WeatherCondition.rain ||
      condition == WeatherCondition.thunderstorm ||
      (!isDemo && (weather?.maxRainChance ?? 0) >= 50);

  String get windLabel => isDemo ? '—' : '${(weather?.windKmh ?? 0).round()} km/h';
  String get humidityLabel => isDemo ? '—' : '${weather?.humidity ?? '--'}%';
  String get rainLabel {
    if (condition == WeatherCondition.rain || condition == WeatherCondition.thunderstorm) {
      return 'Raining now';
    }
    final t = weather?.rainStartsAt;
    if (!isDemo && t != null) return 'Around ${formatHour(t)}';
    return 'None today';
  }

  // -------------------------------------------------------------- lifecycle

  Future<void> init() async {
    _subs.addAll([
      link.status.listen((s) {
        status = s;
        if (s != BleStatus.connected) {
          lock = LockState.unknown;
          pending = false;
        }
        notifyListeners();
      }),
      link.lock.listen((s) {
        lock = s;
        pending = false;
        _ackTimer?.cancel();
        notifyListeners();
      }),
      link.battery.listen((b) {
        battery = b;
        notifyListeners();
      }),
    ]);
    unawaited(link.start());
    await refreshWeather();
    _weatherTimer = Timer.periodic(const Duration(minutes: 15), (_) => refreshWeather());
  }

  @override
  void dispose() {
    for (final s in _subs) {
      s.cancel();
    }
    _weatherTimer?.cancel();
    _ackTimer?.cancel();
    _messageTimer?.cancel();
    link.stop();
    super.dispose();
  }

  // ---------------------------------------------------------------- actions

  Future<void> toggleLock() async {
    if (!connected || pending) return;
    final wantLocked = lock != LockState.locked; // unknown -> lock
    pending = true;
    message = null;
    notifyListeners();

    _ackTimer?.cancel();
    _ackTimer = Timer(const Duration(seconds: 5), () {
      if (pending) {
        pending = false;
        _flash('The umbrella didn’t confirm. Try again.');
      }
    });

    try {
      await link.setLocked(wantLocked);
    } catch (_) {
      _ackTimer?.cancel();
      pending = false;
      _flash('Couldn’t send the command. Check the connection.');
    }
  }

  Future<void> onStatusTap() async {
    if (status == BleStatus.bluetoothOff) {
      await link.enableBluetooth();
    } else if (status == BleStatus.permissionDenied) {
      await link.start();
    }
  }

  Future<void> refreshWeather() async {
    try {
      final loc = await _weatherService.locate();
      locationName = loc.name;
      weather = await _weatherService.fetch(loc.lat, loc.lon);
    } catch (_) {
      _flash('Weather unavailable. Pull down to retry.');
    }
    notifyListeners();
  }

  /// Long-press the weather header to preview each background (handy for demos).
  void cycleDemoWeather() {
    const order = WeatherCondition.values;
    _demo = _demo == null
        ? order.first
        : (order.indexOf(_demo!) == order.length - 1 ? null : order[order.indexOf(_demo!) + 1]);
    notifyListeners();
  }

  void _flash(String text) {
    message = text;
    notifyListeners();
    _messageTimer?.cancel();
    _messageTimer = Timer(const Duration(seconds: 5), () {
      message = null;
      notifyListeners();
    });
  }
}
