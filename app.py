import streamlit as st
import folium
from streamlit_folium import st_folium

from data.resorts import ONTARIO_SKI_RESORTS

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
