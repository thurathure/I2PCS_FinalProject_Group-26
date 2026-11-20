import 'package:flutter/material.dart' hide LockState;
import 'package:flutter/services.dart';

import '../core/theme.dart';
import '../services/umbrella_link.dart';

/// Status text plus the large circular lock/unlock button.
class LockControl extends StatefulWidget {
  const LockControl({
    super.key,
    required this.lock,
    required this.connected,
    required this.pending,
    required this.message,
    required this.onPressed,
  });

  final LockState lock;
  final bool connected;
  final bool pending;
  final String? message;
  final VoidCallback onPressed;

  @override
  State<LockControl> createState() => _LockControlState();
}

class _LockControlState extends State<LockControl> {
  bool _down = false;

  @override
  Widget build(BuildContext context) {
    final locked = widget.lock == LockState.locked;
    final enabled = widget.connected && !widget.pending;

    final title = !widget.connected
        ? 'Umbrella offline'
        : switch (widget.lock) {
            LockState.locked => 'Locked',
            LockState.unlocked => 'Unlocked',
            LockState.unknown => 'Checking…',
          };
    final subtitle = !widget.connected
        ? 'Move closer and keep Bluetooth on.'
        : locked
            ? 'The umbrella can’t open.'
            : 'The umbrella can open.';

    final fill = !widget.connected
        ? Palette.disabled
        : locked
            ? Palette.ink
            : Palette.signal;
    final fg = locked || !widget.connected ? Colors.white : Palette.ink;
    final action = locked ? 'Unlock' : 'Lock';

    return Column(
      children: [
        AnimatedSwitcher(
          duration: const Duration(milliseconds: 250),
          child: Text(
            title,
            key: ValueKey(title),
            style: const TextStyle(
              fontSize: 44,
              fontWeight: FontWeight.w800,
              letterSpacing: -1,
              color: Colors.white,
              shadows: kTextShadow,
            ),
          ),
        ),
        const SizedBox(height: 4),
        Text(
          widget.message ?? subtitle,
          textAlign: TextAlign.center,
          style: TextStyle(
            fontSize: 15,
            fontWeight: FontWeight.w500,
            color: Colors.white,
            shadows: kTextShadow,
          ),
        ),
        const SizedBox(height: 22),
        Semantics(
          button: true,
          enabled: enabled,
          label: '$action umbrella',
          child: GestureDetector(
            onTapDown: enabled ? (_) => setState(() => _down = true) : null,
            onTapCancel: () => setState(() => _down = false),
            onTapUp: (_) => setState(() => _down = false),
            onTap: enabled
                ? () {
                    HapticFeedback.mediumImpact();
                    widget.onPressed();
                  }
                : null,
            child: AnimatedScale(
              scale: _down ? 0.94 : 1,
              duration: const Duration(milliseconds: 120),
              child: SizedBox(
                width: 212,
                height: 212,
                child: Stack(
                  alignment: Alignment.center,
                  children: [
                    Container(
                      width: 212,
                      height: 212,
                      decoration: const BoxDecoration(
                        shape: BoxShape.circle,
                        color: Palette.paper,
                        boxShadow: [
                          BoxShadow(color: Color(0x55000000), blurRadius: 28, offset: Offset(0, 12)),
                        ],
                      ),
                    ),
                    AnimatedContainer(
                      duration: const Duration(milliseconds: 450),
                      curve: Curves.easeOutCubic,
                      width: 180,
                      height: 180,
                      decoration: BoxDecoration(shape: BoxShape.circle, color: fill),
                    ),
                    if (widget.pending)
                      SizedBox(
                        width: 180,
                        height: 180,
                        child: CircularProgressIndicator(strokeWidth: 5, color: fg),
                      ),
                    Column(
                      mainAxisSize: MainAxisSize.min,
                      children: [
                        AnimatedSwitcher(
                          duration: const Duration(milliseconds: 300),
                          transitionBuilder: (child, anim) => ScaleTransition(
                            scale: anim,
                            child: FadeTransition(opacity: anim, child: child),
                          ),
                          child: Icon(
                            locked ? Icons.lock_rounded : Icons.lock_open_rounded,
                            key: ValueKey(locked),
                            size: 64,
                            color: fg,
                          ),
                        ),
                        const SizedBox(height: 6),
                        Text(
                          widget.pending ? 'Working…' : action,
                          style: TextStyle(fontSize: 20, fontWeight: FontWeight.w800, color: fg),
                        ),
                      ],
                    ),
                  ],
                ),
              ),
            ),
          ),
        ),
      ],
    );
  }
}
