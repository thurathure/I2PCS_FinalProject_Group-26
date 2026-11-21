import flet as ft
from UI import *
from flet_ulock_ble import FletUlockBle 

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

    ble = FletUlockBle(
        on_data_channel_open=on_ble_channel_open
    )
    umbrella = FakeUmbrella()
    root = ft.Container(expand=True)

    def on_test_bluetooth(e):
        if not ble_ready:
            print("BLE DataChannel is not ready yet")
            return

        try:
            ble.check_bluetooth()
            print("Bluetooth state check requested")
        except Exception as error:
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

    act = {
        "toggle": on_toggle,
        "drain": on_drain,
        "close_banner": on_close_banner,
        "cycle": on_cycle,
        "go": on_go,
    }

    page.add(ft.SafeArea(content=root, expand=True))
    page.add(
        ft.Button(
            content=ft.Text("Check Bluetooth"),
            on_click=on_test_bluetooth,
        )
    )
    page.add(ble)
    render()

ft.run(main)
