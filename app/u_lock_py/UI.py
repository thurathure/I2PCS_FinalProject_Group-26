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