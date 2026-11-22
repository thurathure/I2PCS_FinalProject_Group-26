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
    "Taitung":           (22.76, 121.14),
    "Penghu County":     (23.57, 119.58),
    "Kinmen County":     (24.44, 118.32),
    "Lienchiang County": (26.16, 119.95),
}

def get_weather(lat, lon):
    params = {
        "latitude": lat,
        "longitude": lon,
        "current": "temperature_2m,relative_humidity_2m,wind_speed_10m,weather_code",
        "hourly": "precipitation_probability",
        "forecast_hours": 12,
        "timezone": "auto",
    }
    response = requests.get(URL, params=params, timeout=10)
    response.raise_for_status()
    return response.json()

def code_to_condition(code):
    if code in (0, 1):
        return "sunny"
    elif code == 2:
        return "cloudy"
    elif code in (3, 45, 48):
        return "dark_cloud"
    elif 51 <= code <= 67 or 80 <= code <= 82:
        return "rain"
    elif 95 <= code <= 99:
        return "thunderstorm"
    else:
        return "dark_cloud"

def first_rain_time(hourly, threshold=50):
    for t, prob in zip(hourly["time"], hourly["precipitation_probability"]):
        if prob >= threshold:
            return t[11:16]
    return None

def get_weather_summary(lat, lon):
    data = get_weather(lat, lon)
    current = data["current"]
    return {
        "temp": round(current["temperature_2m"]),
        "wind": round(current["wind_speed_10m"]),
        "humidity": current["relative_humidity_2m"],
        "condition": code_to_condition(current["weather_code"]),
        "rain_time": first_rain_time(data["hourly"]),
    }

if __name__ == "__main__":
    lat, lon = CITIES["Taipei City"]
    print(get_weather_summary(lat, lon))