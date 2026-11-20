enum WeatherCondition { sunny, cloudy, darkCloud, rain, thunderstorm }

extension WeatherConditionX on WeatherCondition {
  String get label => switch (this) {
        WeatherCondition.sunny => 'Sunny',
        WeatherCondition.cloudy => 'Cloudy',
        WeatherCondition.darkCloud => 'Overcast',
        WeatherCondition.rain => 'Rain',
        WeatherCondition.thunderstorm => 'Thunderstorm',
      };

  String get summary => switch (this) {
        WeatherCondition.sunny => 'Clear skies and sunshine.',
        WeatherCondition.cloudy => 'Cloud cover, but dry for now.',
        WeatherCondition.darkCloud => 'Heavy cloud. Rain could arrive soon.',
        WeatherCondition.rain => 'Steady rain. Take your umbrella.',
        WeatherCondition.thunderstorm => 'Thunder and lightning nearby.',
      };
}

/// Maps Open-Meteo WMO weather codes to the five app themes.
WeatherCondition conditionFromCode(int code) {
  if (code == 0 || code == 1) return WeatherCondition.sunny;
  if (code == 2 || code == 45 || code == 48) return WeatherCondition.cloudy;
  if (code == 3) return WeatherCondition.darkCloud;
  if (code >= 95) return WeatherCondition.thunderstorm;
  if ((code >= 51 && code <= 67) || (code >= 80 && code <= 82)) {
    return WeatherCondition.rain;
  }
  return WeatherCondition.darkCloud; // snow and anything unmapped
}

class WeatherSnapshot {
  const WeatherSnapshot({
    required this.tempC,
    required this.humidity,
    required this.windKmh,
    required this.condition,
    required this.rainStartsAt,
    required this.maxRainChance,
  });

  final double tempC;
  final int humidity;
  final double windKmh;
  final WeatherCondition condition;
  final DateTime? rainStartsAt;
  final int maxRainChance;
}
