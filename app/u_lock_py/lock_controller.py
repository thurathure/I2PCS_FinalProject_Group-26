
from typing import Optional


class LockController:
    """
    Main Python controller for the U-LOCK smart umbrella.

    Responsibilities:
    - Manage Bluetooth device discovery.
    - Track the selected umbrella.
    - Manage connection and disconnection states.
    - Validate lock and unlock commands.
    - Process ESP32 notifications.
    - Track the actual lock state.
    """

    VALID_COMMANDS = {"LOCK", "UNLOCK"}

    def __init__(self):
        # Bluetooth connection information
        self.connected = False
        self.device_id: Optional[str] = None
        self.device_name: Optional[str] = None

        # Bluetooth scanning information
        self.devices = {}
        self.scanning = False
        self.connecting = False
        self.scan_complete = False

        # Physical lock information
        self.locked: Optional[bool] = None
        self.pending_command: Optional[str] = None

        # Error and status information
        self.last_error: Optional[str] = None
        self.last_notification: Optional[str] = None

    # --------------------------------------------------
    # DEVICE DISCOVERY
    # --------------------------------------------------

    def start_scan(self):
        """Prepare the controller for a new Bluetooth scan."""

        if self.connected:
            raise RuntimeError(
                "Disconnect the current umbrella before scanning."
            )

        if self.connecting:
            raise RuntimeError(
                "A Bluetooth connection is already in progress."
            )

        self.devices.clear()
        self.scanning = True
        self.scan_complete = False
        self.last_error = None

    
    def add_device(self, device_id, name, rssi):
        """
        Register every discovered Bluetooth LE device.

        Devices are identified by their Bluetooth ID.
        Repeated advertisements update existing device information.
        """

        if not device_id:
            return False

        device_name = name.strip() if isinstance(name, str) else ""
        if not device_name:
            device_name = "Unknown device"

        device = {
            "device_id": device_id,
            "name": device_name,
            "rssi": int(rssi),
            "is_ulock": "U-LOCK" in device_name.upper(),
        }

        self.devices[device_id] = device
        return True


    def finish_scan(self):
        """Mark the current scan as completed."""

        self.scanning = False
        self.scan_complete = True

    def get_devices(self):
        """Return discovered devices, strongest signal first."""

        return sorted(
            self.devices.values(),
            key=lambda device: device["rssi"],
            reverse=True,
        )

    # --------------------------------------------------
    # CONNECTION MANAGEMENT
    # --------------------------------------------------

    
    def start_connection(self, device_id):
        """Validate and prepare a U-LOCK connection request."""

        if self.connected:
            raise RuntimeError(
                "An umbrella is already connected."
            )

        if self.connecting:
            raise RuntimeError(
                "A connection attempt is already in progress."
            )

        if device_id not in self.devices:
            raise ValueError(
                "The selected device was not found in the scan results."
            )

        device = self.devices[device_id]

        if not device.get("is_ulock", False):
            raise ValueError(
                "This device is not identified as a U-LOCK device."
            )

        self.device_id = device_id
        self.device_name = device["name"]

        self.connecting = True
        self.last_error = None


    def connection_succeeded(self, device_id, device_name=None):
        """Update the controller after ESP32 confirms connection."""

        self.connected = True
        self.connecting = False

        if device_id:
            self.device_id = device_id

        if device_name:
            self.device_name = device_name

        self.last_error = None
        self.pending_command = None

    def connection_failed(self, message):
        """Handle a failed connection attempt."""

        self.connecting = False
        self.connected = False

        self.device_id = None
        self.device_name = None

        self.last_error = message

    def disconnect(self):
        """Reset connection-related information."""

        self.connected = False
        self.connecting = False

        self.device_id = None
        self.device_name = None

        self.pending_command = None
        self.locked = None

    # --------------------------------------------------
    # LOCK AND UNLOCK MANAGEMENT
    # --------------------------------------------------

    def prepare_toggle_command(self):
        """
        Determine the next lock command.

        The controller only allows toggling when the actual
        physical lock state is known.
        """

        if not self.connected:
            raise RuntimeError(
                "Cannot control the umbrella while disconnected."
            )

        if self.locked is None:
            raise RuntimeError(
                "The current lock state is unknown."
            )

        if self.pending_command is not None:
            raise RuntimeError(
                "Please wait for the previous command to finish."
            )

        if self.locked:
            return "UNLOCK"

        return "LOCK"

    def validate_command(self, command):
        """Check whether a requested command is supported."""

        normalized = str(command).strip().upper()

        if normalized not in self.VALID_COMMANDS:
            raise ValueError(
                f"Unsupported lock command: {command}"
            )

        if not self.connected:
            raise RuntimeError(
                "The umbrella is not connected."
            )

        return normalized

    def mark_command_pending(self, command):
        """Record a command before sending it to the ESP32."""

        normalized = self.validate_command(command)

        if self.pending_command is not None:
            raise RuntimeError(
                "Another command is still pending."
            )

        self.pending_command = normalized
        return normalized

    def command_write_failed(self, message):
        """Clear a pending command after a write failure."""

        self.pending_command = None
        self.last_error = message

    # --------------------------------------------------
    # ESP32 NOTIFICATION PROCESSING
    # --------------------------------------------------

    def process_notification(self, data):
        """
        Process notifications received from ESP32.

        Expected messages:
        LOCKED
        UNLOCKED
        """

        if not self.connected:
            return False

        if not isinstance(data, str):
            return False

        notification = data.strip().upper()

        if notification == "LOCKED":
            self.locked = True

        elif notification == "UNLOCKED":
            self.locked = False

        else:
            return False

        self.last_notification = notification
        self.pending_command = None
        self.last_error = None

        return True

    # --------------------------------------------------
    # ERROR MANAGEMENT
    # --------------------------------------------------

    def set_error(self, message):
        """Store an error reported by the BLE bridge."""

        self.last_error = str(message)

        if self.connecting:
            self.connection_failed(self.last_error)

        elif self.scanning:
            self.scanning = False

    def clear_error(self):
        """Clear the previously recorded error."""

        self.last_error = None

    # --------------------------------------------------
    # APPLICATION STATUS
    # --------------------------------------------------

    def get_status(self):
        """Return a snapshot of the controller's current state."""

        return {
            "connected": self.connected,
            "device_id": self.device_id,
            "device_name": self.device_name,
            "devices": self.get_devices(),
            "scanning": self.scanning,
            "connecting": self.connecting,
            "scan_complete": self.scan_complete,
            "locked": self.locked,
            "pending_command": self.pending_command,
            "last_error": self.last_error,
            "last_notification": self.last_notification,
        }
