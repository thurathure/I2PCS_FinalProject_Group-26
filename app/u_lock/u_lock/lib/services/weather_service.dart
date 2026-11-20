import 'dart:convert';
import 'dart:math';

import 'package:geocoding/geocoding.dart';
import 'package:geolocator/geolocator.dart';
import 'package:http/http.dart' as http;

import '../core/constants.dart';
import '../models/weather.dart';

class GeoPoint {
  const GeoPoint(this.lat, this.lon, this.name);
  final double lat, lon;
  final String name;
}

/// Open-Meteo: free, no API key.
class WeatherService {
  Future<GeoPoint> locate() async {
    const fallback = GeoPoint(kFallbackLat, kFallbackLon, kFallbackName);
    try {
      var perm = await Geolocator.checkPermission();
      if (perm == LocationPermission.denied) {
        perm = await Geolocator.requestPermission();
      }
      if (perm == LocationPermission.denied ||
          perm == LocationPermission.deniedForever ||
          !await Geolocator.isLocationServiceEnabled()) {
        return fallback;
      }
      final pos = await Geolocator.getCurrentPosition(
        locationSettings: const LocationSettings(
          accuracy: LocationAccuracy.low,
          timeLimit: Duration(seconds: 8),
        ),
      );
      var name = 'Current location';
      try {
        final marks = await placemarkFromCoordinates(pos.latitude, pos.longitude);
        final p = marks.first;
        name = (p.locality?.isNotEmpty ?? false)
            ? p.locality!
            : (p.administrativeArea ?? name);
      } catch (_) {}
      return GeoPoint(pos.latitude, pos.longitude, name);
    } catch (_) {
      return fallback;
    }
  }

  Future<WeatherSnapshot> fetch(double lat, double lon) async {
    final uri = Uri.https('api.open-meteo.com', '/v1/forecast', {
      'latitude': '$lat',
      'longitude': '$lon',
      'current': 'temperature_2m,relative_humidity_2m,wind_speed_10m,weather_code',
      'hourly': 'precipitation_probability',
      'forecast_days': '1',
      'timezone': 'auto',
      'wind_speed_unit': 'kmh',
    });
    final res = await http.get(uri).timeout(const Duration(seconds: 10));
    if (res.statusCode != 200) throw Exception('Weather HTTP ${res.statusCode}');

    final json = jsonDecode(res.body) as Map<String, dynamic>;
    final cur = json['current'] as Map<String, dynamic>;
    final hourly = json['hourly'] as Map<String, dynamic>;
    final times = (hourly['time'] as List).cast<String>();
    final probs = (hourly['precipitation_probability'] as List)
        .map((e) => (e as num?)?.toInt() ?? 0)
        .toList();

    final from = DateTime.now().subtract(const Duration(hours: 1));
    DateTime? rainAt;
    var maxChance = 0;
    for (var i = 0; i < times.length; i++) {
      final t = DateTime.parse(times[i]);
      if (t.isBefore(from)) continue;
      maxChance = max(maxChance, probs[i]);
      if (rainAt == null && probs[i] >= 50) rainAt = t;
    }

    return WeatherSnapshot(
      tempC: (cur['temperature_2m'] as num).toDouble(),
      humidity: (cur['relative_humidity_2m'] as num).round(),
      windKmh: (cur['wind_speed_10m'] as num).toDouble(),
      condition: conditionFromCode((cur['weather_code'] as num).toInt()),
      rainStartsAt: rainAt,
      maxRainChance: maxChance,
    );
  }
}
