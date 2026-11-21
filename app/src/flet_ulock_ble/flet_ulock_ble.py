
import json
from queue import Queue, Empty
from typing import Optional

import flet as ft


@ft.control("FletUlockBle")
class FletUlockBle(ft.LayoutControl):
    """
    Python interface for the native Android BLE bridge.
    """

    on_data_channel_open: Optional[
        ft.EventHandler[ft.DataChannelOpenEvent]
    ] = None

    
    def init(self):
        self._channel = None
        self._messages = Queue()

        # Preserve the callback provided by main.py
        self._user_on_data_channel_open = self.on_data_channel_open

        # Always register our internal handler
        self.on_data_channel_open = self._handle_data_channel_open

    
    def _handle_data_channel_open(self, e: ft.DataChannelOpenEvent):
        print(f"[BLE DEBUG] Channel-open event on control: {id(self)}")
        print(f"[BLE DEBUG] Received channel ID: {e.channel_id}")

        self._capture_channel(e)

        print(f"[BLE DEBUG] Channel stored: {self._channel is not None}")

        if self._user_on_data_channel_open is not None:
            self._user_on_data_channel_open(e)


    def _capture_channel(self, e: ft.DataChannelOpenEvent):
        self._channel = self.get_data_channel(e.channel_id)
        print(f"[BLE DEBUG] Captured channel: {self._channel}")
        self._channel.on_bytes(self._receive_message)

    def _receive_message(self, payload: bytes):
        try:
            message = json.loads(payload.decode("utf-8"))
            self._messages.put(message)

            print(f"[BLE DEBUG] Received from Dart: {message}")

        except (UnicodeDecodeError, json.JSONDecodeError):
            self._messages.put({
                "type": "error",
                "message": "Invalid message received from BLE bridge"
            })
            print("[BLE DEBUG] Invalid message received from Dart")

    def send(self, action: str, **data):
        print(f"[BLE DEBUG] Sending from control: {id(self)}")
        print(f"[BLE DEBUG] Channel available: {self._channel is not None}")

        if self._channel is None:
            raise RuntimeError("BLE bridge is not ready yet")

        message = {"action": action, **data}
        payload = json.dumps(message).encode("utf-8")
        self._channel.send(payload)

    def check_bluetooth(self):
        """Check phone Bluetooth state and request activation if needed."""
        self.send("check_bluetooth")

    def scan(self, timeout: int = 10):
        self.send("scan", timeout=timeout)

    def connect(self, device_id: str):
        self.send("connect", device_id=device_id)

    def disconnect(self):
        self.send("disconnect")

    def write(self, command: str):
        self.send("write", command=command)

    def get_messages(self):
        """Retrieve all currently available messages from Dart."""
        messages = []

        while True:
            try:
                messages.append(self._messages.get_nowait())
            except Empty:
                break

        return messages

    def will_unmount(self):
        if self._channel is not None:
            self._channel.close()

        super().will_unmount()
