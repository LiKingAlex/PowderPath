import time
import json
import requests
from typing import Optional, Dict, Any

NOMINATIM_URL = "https://nominatim.openstreetmap.org/search"


def geocode_place(query: str, country_codes: str = "ca", limit: int = 5) -> list[Dict[str, Any]]:
    """
    Geocode a place name using OpenStreetMap Nominatim (no API key).
    Returns a list of candidates (best first).
    """
    headers = {
        # Use a real User-Agent per Nominatim policy; replace with your project name/email if you want.
        "User-Agent": "ski-map-ontario/1.0 (educational project)",
        "Accept": "application/json",
    }
    params = {
        "q": query,
        "format": "jsonv2",
        "addressdetails": 1,
        "limit": limit,
        "countrycodes": country_codes,  # restrict to Canada by default
    }

    resp = requests.get(NOMINATIM_URL, params=params, headers=headers, timeout=15)
    resp.raise_for_status()
    return resp.json()


def pick_best_candidate(candidates: list[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    """
    Picks the top candidate (Nominatim already ranks results),
    but you could add custom scoring here if you want.
    """
    return candidates[0] if candidates else None


def to_resort_snippet(name: str, city_hint: str, lat: float, lng: float) -> Dict[str, Any]:
    """
    Creates a dict you can paste into your resorts list.
    """
    return {
        "name": name,
        "city": city_hint or "Ontario",
        "lat": round(lat, 6),
        "lng": round(lng, 6),
        "difficulty": "Beginner–Expert",
        "description": ""
    }


def main():
    resort_name = input("Resort name (e.g., Blue Mountain): ").strip()
    if not resort_name:
        print("No input.")
        return

    # Make the query more specific for better results
    query = f"{resort_name} ski resort Ontario"

    print(f"\nSearching: {query}\n")
    candidates = geocode_place(query)

    if not candidates:
        print("No results found. Try adding a city: e.g., 'Blue Mountain Collingwood ski resort'.")
        return

    # Show top candidates
    for i, c in enumerate(candidates, start=1):
        display = c.get("display_name", "")
        lat = c.get("lat")
        lon = c.get("lon")
        print(f"{i}. {display}")
        print(f"   lat={lat}, lon={lon}\n")

    best = pick_best_candidate(candidates)
    lat = float(best["lat"])
    lng = float(best["lon"])
    display_name = best.get("display_name", "")

    # Simple city hint from address
    addr = best.get("address", {})
    city_hint = addr.get("city") or addr.get("town") or addr.get("village") or addr.get("county") or "Ontario"

    print("Best match:")
    print(display_name)
    print(f"Latitude:  {lat}")
    print(f"Longitude: {lng}")

    print("\nJSON snippet for resorts.py:")
    snippet = to_resort_snippet(resort_name, city_hint, lat, lng)
    print(json.dumps(snippet, indent=2))

    # Be polite to Nominatim if you plan to call repeatedly
    time.sleep(1)


if __name__ == "__main__":
    main()
