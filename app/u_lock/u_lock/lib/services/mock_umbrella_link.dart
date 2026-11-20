import 'dart:async';

import 'umbrella_link.dart';

/// Fake umbrella: connects after ~2 s, confirms lock commands after 700 ms.
class MockUmbrellaLink implements UmbrellaLink {
  final _status = StreamController<BleStatus>.broadcast();
  final _lock = StreamController<LockState>.broadcast();
  final _battery = StreamController<int>.broadcast();
  bool _locked = true;

  @override
  Stream<BleStatus> get status => _status.stream;
  @override
  Stream<LockState> get lock => _lock.stream;
  @override
  Stream<int> get battery => _battery.stream;

  @override
  Future<void> start() async {
    _status.add(BleStatus.scanning);
    await Future<void>.delayed(const Duration(seconds: 1));
    _status.add(BleStatus.connecting);
    await Future<void>.delayed(const Duration(seconds: 1));
    _status.add(BleStatus.connected);
    _lock.add(_locked ? LockState.locked : LockState.unlocked);
    _battery.add(82);
  }

  @override
  Future<void> stop() async => _status.add(BleStatus.idle);

  @override
  Future<void> setLocked(bool locked) async {
    await Future<void>.delayed(const Duration(milliseconds: 700));
    _locked = locked;
    _lock.add(locked ? LockState.locked : LockState.unlocked);
  }

  @override
  Future<void> enableBluetooth() async {}
}
