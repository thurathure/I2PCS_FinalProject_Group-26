import flet as ft
from UI import *

def main(page: ft.Page):
    page.title = "U-Lock"
    page.padding = 0
    page.theme_mode = ft.ThemeMode.DARK
    page.window.width = 400     # phone-sized preview on desktop
    page.window.height = 860

    umbrella = FakeUmbrella()
    root = ft.Container(expand=True)

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
    render()


ft.run(main)
