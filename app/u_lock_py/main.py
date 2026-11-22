import asyncio
import flet as ft
from UI import *
from flet_ulock_ble import FletUlockBle 
from weather_test import get_weather_summary, CITIES

def main(page: ft.Page):
    page.title = "U-Lock"
    page.padding = 0
    page.theme_mode = ft.ThemeMode.DARK
    page.window.width = 400
    page.window.height = 860

    
    ble_ready = False

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

    def render():
        s = dict(state)
        s["locked"] = umbrella.locked
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
        page.update()

    async def poll_ble_messages():
        while True:
            messages = ble.get_messages()

            for message in messages:
                msg_type = message.get("type")

                if msg_type == "bluetooth_ready":
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
        umbrella.toggle()
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

    CITY = "Tainan City"

    def load_weather():
        try:
            lat, lon = CITIES[CITY]
            state.update(get_weather_summary(lat, lon))
            state["location"] = CITY
        except Exception as ex:
            print("Weather error:", ex)

    act = {
        "toggle": on_toggle,
        "drain": on_drain,
        "close_banner": on_close_banner,
        "cycle": on_cycle,
        "go": on_go,
        "check_bluetooth": on_check_bluetooth,
    }

    page.add(ft.SafeArea(content=root, expand=True))
    page.add(ble)

    load_weather()

    page.run_task(poll_ble_messages)

    render()

if __name__ == "__main__":
    ft.run(main)
