import flet as ft
from datetime import datetime
class FakeUmbrella:
    def __init__(self):
        self.locked = True
        self.battery = 82

    def toggle(self):
        self.locked = not self.locked

    def drain(self):                       # for testing only
        self.battery = max(0, self.battery - 10)

def battery_status(percent):
    if percent==0:
        return "Change your battery", "yellow"
    elif percent <= 20:
        return "Replace the battery soon", "red"
    elif 20<percent<=40 :                 
        return "Battery is getting low", "orange"
    else:
        return "Battery is healthy", "green"

def main(page: ft.Page):
    page.title = "U-Lock"
    umbrella = FakeUmbrella()

    lock_label = ft.Text("Locked", size=40, color="red")
    battery_text = ft.Text("", size=20)
    battery_bar = ft.ProgressBar(value=0, width=300)
    battery_note = ft.Text("")

    def refresh():
        lock_label.value = "Locked" if umbrella.locked else "Unlocked"
        lock_label.color = "red" if umbrella.locked else "green"

        message, color = battery_status(umbrella.battery)
        battery_text.value = f"Battery: {umbrella.battery}%"
        battery_bar.value = umbrella.battery / 100
        battery_bar.color = color
        battery_note.value = message
        battery_note.color = color
        page.update()

    def on_toggle(e):
        umbrella.toggle()
        refresh()

    def on_drain(e):
        umbrella.drain()
        refresh()

    page.add(
        lock_label,
        ft.Button("Toggle", on_click=on_toggle),
        battery_text,
        battery_bar,
        battery_note,
        ft.Button("Drain battery (test)", on_click=on_drain),
    )
    refresh()

ft.run(main)