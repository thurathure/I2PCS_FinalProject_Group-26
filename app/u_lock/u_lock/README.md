# U-Lock (UmbrellaOS)

Flutter companion app + ESP32-C3 firmware for the smart-lock umbrella.

## Run it (no hardware needed)
1. Install Flutter, then in this folder: `flutter create . --project-name u_lock`
   (this generates the android/ and ios/ folders; it keeps lib/ and pubspec.yaml)
2. `flutter pub get`
3. Plug in a real phone and run `flutter run`.
   `kUseSimulator = true` in `lib/core/constants.dart` fakes the umbrella.
4. Long-press the weather header to cycle the five weather backgrounds.

## Switch to the real umbrella
1. Flash `firmware/u_lock_firmware/u_lock_firmware.ino` to the ESP32-C3.
2. Check with the nRF Connect phone app: device "U-Lock" with 3 characteristics.
3. Set `kUseSimulator = false`, rebuild.

## Android setup
`android/app/src/main/AndroidManifest.xml`, inside `<manifest>`:
```xml
<uses-permission android:name="android.permission.BLUETOOTH_SCAN" android:usesPermissionFlags="neverForLocation" />
<uses-permission android:name="android.permission.BLUETOOTH_CONNECT" />
<uses-permission android:name="android.permission.BLUETOOTH" android:maxSdkVersion="30" />
<uses-permission android:name="android.permission.BLUETOOTH_ADMIN" android:maxSdkVersion="30" />
<uses-permission android:name="android.permission.ACCESS_FINE_LOCATION" />
<uses-permission android:name="android.permission.INTERNET" />
```
In `android/app/build.gradle`, set `minSdkVersion 21` (or higher).

## iOS setup
`ios/Runner/Info.plist`:
```xml
<key>NSBluetoothAlwaysUsageDescription</key>
<string>U-Lock uses Bluetooth to lock and unlock your umbrella.</string>
<key>NSLocationWhenInUseUsageDescription</key>
<string>U-Lock uses your location to show local weather.</string>
```
iOS needs a Mac with Xcode to build.

## Structure
```
lib/
  main.dart                    app entry, provider
  core/                        constants (UUIDs), theme, formatting
  models/weather.dart          conditions + WMO code mapping
  services/
    umbrella_link.dart         interface the UI depends on
    ble_service.dart           real BLE: scan, connect, notify, auto-reconnect
    mock_umbrella_link.dart    simulator
    weather_service.dart       Open-Meteo + GPS
  state/app_state.dart         lock toggle, pending/ack, weather, demo mode
  widgets/                     background painter, lock button, cards
  screens/home_screen.dart
firmware/u_lock_firmware/      ESP32-C3 sketch matching the BLE contract
```
