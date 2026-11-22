import 'package:permission_handler/permission_handler.dart';
import 'dart:async';
import 'dart:convert';
import 'dart:typed_data';
import 'package:flet/flet.dart';
import 'package:flutter/material.dart';
import 'package:flutter_blue_plus/flutter_blue_plus.dart';

const String serviceUuid = "12345678-1234-5678-1234-56789abcdef0";

const String writeUuid = "12345678-1234-5678-1234-56789abcdef1";

const String notifyUuid = "12345678-1234-5678-1234-56789abcdef2";

class FletUlockBleControl extends StatefulWidget {
  final Control control;

  const FletUlockBleControl({
    super.key,
    required this.control,
  });

  @override
  State<FletUlockBleControl> createState() => _FletUlockBleControlState();
}

class _FletUlockBleControlState extends State<FletUlockBleControl> {
  DataChannel? _channel;
  StreamSubscription<Uint8List>? _channelSubscription;

  StreamSubscription<List<ScanResult>>? _scanSubscription;
  StreamSubscription<List<int>>? _notifySubscription;

  BluetoothDevice? _device;
  BluetoothCharacteristic? _writeCharacteristic;

  @override
  void didChangeDependencies() {
    super.didChangeDependencies();

    if (_channel != null) return;

    _channel = FletBackend.of(context).openDataChannel();

    _channelSubscription = _channel!.messages.listen(
      _handlePythonMessage,
    );

    widget.control.triggerEvent("data_channel_open", {
      "channel_name": "ble",
      "channel_id": _channel!.id,
    });
  }

  void _sendToPython(Map<String, dynamic> message) {
    if (_channel == null) return;

    _channel!.send(
      Uint8List.fromList(
        utf8.encode(jsonEncode(message)),
      ),
    );
  }

  Future<void> _handlePythonMessage(Uint8List bytes) async {
    try {
      final message = jsonDecode(utf8.decode(bytes));
      debugPrint("[U-LOCK BLE] Received action: ${message["action"]}");
      switch (message["action"]) {
        case "check_bluetooth":
          await _checkBluetooth();
          break;
        case "scan":
          await _scan(message["timeout"] ?? 10);
          break;

        case "connect":
          await _connect(message["device_id"]);
          break;

        case "disconnect":
          await _disconnect();
          break;

        case "write":
          await _write(message["command"]);
          break;
      }
    } catch (e) {
      _sendToPython({
        "type": "error",
        "message": e.toString(),
      });
    }
  }

  Future<void> _checkBluetooth() async {
    debugPrint("[U-LOCK BLE] Checking Bluetooth state...");

    try {
      final supported = await FlutterBluePlus.isSupported;

      if (!supported) {
        _sendToPython({
          "type": "bluetooth_unsupported",
          "message": "This phone does not support Bluetooth.",
        });
        return;
      }

      var state = FlutterBluePlus.adapterStateNow;

      // Wait briefly if the initial state is unknown.
      if (state == BluetoothAdapterState.unknown) {
        state = await FlutterBluePlus.adapterState
            .where((value) => value != BluetoothAdapterState.unknown)
            .first
            .timeout(const Duration(seconds: 5));
      }

      debugPrint("[U-LOCK BLE] Current Bluetooth state: $state");

      if (state == BluetoothAdapterState.on) {
        _sendToPython({
          "type": "bluetooth_ready",
        });
        return;
      }

      if (!mounted) return;

      final shouldTurnOn = await showDialog<bool>(
        context: context,
        barrierDismissible: false,
        builder: (dialogContext) {
          return AlertDialog(
            title: const Text("Bluetooth is turned off"),
            content: const Text(
              "Bluetooth is required to use U-Lock. "
              "Would you like to turn it on?",
            ),
            actions: [
              TextButton(
                onPressed: () {
                  Navigator.pop(dialogContext, false);
                },
                child: const Text("Cancel"),
              ),
              ElevatedButton(
                onPressed: () {
                  Navigator.pop(dialogContext, true);
                },
                child: const Text("Turn on Bluetooth"),
              ),
            ],
          );
        },
      );

      if (shouldTurnOn != true) {
        _sendToPython({
          "type": "bluetooth_off",
        });
        return;
      }

      debugPrint("[U-LOCK BLE] Requesting Bluetooth activation...");

      await FlutterBluePlus.turnOn();

      await FlutterBluePlus.adapterState
          .where((value) => value == BluetoothAdapterState.on)
          .first
          .timeout(const Duration(seconds: 60));

      debugPrint("[U-LOCK BLE] Bluetooth is now ON!");

      _sendToPython({
        "type": "bluetooth_ready",
      });
    } catch (e) {
      debugPrint("[U-LOCK BLE] Bluetooth check error: $e");

      _sendToPython({
        "type": "error",
        "message": e.toString(),
      });
    }
  }

  Future<void> _requestBluetoothPermissions() async {
    debugPrint("[U-LOCK BLE] Requesting Bluetooth permissions...");

    final scanStatus = await Permission.bluetoothScan.request();
    debugPrint("[U-LOCK BLE] Scan permission: $scanStatus");

    final connectStatus = await Permission.bluetoothConnect.request();
    debugPrint("[U-LOCK BLE] Connect permission: $connectStatus");

    if (!scanStatus.isGranted || !connectStatus.isGranted) {
      throw Exception(
        "Bluetooth permissions denied. "
        "Please allow Nearby devices permission in Android Settings.",
      );
    }

    debugPrint("[U-LOCK BLE] Both permissions granted!");
  }

  Future<void> _scan(int timeout) async {
    await _requestBluetoothPermissions();

    if (!await FlutterBluePlus.isSupported) {
      throw Exception("Bluetooth LE is not supported");
    }

    _sendToPython({
      "type": "scan_started",
    });

    _scanSubscription = FlutterBluePlus.onScanResults.listen(
      (results) {
        for (final result in results) {
          final device = result.device;

          final name = result.advertisementData.advName.isNotEmpty
              ? result.advertisementData.advName
              : device.platformName;

          _sendToPython({
            "type": "device_found",
            "name": name,
            "device_id": device.remoteId.str,
            "rssi": result.rssi,
          });
        }
      },
    );

    await FlutterBluePlus.startScan(
      timeout: Duration(seconds: timeout),
    );

    await FlutterBluePlus.isScanning
        .where((scanning) => scanning == false)
        .first;

    _sendToPython({
      "type": "scan_complete",
    });

    await _scanSubscription?.cancel();
    _scanSubscription = null;
  }

  Future<void> _connect(String deviceId) async {
    await _requestBluetoothPermissions();

    _device = BluetoothDevice.fromId(deviceId);

    await _device!.connect(
      license: License.nonprofit,
      timeout: const Duration(seconds: 15),
    );

    final services = await _device!.discoverServices();

    BluetoothCharacteristic? writeChar;
    BluetoothCharacteristic? notifyChar;

    for (final service in services) {
      if (service.uuid != Guid(serviceUuid)) continue;

      for (final characteristic in service.characteristics) {
        if (characteristic.uuid == Guid(writeUuid)) {
          writeChar = characteristic;
        }

        if (characteristic.uuid == Guid(notifyUuid)) {
          notifyChar = characteristic;
        }
      }
    }

    if (writeChar == null) {
      throw Exception("BLE write characteristic not found");
    }

    // Store the write characteristic.
    _writeCharacteristic = writeChar;

    // Tell Python that the BLE connection is ready.
    // Do this before enabling notifications.
    _sendToPython({
      "type": "connected",
      "device_id": deviceId,
      "device_name": _device!.platformName,
    });

    // Listen for incoming ESP32 notifications.
    if (notifyChar != null) {
      _notifySubscription = notifyChar.onValueReceived.listen((value) {
        final notification = utf8.decode(
          value,
          allowMalformed: true,
        );

        _sendToPython({
          "type": "notification",
          "data": notification,
        });
      });

      // Enable notifications after Python is informed.
      await notifyChar.setNotifyValue(true);
    }

    _sendToPython({
      "type": "connected",
      "device_id": deviceId,
      "device_name": _device!.platformName,
    });
  }

  Future<void> _write(String command) async {
    if (_writeCharacteristic == null) {
      throw Exception("Not connected to a BLE device");
    }

    await _writeCharacteristic!.write(
      utf8.encode(command),
    );

    _sendToPython({
      "type": "write_success",
      "command": command,
    });
  }

  Future<void> _disconnect() async {
    await _notifySubscription?.cancel();
    _notifySubscription = null;

    if (_device != null) {
      await _device!.disconnect();
    }

    _device = null;
    _writeCharacteristic = null;

    _sendToPython({
      "type": "disconnected",
    });
  }

  @override
  void dispose() {
    _channelSubscription?.cancel();
    _scanSubscription?.cancel();
    _notifySubscription?.cancel();

    _channel?.close();

    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return LayoutControl(
      control: widget.control,
      child: const SizedBox.shrink(),
    );
  }
}
