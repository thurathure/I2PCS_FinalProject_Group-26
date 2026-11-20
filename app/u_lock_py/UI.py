import flet as ft
from datetime import datetime

# =====================================================================
# 1. COLOR AND WEATHER VARIABLES
# =====================================================================
INK = "#0B1318"
TEXT = "#FFFFFF"
MUTED = "#8FA3AE"
ICE = "#CFEFFC"
ICE_DEEP = "#5BB3E0"
AMBER = "#F5B041"
GREEN = "#3DDC84"
RED = "#FF5A5F"
YELLOW = "#F4D35E"
MINT = "#CFF7DE"
MINT_DEEP = "#3DDC84"

PAD = 20 
GAP_S, GAP_M = 8, 16
RADIUS_CARD = 20

BOLD = ft.FontWeight.BOLD
SEMI = ft.FontWeight.W_600
THIN = ft.FontWeight.W_200

CENTER = ft.Alignment(0, 0)
TOP = ft.Alignment(0, -1)
BOTTOM = ft.Alignment(0, 1)

SKY = {
    "sunny":        ["#1B6FE0", "#6DB8F7"],
    "cloudy":       ["#56697D", "#93A5B8"],
    "dark_cloud":   ["#1F252B", "#3C444C"],
    "rain":         ["#1F3347", "#4F6A82"],
    "thunderstorm": ["#0B1318", "#1B2A33"],
}
CONDITIONS = list(SKY.keys())

WEATHER_TEXT = {
    "sunny":        ("Sunny", "Clear skies today"),
    "cloudy":       ("Cloudy", "Dry for now"),
    "dark_cloud":   ("Overcast", "Rain could arrive soon"),
    "rain":         ("Rain", "Take your umbrella"),
    "thunderstorm": ("Thunderstorm", "Severe weather in your area"),
}


# =====================================================================
# 2. TEMPLATE DESIGN
# =====================================================================
def battery_status(percent):
    if percent == 0:
        return "Change your battery", RED
    elif percent <= 20:
        return "Replace the battery soon", AMBER
    elif percent <= 40:
        return "Battery is getting low", YELLOW
    else:
        return "Battery is healthy", GREEN

def gap(height):
    return ft.Container(height=height)

def with_gaps(items, height=GAP_M):
    out = []
    for item in items:
        if item is None:
            continue
        if out:
            out.append(gap(height))
        out.append(item)
    return out

def small_label(text, color=MUTED):
    return ft.Text(text.upper(), size=10, weight=BOLD, color=color)

def tint(hex_color, opacity):
    return f"#{round(opacity * 255):02X}{hex_color.lstrip('#')}"

def border(color, width=1):
    side = ft.BorderSide(width, color)
    return ft.Border(top=side, right=side, bottom=side, left=side)

def card(content, on_click=None, bg=None, outline=None, radius=RADIUS_CARD, h=16, v=14):
    return ft.Container(
        content=content,
        padding=ft.Padding(left=h, top=v, right=h, bottom=v),
        bgcolor=bg or tint("#FFFFFF", 0.07),
        border=border(outline or tint("#FFFFFF", 0.10)),
        border_radius=radius,
        on_click=on_click,
    )

def icon_box(icon, color, bg, size=40):
    return ft.Container(
        width=size, height=size, border_radius=12, bgcolor=bg, alignment=CENTER,
        content=ft.Icon(icon, color=color, size=20),
    )

# =====================================================================
# 3. DATA
# =====================================================================
class FakeUmbrella:
    def __init__(self):
        self.locked = True
        self.battery = 82

    def toggle(self):
        self.locked = not self.locked

    def drain(self):
        self.battery = max(0, self.battery - 10)

state = {
    "tab": "control",
    "condition": "thunderstorm",
    "temp": 15,
    "location": "Your location",
    "wind": 18,
    "humidity": 78,
    "rain_time": "16:00",
    "connected": True,
    "banner_visible": True,
}

# =====================================================================
# 4. SECTIONS
# =====================================================================
def header(state, act):
    _, bat_color = battery_status(state["battery"])
    left = ft.Row(
        [
            icon_box(ft.Icons.UMBRELLA, INK, ICE),
            ft.Column(
                [
                    ft.Text("UmbrellaOS", size=15, weight=BOLD, color=TEXT),
                    ft.Row(
                        [
                            ft.Text(state["location"], size=12, color=MUTED),
                            ft.Icon(ft.Icons.CHEVRON_RIGHT, size=14, color=MUTED),
                        ],
                        spacing=0,
                    ),
                ],
                spacing=2,
            ),
        ],
        spacing=12,
    )
    battery_pill = card(
        ft.Row(
            [
                ft.Text(f"{state['battery']}%", size=13, weight=BOLD, color=TEXT),
                ft.Icon(ft.Icons.BATTERY_FULL, size=16, color=bat_color),
            ],
            spacing=6,
        ),
        radius=14, h=12, v=8,
    )
    return ft.Row(
        [left, battery_pill],
        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
        vertical_alignment=ft.CrossAxisAlignment.CENTER,
    )

def lock_section(state, act):
    locked = state["locked"]
    connected = state["connected"]

    status = ft.Row(
        [
            ft.Container(
                width=44, height=44, border_radius=22, alignment=CENTER,
                bgcolor=tint("#FFFFFF", 0.06),
                border=border(tint("#FFFFFF", 0.12)),
                content=ft.Icon(ft.Icons.LOCK if locked else ft.Icons.LOCK_OPEN, color=ICE if locked else GREEN, size=20),
            ),
            ft.Column(
                [
                    small_label("Smart lock"),
                    ft.Text("Locked" if locked else "Unlocked", size=26, weight=BOLD, color=TEXT),
                ],
                spacing=0,
            ),
        ],
        alignment=ft.MainAxisAlignment.CENTER,
        spacing=12,
    )
    if not connected:
        colors = ["#4A5963", "#34424B"]
    elif locked:
        colors = [ICE, ICE_DEEP]
    else:
        colors = [MINT, MINT_DEEP]
    action = "Unlock" if locked else "Lock"
    hint = "Press to release" if locked else "Press to secure"
    button = ft.Container(
        width=200, height=200, border_radius=100, alignment=CENTER,
        bgcolor=tint("#FFFFFF", 0.04),
        border=border(tint("#FFFFFF", 0.08)),
        content=ft.Container(
            width=164, height=164, border_radius=82, alignment=CENTER,
            gradient=ft.LinearGradient(begin=TOP, end=BOTTOM, colors=colors),
            shadow=ft.BoxShadow(blur_radius=50, color=tint(ICE_DEEP, 0.35), offset=ft.Offset(0, 10)),
            on_click=act["toggle"] if connected else None,
            content=ft.Column(
                [
                    ft.Icon(ft.Icons.LOCK_OPEN if locked else ft.Icons.LOCK, color=INK, size=30),
                    ft.Text(action, size=20, weight=BOLD, color=INK),
                    ft.Text(hint, size=10, color=tint(INK, 0.6)),
                ],
                spacing=4,
                alignment=ft.MainAxisAlignment.CENTER,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            ),
        ),
    )

    pill = card(
        ft.Row(
            [
                ft.Container(width=8, height=8, border_radius=4, bgcolor=GREEN if connected else RED),
                ft.Icon(ft.Icons.BLUETOOTH, size=14, color=MUTED),
                ft.Text("Connected" if connected else "Disconnected", size=11, weight=SEMI, color=TEXT),
            ],
            spacing=8,
            alignment=ft.MainAxisAlignment.CENTER,
            tight=True,
        ),
        radius=999, h=14, v=8,
    )

    return ft.Column(
        [status, gap(GAP_M), button, gap(GAP_M), pill],
        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        spacing=0,
    )

def advisory_card(state, act):
    # SLOT: weather feature. Shown only for severe weather.
    if state["condition"] != "thunderstorm":
        return None
    return card(
        ft.Row(
            [
                icon_box(ft.Icons.WARNING_AMBER, AMBER, tint(AMBER, 0.15)),
                ft.Column(
                    [
                        small_label("Severe weather advisory", AMBER),
                        ft.Text("Consider staying indoors today for your safety.", size=13, weight=SEMI, color=TEXT),
                    ],
                    spacing=2,
                    expand=True,
                ),
                ft.Icon(ft.Icons.CHEVRON_RIGHT, color=MUTED, size=18),
            ],
            spacing=12,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
        ),
        bg=tint(AMBER, 0.10), outline=tint(AMBER, 0.30),
    )

def weather_summary(state, act):
    title, subtitle = WEATHER_TEXT[state["condition"]]
    left = ft.Container(
        on_click=act["cycle"],
        content=ft.Column(
            [
                small_label(f"Today · {datetime.now().strftime('%H:%M')}"),
                ft.Text(f"{state['temp']}°", size=72, weight=THIN, color=TEXT),
            ],
            spacing=0,
        ),
    )
    right = ft.Column(
        [
            ft.Text(title, size=15, weight=BOLD, color=TEXT),
            ft.Text(subtitle, size=11, color=MUTED, text_align=ft.TextAlign.RIGHT),
        ],
        spacing=2,
        horizontal_alignment=ft.CrossAxisAlignment.END,
    )
    return ft.Row(
        [left, right],
        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
        vertical_alignment=ft.CrossAxisAlignment.END,
    )

def conditions_card(state, act):
    def stat(icon, value):
        return ft.Row([ft.Icon(icon, size=14, color=MUTED), ft.Text(value, size=11, color=MUTED)], spacing=4)

    return card(
        ft.Row(
            [
                ft.Column(
                    [
                        small_label("Local conditions"),
                        ft.Text(f"Rain expected around {state['rain_time']}", size=14, weight=SEMI, color=TEXT),
                    ],
                    spacing=2,
                    expand=True,
                ),
                stat(ft.Icons.AIR, f"{state['wind']} km/h"),
                stat(ft.Icons.WATER_DROP, f"{state['humidity']}%"),
                ft.Icon(ft.Icons.CHEVRON_RIGHT, color=MUTED, size=18),
            ],
            spacing=10,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
        ),
    )


def rain_banner(state, act):
    if not state["banner_visible"] or state["condition"] not in ("rain", "thunderstorm"):
        return None
    body = ft.Column(
        [
            ft.Row(
                [
                    ft.Text("UmbrellaOS", size=11, weight=BOLD, color=TEXT),
                    ft.Text("now", size=10, color=MUTED),
                ],
                spacing=8,
            ),
            ft.Text(
                "Rain predicted today — Don’t forget to bring your umbrella!",
                size=12, color=tint("#FFFFFF", 0.8),
            ),
        ],
        spacing=2,
        expand=True,
    )
    return card(
        ft.Row(
            [
                icon_box(ft.Icons.CLOUD, ICE, tint("#FFFFFF", 0.08), size=36),
                body,
                ft.IconButton(ft.Icons.CLOSE, icon_size=16, icon_color=MUTED, on_click=act["close_banner"]),
            ],
            spacing=12,
            vertical_alignment=ft.CrossAxisAlignment.START,
        ),
        h=12, v=10,
    )