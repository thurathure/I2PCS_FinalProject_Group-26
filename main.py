import flet as ft

def main(page: ft.Page):
    page.title = "U-Lock"
    locked = True
    label = ft.Text("Locked", size=40, color = "red")

    def toggle(e):
        nonlocal locked
        locked = not locked
        label.value = "Locked" if locked else "Unlocked"
        label.color = "red" if locked==True else "green"
        page.update()

    page.add(label, ft.Button("Toggle", on_click=toggle))

ft.run(main)