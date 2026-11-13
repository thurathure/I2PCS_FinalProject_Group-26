import time
import requests

URL = "https://api.open-meteo.com/v1/forecast"

CITIES = {
    # Special Municipalities
    "Taipei City":       (25.03, 121.56),
    "New Taipei City":   (25.01, 121.46),
    "Taoyuan City":      (24.99, 121.30),
    "Taichung City":     (24.15, 120.67),
    "Tainan City":       (23.00, 120.22),
    "Kaohsiung City":    (22.63, 120.30),
    
    # Provincial Cities
    "Keelung City":      (25.13, 121.74),
    "Hsinchu City":      (24.80, 120.97),
    "Chiayi City":       (23.48, 120.44),
    
    # Counties
    "Hsinchu County":    (24.83, 121.01),
    "Miaoli County":     (24.56, 120.82),
    "Changhua County":   (24.05, 120.54),
    "Nantou County":     (23.90, 120.68),
    "Yunlin County":     (23.71, 120.54),
    "Chiayi County":     (23.46, 120.29),
    "Pingtung County":   (22.68, 120.48),
    "Yilan County":      (24.75, 121.75),
    "Hualien County":    (23.99, 121.61),
    "Taitung":           (22.76, 121.14),  # Blank 1 filled in
    "Penghu County":     (23.57, 119.58),
    "Kinmen County":     (24.44, 118.32),
    "Lienchiang County": (26.16, 119.95),
}

def get_weather(lat, lon):
    params = {
        "latitude": lat,
        "longitude": lon,    # blank 2: which variable goes here?
        "current": "temperature_2m,relative_humidity_2m,wind_speed_10m,weather_code",
        "timezone": "auto",
    }
    
lat, lon = CITIES["Taipei City"]
print(get_weather(lat, lon))