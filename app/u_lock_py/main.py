import flet as ft

class FakeUmbrella:
    def __init__(self):
        self.locked = True       # state
        self.battery = 82        # state

    def lock(self):
        locked = True    # set locked to True

    def unlock(self):
        lock = False     # set locked to False

    def toggle(self):
        self.locked = not self.locked     # flip locked (hint: it's one line, using `not`)

def main(page: ft.Page):
    umbrella = FakeUmbrella()
    label = ft.Text("Locked", size=40, color="red")

    def on_click(e):
        umbrella.toggle()
        label.value = "Locked" if umbrella.locked else "Unlocked"
        label.color = "red" if umbrella.locked else "green"
        page.update()

    page.add(label, ft.Button("Toggle", on_click=on_click))



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