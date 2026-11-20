import 'package:flet/flet.dart';
import 'package:flutter/widgets.dart';

import 'flet_ulock_ble.dart';

class Extension extends FletExtension {
  @override
  Widget? createWidget(Key? key, Control control) {
    switch (control.type) {
      case "FletUlockBle":
        return FletUlockBleControl(control: control);
      default:
        return null;
    }
  }
}
