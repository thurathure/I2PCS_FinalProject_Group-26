import 'package:flutter/material.dart';

class Palette {
  static const ink = Color(0xFF11181F);
  static const paper = Color(0xFFF4F6F7);
  static const signal = Color(0xFFFF5B1F); // safety orange
  static const ok = Color(0xFF1E9E63);
  static const warn = Color(0xFFF2A900);
  static const danger = Color(0xFFB3261E);
  static const muted = Color(0xFF55616C);
  static const hairline = Color(0xFFD5DADE);
  static const disabled = Color(0xFF8A949E);
}

Color alpha(Color c, double a) => c.withAlpha((a * 255).round());

const kTextShadow = [
  Shadow(color: Color(0x66000000), blurRadius: 8, offset: Offset(0, 1)),
];

ThemeData buildTheme() => ThemeData(
      useMaterial3: true,
      colorScheme: ColorScheme.fromSeed(
        seedColor: Palette.signal,
        brightness: Brightness.light,
      ),
      scaffoldBackgroundColor: Palette.ink,
    );
