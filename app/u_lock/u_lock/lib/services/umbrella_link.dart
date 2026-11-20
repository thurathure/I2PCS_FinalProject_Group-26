enum BleStatus { bluetoothOff, permissionDenied, idle, scanning, connecting, connected }

enum LockState { unknown, locked, unlocked }

/// What the UI needs from the umbrella. Implemented by the real BLE service
/// and by a simulator, so the app can be built before the hardware works.
abstract class UmbrellaLink {
  Stream<BleStatus> get status;
  Stream<LockState> get lock;
  Stream<int> get battery;

  Future<void> start();
  Future<void> stop();
  Future<void> setLocked(bool locked);
  Future<void> enableBluetooth();
}
