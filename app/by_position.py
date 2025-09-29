import requests
import time
from shapely.geometry import Point, shape
from config import _PLACES_API_KEY
import math

# ========== CONFIG ==========
CITY_NAME = "Cordoba"
GOOGLE_API_KEY = _PLACES_API_KEY
SEARCH_TEXT = f"Agencia inmobiliaria en {CITY_NAME}"
SEARCH_RADIUS = 1500   # meters
GRID_SPACING = 0.02    # degrees (about 2km at Lisbon's latitude)
# ============================

# Step 1: Get Lisbon's polygon from OpenStreetMap (Overpass API)
def get_city_polygon(city_name):
    url = "https://overpass-api.de/api/interpreter"
    query = f"""
    [out:json];
    relation["name"="{city_name}"]["boundary"="administrative"]["admin_level"="8"];
    out geom;
    """
    response = requests.get(url, params={"data": query})
    data = response.json()
    print(data)

    # Extract polygon coordinates
    for element in data["elements"]:
        if "members" in element:
            for m in element["members"]:
                if "geometry" in m:
                    coords = [(pt["lon"], pt["lat"]) for pt in m["geometry"]]
                    return shape({"type": "Polygon", "coordinates": [coords]})
    return None


# Step 2: Generate grid points over bounding box
def generate_grid(polygon, spacing):
    minx, miny, maxx, maxy = polygon.bounds
    lat = miny
    points = []
    while lat <= maxy:
        lon = minx
        while lon <= maxx:
            p = Point(lon, lat)
            if polygon.contains(p):
                points.append((lat, lon))
            lon += spacing
        lat += spacing
    return points


# Step 3: Query Google Places API (New)
def search_places(lat, lon, radius, api_key, text_query):
    url = f"https://places.googleapis.com/v1/places:searchText"
    headers = {"Content-Type": "application/json", "X-Goog-Api-Key": api_key}
    payload = {
        "textQuery": text_query,
        "locationBias": {
            "circle": {
                "center": {"latitude": lat, "longitude": lon},
                "radius": radius
            }
        }
    }
    all_results = []
    while True:
        r = requests.post(url, headers=headers, json=payload)
        data = r.json()
        if "places" in data:
            all_results.extend(data["places"])
        if "nextPageToken" in data:
            payload["pageToken"] = data["nextPageToken"]
            time.sleep(2)  # wait before next page
        else:
            break
    return all_results


# Step 4: Collect agencies inside polygon
def main():
    polygon = get_city_polygon(CITY_NAME)
    if not polygon:
        print("❌ Could not fetch city polygon")
        return

    print(f"✅ Got {CITY_NAME} polygon")
    grid_points = generate_grid(polygon, GRID_SPACING)
    print(f"✅ Generated {len(grid_points)} grid points")

    all_places = {}
    for i, (lat, lon) in enumerate(grid_points):
        print(f"🔎 Searching grid {i+1}/{len(grid_points)} at ({lat}, {lon})...")
        results = search_places(lat, lon, SEARCH_RADIUS, GOOGLE_API_KEY, SEARCH_TEXT)
        for place in results:
            pid = place["id"]
            loc = place.get("location", {})
            point = Point(loc.get("longitude", 0), loc.get("latitude", 0))
            if polygon.contains(point):
                all_places[pid] = place
        time.sleep(1)  # avoid hitting rate limits

    print(f"✅ Found {len(all_places)} unique agencies in {CITY_NAME}")

    # Example: print some details
    for pid, place in list(all_places.items())[:10]:
        print(place["displayName"]["text"], "-", place.get("formattedAddress", "No address"))


if __name__ == "__main__":
    main()
