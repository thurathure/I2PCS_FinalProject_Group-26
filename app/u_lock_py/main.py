import asyncio
import flet as ft
from UI import *
from flet_ulock_ble import FletUlockBle
from lock_controller import LockController

def main(page: ft.Page):
    page.title = "U-Lock"
    page.padding = 0
    page.theme_mode = ft.ThemeMode.DARK
    page.window.width = 400
    page.window.height = 860

    
    ble_ready = False
    lock_controller = LockController()
    state["connected"] = False
    state["devices"] = []
    state["scan_status"] = "idle"
    state["selected_device_id"] = None
    state["selected_device_name"] = None
    state["connection_message"] = "No umbrella connected."
    state["lock_status"] = "LOCKED"

    def on_ble_channel_open(e):
        nonlocal ble_ready
        ble_ready = True
        print("BLE DataChannel is ready")

        state["bluetooth_status"] = "checking"
        state["bluetooth_message"] = "Checking your phone..."
        render()

        try:
            ble.check_bluetooth()
            print("Initial Bluetooth check requested")
        except Exception as error:
            state["bluetooth_status"] = "error"
            state["bluetooth_message"] = str(error)
            render()
            print(f"Bluetooth check error: {error}")

    ble = FletUlockBle(
        on_data_channel_open=on_ble_channel_open
    )
    umbrella = FakeUmbrella()
    root = ft.Container(expand=True)
    scanner_open = False

    def on_check_bluetooth(e):
        if not ble_ready:
            print("BLE DataChannel is not ready yet")
            return

        state["bluetooth_status"] = "checking"
        state["bluetooth_message"] = "Checking your phone..."
        render()

        try:
            ble.check_bluetooth()
            print("Bluetooth state check requested")
        except Exception as error:
            state["bluetooth_status"] = "error"
            state["bluetooth_message"] = str(error)
            render()
            print(f"Bluetooth check error: {error}")

    
    def on_scan(e):
        if not ble_ready:
            print("[U-LOCK] BLE DataChannel is not ready.")
            return

        if state["bluetooth_status"] != "on":
            state["connection_message"] = (
                "Turn on Bluetooth before scanning."
            )
            render()
            return

        try:
            # Let Python prepare and validate the scan.
            lock_controller.start_scan()

            # Synchronize the interface with controller state.
            state["devices"] = lock_controller.get_devices()
            state["scan_status"] = "scanning"
            state["connection_message"] = (
                "Searching for nearby U-LOCK devices..."
            )

            render()

            # Request the actual Android BLE scan.
            ble.scan(timeout=10)

            print("[U-LOCK] Python controller started BLE scan.")

        except Exception as error:
            lock_controller.set_error(str(error))

            state["scan_status"] = "error"
            state["connection_message"] = str(error)

            render()

            print(f"[U-LOCK] Scan error: {error}")


    
    def on_connect(device_id):
        if not ble_ready:
            print("[U-LOCK] BLE DataChannel is not ready.")
            return

        try:
            # Validate the selected device through Python.
            lock_controller.start_connection(device_id)

            state["selected_device_id"] = device_id
            state["selected_device_name"] = lock_controller.device_name
            state["scan_status"] = "connecting"
            state["connection_message"] = (
                f"Connecting to {lock_controller.device_name}..."
            )

            render()

            # Send the validated connection request to Android BLE.
            ble.connect(device_id)

            print(
                f"[U-LOCK] Connecting to "
                f"{lock_controller.device_name} ({device_id})"
            )

        except (ValueError, RuntimeError) as error:
            lock_controller.set_error(str(error))

            state["scan_status"] = "error"
            state["connection_message"] = str(error)

            render()

            print(f"[U-LOCK] Connection request rejected: {error}")

        except Exception as error:
            lock_controller.connection_failed(str(error))

            state["scan_status"] = "error"
            state["connection_message"] = str(error)

            render()

            print(f"[U-LOCK] BLE connection error: {error}")


    def on_disconnect(e):
        if not ble_ready:
            return

        try:
            ble.disconnect()
            print("BLE disconnect requested")
        except Exception as error:
            print(f"BLE disconnect error: {error}")
        
    def close_scanner(e=None):
        nonlocal scanner_open

        if scanner_open:
            scanner_open = False
            page.pop_dialog()

    def build_scanner_content():
        devices = state.get("devices", [])
        scan_status = state.get("scan_status", "idle")

        device_rows = []

        if not devices:
            if scan_status == "scanning":
                empty_message = "Searching for nearby devices..."
            elif scan_status == "complete":
                empty_message = "No Bluetooth devices found."
            else:
                empty_message = "Press Start Scan to find devices."

            device_rows.append(
                ft.Container(
                    content=ft.Text(
                        empty_message,
                        color=MUTED,
                        size=13,
                    ),
                    padding=20,
                    alignment=ft.Alignment.CENTER,
                )
            )

        for device in devices:
            device_id = device.get("device_id")
            device_name = device.get("name", "Unknown device")
            rssi = device.get("rssi", -100)

            is_ulock = device.get(
                "is_ulock",
                "U-LOCK" in device_name.upper(),
            )

            if rssi >= -60:
                signal_label = "Strong"
            elif rssi >= -80:
                signal_label = "Moderate"
            else:
                signal_label = "Weak"

            device_info = [
                ft.Text(
                    device_name,
                    size=14,
                    weight=BOLD,
                    color=TEXT,
                ),
                ft.Text(
                    f"{device_id}",
                    size=10,
                    color=MUTED,
                ),
                ft.Text(
                    f"{signal_label} signal ({rssi} dBm)",
                    size=11,
                    color=MUTED,
                ),
                ft.Text(
                    "U-LOCK device" if is_ulock else "Other Bluetooth device",
                    size=11,
                    color=GREEN if is_ulock else MUTED,
                ),
            ]

            device_actions = []

            if is_ulock:
                device_actions.append(
                    ft.Button(
                        "Connect",
                        disabled=scan_status == "connecting",
                        on_click=(
                            lambda e, selected_id=device_id:
                            on_connect(selected_id)
                        ),
                    )
                )

            device_rows.append(
                ft.Container(
                    content=ft.Row(
                        [
                            ft.Column(
                                device_info,
                                spacing=3,
                                expand=True,
                            ),
                            *device_actions,
                        ],
                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                        vertical_alignment=ft.CrossAxisAlignment.CENTER,
                    ),
                    padding=12,
                    border=ft.Border.all(
                        1,
                        tint("#FFFFFF", 0.12),
                    ),
                    border_radius=12,
                )
            )

        return ft.Container(
            width=340,
            content=ft.Column(
                [
                    ft.Text(
                        f"Discovered devices: {len(devices)}",
                        size=12,
                        color=MUTED,
                    ),
                    ft.Button(
                        "Scanning..." if scan_status == "scanning"
                        else "Start Scan",
                        icon=ft.Icons.BLUETOOTH_SEARCHING,
                        on_click=on_scan,
                        disabled=(
                            scan_status in ("scanning", "connecting")
                            or state.get("bluetooth_status") != "on"
                        ),
                    ),
                    ft.Column(
                        device_rows,
                        spacing=8,
                        scroll=ft.ScrollMode.AUTO,
                        height=340,
                    ),
                ],
                spacing=12,
            ),
        )

    scanner_dialog = ft.AlertDialog(
        modal=True,
        title=ft.Text("Bluetooth Devices"),
        content=ft.Container(width=340),
        actions=[
            ft.Button(
                "Close",
                on_click=close_scanner,
            ),
        ],
    )

    def on_open_scanner(e):
        nonlocal scanner_open

        if state.get("bluetooth_status") != "on":
            state["connection_message"] = (
                "Turn on Bluetooth before scanning."
            )
            render()
            return

        scanner_open = True
        scanner_dialog.content = build_scanner_content()

        page.show_dialog(scanner_dialog)
        page.update()


    def render():
        s = dict(state)
        s["locked"] = lock_controller.locked
        s["battery"] = umbrella.battery

        body = ft.Column(
            SCREENS[s["tab"]](s, act),
            scroll=ft.ScrollMode.AUTO,
            expand=True,
            spacing=0,
            horizontal_alignment=ft.CrossAxisAlignment.STRETCH,
        )
        root.gradient = ft.LinearGradient(begin=TOP, end=BOTTOM, colors=SKY[s["condition"]])
        root.content = ft.Column(
            [
                ft.Container(
                    content=body,
                    expand=True,
                    padding=ft.Padding(left=PAD, top=16, right=PAD, bottom=8),
                ),
                bottom_nav(s, act),
            ],
            spacing=0,
        )

        # Refresh the scanner popup whenever BLE state changes.
        if scanner_open:
            scanner_dialog.content = build_scanner_content()

        page.update()

    async def poll_ble_messages():
        while True:
            messages = ble.get_messages()

            for message in messages:
                msg_type = message.get("type")
                if msg_type == "scan_started":
                    state["scan_status"] = "scanning"
                    state["connection_message"] = "Searching for nearby devices..."
                    render()

                
                elif msg_type == "device_found":
                    device_id = message.get("device_id")
                    device_name = message.get("name") or ""
                    rssi = message.get("rssi", -100)
                    print(
                        f"[BLE SCAN] Found: "
                        f"{device_name or 'Unnamed device'} | "
                        f"ID: {device_id} | RSSI: {rssi} dBm"
                    )
                    try:
                        # Let Python validate and register the device.
                        device_added = lock_controller.add_device(
                            device_id=device_id,
                            name=device_name,
                            rssi=rssi,
                        )

                        if device_added:
                            # Synchronize the UI with controller data.
                            state["devices"] = lock_controller.get_devices()

                            print(
                                f"[U-LOCK] Device discovered: "
                                f"{device_name} | RSSI: {rssi}"
                            )

                            render()

                    except (ValueError, TypeError) as error:
                        print(
                            f"[U-LOCK] Invalid BLE device information: {error}"
                        )


                elif msg_type == "scan_complete":
                    state["scan_status"] = "complete"
                    lock_controller.finish_scan()
                    state["devices"] = lock_controller.get_devices()
                    state["connection_message"] = (
                        "Scan complete. Select your U-LOCK device."
                        if state["devices"]
                        else "No devices found. Try scanning again."
                    )
                    render()

                
                elif msg_type == "connected":
                    close_scanner()
                    device_id = message.get("device_id")
                    device_name = message.get("device_name") or "U-LOCK"

                    # Python records the confirmed connection.
                    lock_controller.connection_succeeded(
                        device_id=device_id,
                        device_name=device_name,
                    )

                    state["connected"] = lock_controller.connected
                    state["selected_device_id"] = lock_controller.device_id
                    state["selected_device_name"] = lock_controller.device_name
                    state["scan_status"] = "connected"
                    state["connection_message"] = "Umbrella connected."

                    print(
                        f"[U-LOCK] Connected successfully: {device_name}"
                    )

                    render()


                
                elif msg_type == "notification":
                    notification = message.get("data", "")

                    # Python validates and processes the ESP32 response.
                    notification_received = (
                        lock_controller.process_notification(notification)
                    )

                    if notification_received:
                        # Update the simulation's displayed state too,
                        # while the UI is being migrated to the controller.
                        umbrella.locked = lock_controller.locked

                        state["lock_status"] = (
                            "LOCKED"
                            if lock_controller.locked
                            else "UNLOCKED"
                        )

                        print(
                            f"[U-LOCK] Physical lock state: "
                            f"{state['lock_status']}"
                        )

                        render()
                    else:
                        print(
                            f"[U-LOCK] Ignored notification: {notification}"
                        )


                
                elif msg_type == "disconnected":
                    # Reset the Python connection state.
                    lock_controller.disconnect()

                    state["connected"] = False
                    state["selected_device_id"] = None
                    state["selected_device_name"] = None
                    state["scan_status"] = "idle"
                    state["connection_message"] = "Umbrella disconnected."

                    print("[U-LOCK] Device disconnected.")

                    render()


                elif msg_type == "write_success":
                    print(f"BLE command sent: {message.get('command')}")

                elif msg_type == "bluetooth_ready":
                    state["bluetooth_status"] = "on"
                    state["bluetooth_message"] = (
                        "Your phone's Bluetooth is ready."
                    )
                    render()

                elif msg_type == "bluetooth_off":
                    state["bluetooth_status"] = "off"
                    state["bluetooth_message"] = (
                        "Turn on Bluetooth to use your umbrella."
                    )
                    render()

                elif msg_type == "bluetooth_unsupported":
                    state["bluetooth_status"] = "unsupported"
                    state["bluetooth_message"] = message.get(
                        "message",
                        "Bluetooth is not supported."
                    )
                    render()

                elif msg_type == "error":
                    if state["bluetooth_status"] == "checking":
                        state["bluetooth_status"] = "error"
                        state["bluetooth_message"] = message.get(
                            "message",
                            "An unknown Bluetooth error occurred."
                        )
                        render()

                    print(f"BLE error: {message.get('message')}")

            await asyncio.sleep(0.2)

    # ---- actions: what each tap does (logic) ----
    
    def on_toggle(e):
        try:
            # Ask Python which command should be sent.
            command = lock_controller.prepare_toggle_command()

            # Mark the command as pending before transmission.
            lock_controller.mark_command_pending(command)

            # Send the real command through the Android BLE bridge.
            ble.write(command)

            print(f"[U-LOCK] Sent command: {command}")

            # Wait for the ESP32 notification.
            # Do not change the lock state optimistically.
            render()

        except (RuntimeError, ValueError) as error:
            print(f"[U-LOCK] Cannot toggle lock: {error}")

            state["connection_message"] = str(error)
            render()

        except Exception as error:
            lock_controller.command_write_failed(str(error))

            print(f"[U-LOCK] Command transmission failed: {error}")

            state["connection_message"] = str(error)
            render()


    def on_drain(e):
        umbrella.drain()
        render()

    def on_close_banner(e):
        state["banner_visible"] = False
        render()

    def on_cycle(e):
        i = CONDITIONS.index(state["condition"])
        state["condition"] = CONDITIONS[(i + 1) % len(CONDITIONS)]
        state["banner_visible"] = True
        render()

    def on_go(tab):
        state["tab"] = tab
        render()

    act = {
        "toggle": on_toggle,
        "drain": on_drain,
        "close_banner": on_close_banner,
        "cycle": on_cycle,
        "go": on_go,
        "check_bluetooth": on_check_bluetooth,
        "scan": on_scan,
        "connect": on_connect,
        "disconnect": on_disconnect,
        "open_scanner": on_open_scanner,
    }

    page.add(ft.SafeArea(content=root, expand=True))
    page.add(ble)

    page.run_task(poll_ble_messages)

    render()

ft.run(main)
