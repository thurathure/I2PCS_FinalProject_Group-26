import 'dart:async';
import 'dart:io' show Platform;

import 'package:flutter_blue_plus/flutter_blue_plus.dart';
import 'package:permission_handler/permission_handler.dart';

import '../core/constants.dart';
import 'umbrella_link.dart';

/// Real BLE link to the ESP32-C3: scan -> connect -> discover -> subscribe,
/// then auto-reconnect whenever the connection drops.
class BleService implements UmbrellaLink {
  final _status = StreamController<BleStatus>.broadcast();
  final _lock = StreamController<LockState>.broadcast();
  final _battery = StreamController<int>.broadcast();

  @override
  Stream<BleStatus> get status => _status.stream;
  @override
  Stream<LockState> get lock => _lock.stream;
  @override
  Stream<int> get battery => _battery.stream;

  BluetoothDevice? _device;
  BluetoothCharacteristic? _cmdChar;
  BluetoothCharacteristic? _stateChar;
  BluetoothCharacteristic? _battChar;

  StreamSubscription<BluetoothAdapterState>? _adapterSub;
  StreamSubscription<BluetoothConnectionState>? _connSub;
  StreamSubscription<List<int>>? _stateSub;
  StreamSubscription<List<int>>? _battSub;

  bool _wanted = false;
  bool _looping = false;

  // ---------------------------------------------------------------- public

  @override
  Future<void> start() async {
    _wanted = true;
    _adapterSub ??= FlutterBluePlus.adapterState.listen((s) {
      if (s == BluetoothAdapterState.on) {
        unawaited(_connectLoop());
      } else {
        _status.add(BleStatus.bluetoothOff);
      }
    });
  }

  @override
  Future<void> stop() async {
    _wanted = false;
    await _adapterSub?.cancel();
    _adapterSub = null;
    await _device?.disconnect();
    _cleanup();
    _status.add(BleStatus.idle);
  }

  /// Sends 0x01 (lock) or 0x00 (unlock). The new state arrives later through
  /// the state notification, which is what the UI waits for.
  @override
  Future<void> setLocked(bool locked) async {
    final c = _cmdChar;
    if (c == null) throw StateError('Not connected');
    await c.write([locked ? 0x01 : 0x00]);
  }

  /// Android only; iOS cannot toggle Bluetooth from an app.
  @override
  Future<void> enableBluetooth() async {
    if (Platform.isAndroid) await FlutterBluePlus.turnOn();
  }

  // --------------------------------------------------------------- internal

  Future<void> _connectLoop() async {
    if (_looping) return;
    _looping = true;
    try {
      while (_wanted && _device == null) {
        if (!await _ensurePermissions()) {
          _status.add(BleStatus.permissionDenied);
          break;
        }
        if (FlutterBluePlus.adapterStateNow != BluetoothAdapterState.on) {
          _status.add(BleStatus.bluetoothOff);
          break;
        }
        final found = await _scan();
        if (found == null) {
          _status.add(BleStatus.idle);
          await Future<void>.delayed(const Duration(seconds: 3));
          continue;
        }
        final ok = await _connect(found);
        if (!ok) await Future<void>.delayed(const Duration(seconds: 3));
      }
    } finally {
      _looping = false;
    }
  }

  Future<bool> _ensurePermissions() async {
    if (!Platform.isAndroid) return true; // iOS prompts on first scan
    final r = await [
      Permission.bluetoothScan,
      Permission.bluetoothConnect,
      Permission.locationWhenInUse,
    ].request();
    final modern = (r[Permission.bluetoothScan]?.isGranted ?? false) &&
        (r[Permission.bluetoothConnect]?.isGranted ?? false);
    final legacy = r[Permission.locationWhenInUse]?.isGranted ?? false; // Android 11 and below
    return modern || legacy;
  }

  Future<BluetoothDevice?> _scan() async {
    _status.add(BleStatus.scanning);
    final found = Completer<BluetoothDevice?>();
    final sub = FlutterBluePlus.scanResults.listen((results) {
      if (results.isNotEmpty && !found.isCompleted) {
        found.complete(results.first.device);
      }
    });
    try {
      await FlutterBluePlus.startScan(
        withServices: [BleUuids.service],
        timeout: const Duration(seconds: 8),
      );
      return await found.future.timeout(
        const Duration(seconds: 10),
        onTimeout: () => null,
      );
    } catch (_) {
      return null;
    } finally {
      await sub.cancel();
      await FlutterBluePlus.stopScan();
    }
  }

  Future<bool> _connect(BluetoothDevice device) async {
    _status.add(BleStatus.connecting);
    try {
      await device.connect(timeout: const Duration(seconds: 10));
      _device = device;
      _connSub = device.connectionState.listen((s) {
        if (s == BluetoothConnectionState.disconnected) _onDisconnected();
      });
      await _setupCharacteristics(device);
      _status.add(BleStatus.connected);
      return true;
    } catch (_) {
      try {
        await device.disconnect();
      } catch (_) {}
      _cleanup();
      return false;
    }
  }

  Future<void> _setupCharacteristics(BluetoothDevice device) async {
    final services = await device.discoverServices();
    final svc = services.firstWhere((s) => s.uuid == BleUuids.service);
    for (final c in svc.characteristics) {
      if (c.uuid == BleUuids.command) _cmdChar = c;
      if (c.uuid == BleUuids.state) _stateChar = c;
      if (c.uuid == BleUuids.battery) _battChar = c;
    }
    if (_cmdChar == null || _stateChar == null || _battChar == null) {
      throw StateError('U-Lock characteristics missing');
    }

    await _stateChar!.setNotifyValue(true);
    _stateSub = _stateChar!.onValueReceived.listen(_handleState);
    _handleState(await _stateChar!.read());

    await _battChar!.setNotifyValue(true);
    _battSub = _battChar!.onValueReceived.listen(_handleBattery);
    _handleBattery(await _battChar!.read());
  }

  void _handleState(List<int> v) {
    if (v.isEmpty) return;
    _lock.add(v.first == 0x01 ? LockState.locked : LockState.unlocked);
  }

  void _handleBattery(List<int> v) {
    if (v.isEmpty) return;
    _battery.add(v.first.clamp(0, 100).toInt());
  }

  void _onDisconnected() {
    _cleanup();
    _status.add(BleStatus.idle);
    if (_wanted) {
      Future<void>.delayed(const Duration(seconds: 2), _connectLoop);
    }
  }

  void _cleanup() {
    _connSub?.cancel();
    _stateSub?.cancel();
    _battSub?.cancel();
    _connSub = _stateSub = _battSub = null;
    _device = null;
    _cmdChar = _stateChar = _battChar = null;
  }
}
