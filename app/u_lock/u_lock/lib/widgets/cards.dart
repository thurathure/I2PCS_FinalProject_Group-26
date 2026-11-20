import 'package:flutter/material.dart';

import '../core/constants.dart';
import '../core/theme.dart';
import 'paper_card.dart';

/// Red warning shown when conditions are hazardous.
class AdvisoryCard extends StatelessWidget {
  const AdvisoryCard({super.key});

  @override
  Widget build(BuildContext context) {
    return const PaperCard(
      color: Palette.danger,
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Icon(Icons.warning_amber_rounded, color: Colors.white, size: 30),
          SizedBox(width: 12),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text('Severe weather warning',
                    style: TextStyle(color: Colors.white, fontSize: 17, fontWeight: FontWeight.w800)),
                SizedBox(height: 4),
                Text(
                  'Severe storm warning: Consider staying indoors today for your safety.',
                  style: TextStyle(color: Colors.white, fontSize: 15, height: 1.35),
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }
}

/// Push-notification mockup.
class NotificationBanner extends StatelessWidget {
  const NotificationBanner({super.key});

  @override
  Widget build(BuildContext context) {
    return PaperCard(
      radius: 22,
      padding: const EdgeInsets.all(14),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Container(
            width: 40,
            height: 40,
            decoration: BoxDecoration(color: Palette.ink, borderRadius: BorderRadius.circular(10)),
            child: const Icon(Icons.umbrella_rounded, color: Palette.signal, size: 24),
          ),
          const SizedBox(width: 12),
          const Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Row(
                  children: [
                    Text('U-Lock', style: TextStyle(fontWeight: FontWeight.w800, fontSize: 15, color: Palette.ink)),
                    Spacer(),
                    Text('now (preview)', style: TextStyle(fontSize: 12, color: Palette.muted)),
                  ],
                ),
                SizedBox(height: 2),
                Text(
                  'Rain predicted today — Don’t forget to bring your umbrella!',
                  style: TextStyle(fontSize: 15, height: 1.3, color: Palette.ink),
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }
}

class ConditionsCard extends StatelessWidget {
  const ConditionsCard({super.key, required this.wind, required this.humidity, required this.rain});
  final String wind, humidity, rain;

  @override
  Widget build(BuildContext context) {
    const divider = SizedBox(
      height: 44,
      child: VerticalDivider(width: 1, thickness: 1, color: Palette.hairline),
    );
    return PaperCard(
      padding: const EdgeInsets.symmetric(vertical: 16, horizontal: 8),
      child: Row(
        children: [
          _Metric(icon: Icons.air_rounded, value: wind, label: 'Wind'),
          divider,
          _Metric(icon: Icons.water_drop_outlined, value: humidity, label: 'Humidity'),
          divider,
          _Metric(icon: Icons.grain_rounded, value: rain, label: 'Rain'),
        ],
      ),
    );
  }
}

class _Metric extends StatelessWidget {
  const _Metric({required this.icon, required this.value, required this.label});
  final IconData icon;
  final String value, label;

  @override
  Widget build(BuildContext context) {
    return Expanded(
      child: Column(
        children: [
          Icon(icon, color: Palette.ink, size: 22),
          const SizedBox(height: 6),
          Text(value,
              textAlign: TextAlign.center,
              style: const TextStyle(fontSize: 16, fontWeight: FontWeight.w800, color: Palette.ink)),
          Text(label, style: const TextStyle(fontSize: 13, color: Palette.muted)),
        ],
      ),
    );
  }
}

class BatteryCard extends StatelessWidget {
  const BatteryCard({super.key, required this.percent});
  final int? percent;

  @override
  Widget build(BuildContext context) {
    final p = percent;
    final low = p != null && p <= kLowBatteryPercent;
    final color = p == null
        ? Palette.disabled
        : low
            ? Palette.danger
            : p <= 40
                ? Palette.warn
                : Palette.ok;

    return PaperCard(
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              const Text('Battery',
                  style: TextStyle(fontSize: 17, fontWeight: FontWeight.w800, color: Palette.ink)),
              const Spacer(),
              Text(p == null ? '--' : '$p%',
                  style: const TextStyle(fontSize: 28, fontWeight: FontWeight.w800, color: Palette.ink)),
            ],
          ),
          const SizedBox(height: 10),
          ClipRRect(
            borderRadius: BorderRadius.circular(6),
            child: LinearProgressIndicator(
              value: (p ?? 0) / 100,
              minHeight: 10,
              backgroundColor: Palette.hairline,
              valueColor: AlwaysStoppedAnimation(color),
            ),
          ),
          const SizedBox(height: 12),
          if (low)
            Row(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: const [
                Icon(Icons.battery_alert_rounded, color: Palette.danger, size: 20),
                SizedBox(width: 8),
                Expanded(
                  child: Text(
                    'Replace the $kBatteryType battery soon. It isn’t rechargeable.',
                    style: TextStyle(fontSize: 14, height: 1.35, color: Palette.danger, fontWeight: FontWeight.w600),
                  ),
                ),
              ],
            )
          else
            Text(
              p == null
                  ? 'Connect to your umbrella to read the battery.'
                  : 'Battery is healthy. Replace the $kBatteryType below $kLowBatteryPercent%.',
              style: const TextStyle(fontSize: 14, height: 1.35, color: Palette.muted),
            ),
        ],
      ),
    );
  }
}
