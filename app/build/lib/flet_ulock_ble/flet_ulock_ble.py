
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

        if self.on_data_channel_open is None:
            self.on_data_channel_open = self._capture_channel

    def _capture_channel(self, e: ft.DataChannelOpenEvent):
        self._channel = self.get_data_channel(e.channel_id)
        self._channel.on_bytes(self._receive_message)

    def _receive_message(self, payload: bytes):
        try:
            message = json.loads(payload.decode("utf-8"))
            self._messages.put(message)
        except (UnicodeDecodeError, json.JSONDecodeError):
            self._messages.put({
                "type": "error",
                "message": "Invalid message received from BLE bridge"
            })

    def send(self, action: str, **data):
        if self._channel is None:
            raise RuntimeError("BLE bridge is not ready yet")

        message = {
            "action": action,
            **data
        }

        payload = json.dumps(message).encode("utf-8")
        self._channel.send(payload)

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
