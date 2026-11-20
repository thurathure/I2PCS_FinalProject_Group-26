import 'package:flutter_blue_plus/flutter_blue_plus.dart';

/// true  = fake umbrella, so the app runs end-to-end with no hardware.
/// false = real BLE connection to the ESP32-C3.
const bool kUseSimulator = true;

const String kDeviceName = 'U-Lock';
const String kBatteryType = 'CR123A';
const int kLowBatteryPercent = 20;

/// Used when location permission is denied. Change to your own city.
const double kFallbackLat = 25.0330;
const double kFallbackLon = 121.5654;
const String kFallbackName = 'Location off';

/// BLE contract. Must match firmware/u_lock_firmware/u_lock_firmware.ino exactly.
///   command (write)        : 0x01 = lock, 0x00 = unlock
///   state   (read, notify) : 0x01 = locked, 0x00 = unlocked
///   battery (read, notify) : one byte, 0-100 (%)
class BleUuids {
  static final service = Guid('c0de0001-7a1b-4c2d-9e3f-0a1b2c3d4e5f');
  static final command = Guid('c0de0002-7a1b-4c2d-9e3f-0a1b2c3d4e5f');
  static final state = Guid('c0de0003-7a1b-4c2d-9e3f-0a1b2c3d4e5f');
  static final battery = Guid('c0de0004-7a1b-4c2d-9e3f-0a1b2c3d4e5f');
}
