import streamlit as st
import folium
import requests
from streamlit_folium import st_folium

from data.resorts import ONTARIO_SKI_RESORTS

def get_today_weather(lat, lon):
    """
    Fetches today's weather from Open-Meteo (no API key).
    """
    url = "https://api.open-meteo.com/v1/forecast"
    params = {
        "latitude": lat,
        "longitude": lon,
        "current": "temperature_2m,wind_speed_10m",
        "hourly": "snowfall",
        "forecast_days": 1,
        "timezone": "auto"
    }

    r = requests.get(url, params=params, timeout=10)
    data = r.json()

    current = data.get("current", {})
    hourly = data.get("hourly", {})

    snowfall_today = sum(hourly.get("snowfall", []))

    return {
        "temp": current.get("temperature_2m"),
        "wind": current.get("wind_speed_10m"),
        "snowfall": round(snowfall_today, 2)
    }


st.set_page_config(page_title="Ontario Ski Map", layout="wide")

st.title("🏔️ Ontario Ski Resorts Map")
st.markdown("Interactive map of ski resorts in Ontario — **Python only, no APIs**.")

# Sidebar filter
difficulty_filter = st.sidebar.selectbox(
    "Filter by difficulty",
    ["All", "Beginner", "Intermediate", "Advanced", "Expert"]
)

# Center map on Ontario
map_center = [44.5, -79.5]
m = folium.Map(location=map_center, zoom_start=6, tiles="OpenStreetMap")

for resort in ONTARIO_SKI_RESORTS:
    if difficulty_filter != "All" and difficulty_filter not in resort["difficulty"]:
        continue

    popup_html = f"""
    <b>{resort['name']}</b><br>
    {resort['city']}<br>
    Difficulty: {resort['difficulty']}<br><br>
    {resort['description']}
    """

    folium.Marker(
        location=[resort["lat"], resort["lng"]],
        popup=popup_html,
        tooltip=resort["name"],
        icon=folium.Icon(icon="info-sign")
    ).add_to(m)

# Render map
st_folium(m, width=1100, height=600)
st.divider()
st.subheader("🌤️ Today's Weather at Resorts")
for resort in ONTARIO_SKI_RESORTS:
    weather = get_today_weather(resort["lat"], resort["lng"])

    st.markdown(f"### 🎿 {resort['name']} ({resort['city']})")

    col1, col2, col3 = st.columns(3)

    col1.metric("🌡️ Temperature (°C)", weather["temp"])
    col2.metric("💨 Wind (km/h)", weather["wind"])
    col3.metric("❄️ Snowfall Today (cm)", weather["snowfall"])

    # Simple ski-day heuristic
    if weather["snowfall"] > 5 and weather["wind"] < 25:
        st.success("Great ski conditions today ❄️")
    elif weather["snowfall"] > 1:
        st.info("Decent conditions, check crowds")
    else:
        st.warning("Limited fresh snow today")

    st.markdown("---")
