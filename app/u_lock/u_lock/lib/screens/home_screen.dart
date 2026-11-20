import 'package:flutter/material.dart';
import 'package:provider/provider.dart';

import '../core/format.dart';
import '../core/theme.dart';
import '../models/weather.dart';
import '../services/umbrella_link.dart';
import '../state/app_state.dart';
import '../widgets/cards.dart';
import '../widgets/lock_control.dart';
import '../widgets/paper_card.dart';
import '../widgets/weather_background.dart';

class HomeScreen extends StatelessWidget {
  const HomeScreen({super.key});

  @override
  Widget build(BuildContext context) {
    final s = context.watch<AppState>();
    const gap = SizedBox(height: 14);

    return Scaffold(
      body: Stack(
        children: [
          Positioned.fill(child: WeatherBackground(condition: s.condition)),
          SafeArea(
            child: Align(
              alignment: Alignment.topCenter,
              child: ConstrainedBox(
                constraints: const BoxConstraints(maxWidth: 520),
                child: RefreshIndicator(
                  color: Palette.ink,
                  onRefresh: s.refreshWeather,
                  child: ListView(
                    physics: const AlwaysScrollableScrollPhysics(),
                    padding: const EdgeInsets.fromLTRB(20, 12, 20, 32),
                    children: [
                      _TopBar(state: s),
                      const SizedBox(height: 28),
                      _WeatherHeader(
                        tempC: s.weather?.tempC,
                        condition: s.condition,
                        demo: s.isDemo,
                        onLongPress: s.cycleDemoWeather,
                      ),
                      const SizedBox(height: 32),
                      LockControl(
                        lock: s.lock,
                        connected: s.connected,
                        pending: s.pending,
                        message: s.message,
                        onPressed: s.toggleLock,
                      ),
                      const SizedBox(height: 32),
                      if (s.showRainReminder) ...[const NotificationBanner(), gap],
                      if (s.severeWarning) ...[const AdvisoryCard(), gap],
                      ConditionsCard(wind: s.windLabel, humidity: s.humidityLabel, rain: s.rainLabel),
                      gap,
                      BatteryCard(percent: s.battery),
                    ],
                  ),
                ),
              ),
            ),
          ),
        ],
      ),
    );
  }
}

class _TopBar extends StatelessWidget {
  const _TopBar({required this.state});
  final AppState state;

  @override
  Widget build(BuildContext context) {
    final (label, dot) = switch (state.status) {
      BleStatus.connected => ('Connected', Palette.ok),
      BleStatus.scanning => ('Searching', Palette.warn),
      BleStatus.connecting => ('Connecting', Palette.warn),
      BleStatus.bluetoothOff => ('Bluetooth off', Palette.danger),
      BleStatus.permissionDenied => ('Allow Bluetooth', Palette.danger),
      BleStatus.idle => ('Disconnected', Palette.danger),
    };
    final pct = state.battery;
    final batteryIcon = pct == null
        ? Icons.battery_unknown_rounded
        : pct >= 70
            ? Icons.battery_full_rounded
            : pct >= 40
                ? Icons.battery_4_bar_rounded
                : pct >= 20
                    ? Icons.battery_2_bar_rounded
                    : Icons.battery_alert_rounded;

    return Row(
      children: [
        Flexible(
          child: Pill(
            child: Row(
              mainAxisSize: MainAxisSize.min,
              children: [
                const Icon(Icons.place_outlined, size: 18, color: Palette.ink),
                const SizedBox(width: 4),
                Flexible(
                  child: Text(
                    state.locationName,
                    overflow: TextOverflow.ellipsis,
                    style: const TextStyle(fontWeight: FontWeight.w700, color: Palette.ink),
                  ),
                ),
              ],
            ),
          ),
        ),
        const SizedBox(width: 8),
        Pill(
          onTap: state.onStatusTap,
          child: Row(
            mainAxisSize: MainAxisSize.min,
            children: [
              Container(width: 9, height: 9, decoration: BoxDecoration(color: dot, shape: BoxShape.circle)),
              const SizedBox(width: 6),
              Text(label, style: const TextStyle(fontWeight: FontWeight.w700, color: Palette.ink)),
            ],
          ),
        ),
        const SizedBox(width: 8),
        Pill(
          child: Row(
            mainAxisSize: MainAxisSize.min,
            children: [
              Icon(batteryIcon, size: 20, color: pct != null && pct < 20 ? Palette.danger : Palette.ink),
              if (pct != null) ...[
                const SizedBox(width: 2),
                Text('$pct%', style: const TextStyle(fontWeight: FontWeight.w700, color: Palette.ink)),
              ],
            ],
          ),
        ),
      ],
    );
  }
}

class _WeatherHeader extends StatelessWidget {
  const _WeatherHeader({
    required this.tempC,
    required this.condition,
    required this.demo,
    required this.onLongPress,
  });

  final double? tempC;
  final WeatherCondition condition;
  final bool demo;
  final VoidCallback onLongPress;

  @override
  Widget build(BuildContext context) {
    const white = Colors.white;
    return GestureDetector(
      behavior: HitTestBehavior.opaque,
      onLongPress: onLongPress,
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(formatDate(DateTime.now()),
              style: const TextStyle(fontSize: 16, fontWeight: FontWeight.w700, color: white, shadows: kTextShadow)),
          Text(tempC == null ? '--°' : '${tempC!.round()}°',
              style: const TextStyle(
                  fontSize: 96, fontWeight: FontWeight.w300, height: 1.05, color: white, shadows: kTextShadow)),
          Text(condition.label,
              style: const TextStyle(fontSize: 24, fontWeight: FontWeight.w800, color: white, shadows: kTextShadow)),
          const SizedBox(height: 2),
          Text(condition.summary,
              style: const TextStyle(fontSize: 16, color: white, shadows: kTextShadow)),
          if (demo)
            const Padding(
              padding: EdgeInsets.only(top: 6),
              child: Text('Demo weather. Long-press to change.',
                  style: TextStyle(fontSize: 13, color: white, fontWeight: FontWeight.w600, shadows: kTextShadow)),
            ),
        ],
      ),
    );
  }
}
