import math
import datetime as dt
import requests
import streamlit as st
import folium
from streamlit_folium import st_folium

from data.resorts import ONTARIO_SKI_RESORTS

st.set_page_config(page_title="Ontario Ski Resorts", layout="wide")

st.title("🏔️ Ontario Ski Resorts")
st.caption("Click a resort marker to see photos + weather + estimated busyness. (No paid APIs)")

USER_AGENT = "ski-map-project/1.0 (educational; no api key)"

def get_today_weather(lat, lon):
    url = "https://api.open-meteo.com/v1/forecast"
    params = {
        "latitude": lat,
        "longitude": lon,
        "current": "temperature_2m,wind_speed_10m",
        "hourly": "snowfall,precipitation_probability",
        "forecast_days": 1,
        "timezone": "auto"
    }
    headers = {"User-Agent": USER_AGENT, "Accept": "application/json"}
    r = requests.get(url, params=params, headers=headers, timeout=15)
    r.raise_for_status()
    data = r.json()

    current = data.get("current", {})
    hourly = data.get("hourly", {})

    snowfall_today = sum(hourly.get("snowfall", [])) if hourly.get("snowfall") else 0.0
    precip_probs = hourly.get("precipitation_probability", [])
    precip_peak = max(precip_probs) if precip_probs else None

    return {
        "temp": current.get("temperature_2m"),
        "wind": current.get("wind_speed_10m"),
        "snowfall": round(float(snowfall_today), 2),
        "precip_peak": precip_peak
    }

def estimate_busy(now: dt.datetime, snowfall_cm: float | None) -> str:
    """
    Simple heuristic (MVP):
    - Weekends midday busier
    - Fresh snow increases busyness
    """
    hour = now.hour
    weekend = now.weekday() >= 5

    snow_boost = 0
    if snowfall_cm is not None:
        if snowfall_cm >= 5:
            snow_boost = 2
        elif snowfall_cm >= 1:
            snow_boost = 1

    base = 0
    if 10 <= hour <= 14:
        base = 2
    elif 15 <= hour <= 18:
        base = 1
    else:
        base = 0

    if weekend:
        base += 1

    score = base + snow_boost
    if score >= 4:
        return "High"
    if score >= 2:
        return "Medium"
    return "Low"

def haversine_km(lat1, lon1, lat2, lon2):
    R = 6371.0
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp = math.radians(lat2 - lat1)
    dl = math.radians(lon2 - lon1)
    a = math.sin(dp/2)**2 + math.cos(p1)*math.cos(p2)*math.sin(dl/2)**2
    return 2*R*math.atan2(math.sqrt(a), math.sqrt(1-a))

def find_resort_by_click(lat, lng, resorts):
    # pick closest resort to click (more reliable than tolerance check)
    best = None
    best_d = float("inf")
    for r in resorts:
        d = haversine_km(lat, lng, r["lat"], r["lng"])
        if d < best_d:
            best_d = d
            best = r
    # Only accept if click is reasonably close to a marker (~5km)
    return best if best_d <= 5 else None

# ---------- Layout: left map, right details ----------
left, right = st.columns([2.2, 1.2], gap="large")

with left:
    st.subheader("🗺️ Map")
    center = [44.5, -79.5]
    m = folium.Map(location=center, zoom_start=6, tiles="OpenStreetMap")

    for r in ONTARIO_SKI_RESORTS:
        folium.Marker(
            location=[r["lat"], r["lng"]],
            tooltip=r["name"],
            popup=r["name"],
            icon=folium.Icon(icon="info-sign"),
        ).add_to(m)

    map_data = st_folium(
        m,
        width=None,           # responsive
        height=650,
        returned_objects=["last_object_clicked"]
    )

with right:
    st.subheader("🎿 Resort Details")
    st.write("Click a resort marker to load details here.")

    clicked = map_data.get("last_object_clicked") if map_data else None
    if clicked:
        c_lat = clicked["lat"]
        c_lng = clicked["lng"]
        resort = find_resort_by_click(c_lat, c_lng, ONTARIO_SKI_RESORTS)

        if resort:
            # Picture
            if resort.get("image_url"):
                st.image(resort["image_url"], use_container_width=True)
            else:
                st.info("No image set for this resort yet.")

            st.markdown(f"### {resort['name']}")
            st.caption(f"{resort['city']} • {resort.get('difficulty','')}")

            st.write(resort.get("description", ""))

            # Weather
            try:
                w = get_today_weather(resort["lat"], resort["lng"])
                busy = estimate_busy(dt.datetime.now(), w.get("snowfall"))

                c1, c2 = st.columns(2)
                c1.metric("🌡️ Temp (°C)", w.get("temp"))
                c2.metric("💨 Wind (km/h)", w.get("wind"))
                st.metric("❄️ Snow today (cm)", w.get("snowfall"))
                if w.get("precip_peak") is not None:
                    st.caption(f"🌧️ Peak precip chance today: {w['precip_peak']}%")

                # Busyness
                if busy == "High":
                    st.error("👥 Busy now: High")
                elif busy == "Medium":
                    st.warning("👥 Busy now: Medium")
                else:
                    st.success("👥 Busy now: Low")

                # Quick “ski day” message
                snowfall = w.get("snowfall") or 0
                wind = w.get("wind") or 0
                if snowfall >= 5 and wind < 25:
                    st.success("✅ Great conditions: fresh snow + manageable wind.")
                elif snowfall >= 1:
                    st.info("👍 Decent conditions: some fresh snow possible.")
                else:
                    st.warning("⚠️ Limited fresh snow today (still could be fun).")

            except Exception as e:
                st.warning(f"Weather unavailable right now: {e}")

            # Maps link
            st.link_button(
                "🧭 Open in Google Maps",
                f"https://www.google.com/maps/search/?api=1&query={resort['lat']},{resort['lng']}"
            )
        else:
            st.info("Click directly on a resort marker (not just the map).")
