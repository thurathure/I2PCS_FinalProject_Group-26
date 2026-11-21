
import 'dart:async';
import 'dart:convert';
import 'dart:typed_data';
import 'package:flet/flet.dart';
import 'package:flutter/widgets.dart';
import 'package:flutter_blue_plus/flutter_blue_plus.dart';

const String serviceUuid =
    "12345678-1234-5678-1234-56789abcdef0";

const String writeUuid =
    "12345678-1234-5678-1234-56789abcdef1";

const String notifyUuid =
    "12345678-1234-5678-1234-56789abcdef2";


class FletUlockBleControl extends StatefulWidget {
  final Control control;

  const FletUlockBleControl({
    super.key,
    required this.control,
  });

  @override
  State<FletUlockBleControl> createState() =>
      _FletUlockBleControlState();
}


class _FletUlockBleControlState
    extends State<FletUlockBleControl> {

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

      switch (message["action"]) {
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


  Future<void> _scan(int timeout) async {
    if (!await FlutterBluePlus.isSupported) {
      throw Exception("Bluetooth LE is not supported");
    }

    await _scanSubscription?.cancel();

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

    _writeCharacteristic = writeChar;

    if (notifyChar != null) {
      _notifySubscription =
          notifyChar.onValueReceived.listen((value) {
        _sendToPython({
          "type": "notification",
          "data": utf8.decode(value, allowMalformed: true),
        });
      });

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
