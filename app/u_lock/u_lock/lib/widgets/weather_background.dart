import 'dart:math';

import 'package:flutter/material.dart';

import '../core/theme.dart';
import '../models/weather.dart';

/// Full-screen animated sky. Cross-fades when the condition changes.
class WeatherBackground extends StatelessWidget {
  const WeatherBackground({super.key, required this.condition});
  final WeatherCondition condition;

  @override
  Widget build(BuildContext context) {
    return AnimatedSwitcher(
      duration: const Duration(milliseconds: 900),
      child: _Scene(key: ValueKey(condition), condition: condition),
    );
  }
}

class _Look {
  const _Look(this.sky, this.cloud, this.cloudAlpha, this.clouds, this.cloudScale);
  final List<Color> sky;
  final Color cloud;
  final double cloudAlpha;
  final int clouds;
  final double cloudScale;
}

const _looks = <WeatherCondition, _Look>{
  WeatherCondition.sunny:
      _Look([Color(0xFF1B6FE0), Color(0xFF6DB8F7)], Color(0xFFFFFFFF), 0.85, 2, 1.0),
  WeatherCondition.cloudy:
      _Look([Color(0xFF56697D), Color(0xFF93A5B8)], Color(0xFFE3EAF0), 0.60, 5, 1.3),
  WeatherCondition.darkCloud:
      _Look([Color(0xFF23282E), Color(0xFF3C444C)], Color(0xFF59626B), 0.90, 6, 1.8),
  WeatherCondition.rain:
      _Look([Color(0xFF1F3347), Color(0xFF4F6A82)], Color(0xFF6D7F90), 0.85, 5, 1.5),
  WeatherCondition.thunderstorm:
      _Look([Color(0xFF10131A), Color(0xFF2A2F3D)], Color(0xFF3A4150), 0.95, 6, 1.8),
};

class _CloudSpec {
  const _CloudSpec(this.base, this.y, this.scale, this.speed);
  final double base, y, scale;
  final int speed; // whole loops per cycle, so the drift wraps seamlessly
}

const _cloudSpecs = [
  _CloudSpec(0.05, 0.10, 1.3, 1),
  _CloudSpec(0.45, 0.22, 1.0, 2),
  _CloudSpec(0.75, 0.06, 1.6, 1),
  _CloudSpec(0.25, 0.30, 1.2, 2),
  _CloudSpec(0.60, 0.16, 0.9, 1),
  _CloudSpec(0.90, 0.26, 1.4, 1),
];

class _Drop {
  const _Drop(this.x, this.y, this.s);
  final double x, y, s;
}

class _Scene extends StatefulWidget {
  const _Scene({super.key, required this.condition});
  final WeatherCondition condition;

  @override
  State<_Scene> createState() => _SceneState();
}

class _SceneState extends State<_Scene> with SingleTickerProviderStateMixin {
  static const _cycleSeconds = 20;
  late final AnimationController _c = AnimationController(
    vsync: this,
    duration: const Duration(seconds: _cycleSeconds),
  );
  late final List<_Drop> _drops = () {
    final r = Random(7);
    return List.generate(90, (_) => _Drop(r.nextDouble(), r.nextDouble(), 0.6 + r.nextDouble() * 0.8));
  }();

  @override
  void didChangeDependencies() {
    super.didChangeDependencies();
    // Respect the system "reduce motion" setting.
    if (MediaQuery.of(context).disableAnimations) {
      _c.stop();
    } else if (!_c.isAnimating) {
      _c.repeat();
    }
  }

  @override
  void dispose() {
    _c.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return SizedBox.expand(
      child: AnimatedBuilder(
        animation: _c,
        builder: (_, __) => CustomPaint(
          painter: _ScenePainter(widget.condition, _c.value, _drops),
        ),
      ),
    );
  }
}

class _ScenePainter extends CustomPainter {
  _ScenePainter(this.condition, this.t, this.drops);
  final WeatherCondition condition;
  final double t; // 0..1 over a 20 s cycle
  final List<_Drop> drops;

  _Look get look => _looks[condition]!;
  bool get _wet => condition == WeatherCondition.rain || condition == WeatherCondition.thunderstorm;

  @override
  void paint(Canvas canvas, Size size) {
    final rect = Offset.zero & size;
    canvas.drawRect(
      rect,
      Paint()
        ..shader = LinearGradient(
          begin: Alignment.topCenter,
          end: Alignment.bottomCenter,
          colors: look.sky,
        ).createShader(rect),
    );
    if (condition == WeatherCondition.sunny) _sun(canvas, size);
    _clouds(canvas, size);
    if (_wet) _rain(canvas, size);
    if (condition == WeatherCondition.thunderstorm) _lightning(canvas, size);
  }

  void _sun(Canvas canvas, Size size) {
    final c = Offset(size.width * 0.78, size.height * 0.12 + 30);
    canvas.drawCircle(
      c,
      170,
      Paint()
        ..shader = RadialGradient(colors: [
          alpha(const Color(0xFFFFF3B0), 0.9),
          alpha(const Color(0xFFFFE066), 0.0),
        ]).createShader(Rect.fromCircle(center: c, radius: 170)),
    );
    final ray = Paint()
      ..color = alpha(const Color(0xFFFFF0A0), 0.55)
      ..strokeWidth = 3
      ..strokeCap = StrokeCap.round;
    for (var i = 0; i < 12; i++) {
      final a = t * 2 * pi + i * pi / 6;
      final d = Offset(cos(a), sin(a));
      canvas.drawLine(c + d * 62, c + d * 86, ray);
    }
    canvas.drawCircle(c, 46, Paint()..color = const Color(0xFFFFD84D));
  }

  void _clouds(Canvas canvas, Size size) {
    final paint = Paint()..color = alpha(look.cloud, look.cloudAlpha);
    for (var i = 0; i < look.clouds; i++) {
      final s = _cloudSpecs[i];
      final f = (s.base + t * s.speed) % 1.0;
      final x = (-0.25 + 1.5 * f) * size.width;
      final y = s.y * size.height + 40;
      _cloud(canvas, Offset(x, y), s.scale * look.cloudScale, paint);
    }
  }

  void _cloud(Canvas c, Offset o, double s, Paint paint) {
    final path = Path()
      ..addOval(Rect.fromCenter(center: o, width: 120 * s, height: 60 * s))
      ..addOval(Rect.fromCenter(center: o.translate(-34 * s, 8 * s), width: 80 * s, height: 50 * s))
      ..addOval(Rect.fromCenter(center: o.translate(36 * s, 10 * s), width: 90 * s, height: 50 * s))
      ..addOval(Rect.fromCenter(center: o.translate(0, -18 * s), width: 70 * s, height: 56 * s));
    c.drawPath(path, paint);
  }

  void _rain(Canvas canvas, Size size) {
    final paint = Paint()
      ..color = alpha(const Color(0xFFBFD7EA), 0.5)
      ..strokeWidth = 1.4
      ..strokeCap = StrokeCap.round;
    for (final d in drops) {
      final k = (d.s * 10).round(); // whole loops per cycle
      final fy = (d.y + t * k) % 1.0;
      final x = d.x * size.width + fy * 30;
      final y = fy * size.height;
      canvas.drawLine(Offset(x, y), Offset(x - 5, y + 18 * d.s), paint);
    }
  }

  void _lightning(Canvas canvas, Size size) {
    final sec = t * 20;
    const strikes = [3.0, 3.35, 11.0, 16.0, 16.3];
    const xs = [0.72, 0.72, 0.28, 0.6, 0.6];
    var flash = 0.0;
    var xFrac = 0.5;
    for (var i = 0; i < strikes.length; i++) {
      final d = sec - strikes[i];
      if (d >= 0 && d < 0.18) {
        final f = 1 - d / 0.18;
        if (f > flash) {
          flash = f;
          xFrac = xs[i];
        }
      }
    }
    if (flash <= 0) return;
    canvas.drawRect(Offset.zero & size, Paint()..color = alpha(Colors.white, flash * 0.30));
    final x = size.width * xFrac;
    final h = size.height;
    final bolt = Path()
      ..moveTo(x, 0)
      ..lineTo(x - 18, h * 0.12)
      ..lineTo(x + 6, h * 0.14)
      ..lineTo(x - 26, h * 0.30)
      ..lineTo(x - 4, h * 0.32)
      ..lineTo(x - 40, h * 0.50);
    canvas.drawPath(
      bolt,
      Paint()
        ..color = alpha(const Color(0xFFCFE3FF), flash)
        ..style = PaintingStyle.stroke
        ..strokeWidth = 8
        ..maskFilter = const MaskFilter.blur(BlurStyle.normal, 8),
    );
    canvas.drawPath(
      bolt,
      Paint()
        ..color = alpha(Colors.white, flash)
        ..style = PaintingStyle.stroke
        ..strokeWidth = 3
        ..strokeJoin = StrokeJoin.round,
    );
  }

  @override
  bool shouldRepaint(covariant _ScenePainter old) => true;
}
