import os
import requests
import time
from config import SUPABASE_URL, SUPABASE_KEY, GEMINI_KEY

HEADERS = {"apikey": SUPABASE_KEY, "Authorization": "Bearer " + SUPABASE_KEY, "Content-Type": "application/json", "Prefer": "return=minimal"}

def get_cities():
    r = requests.get(SUPABASE_URL + "/rest/v1/cities?select=id,lat,lng,radius_km&active=eq.true", headers=HEADERS)
    return r.json()

def overpass_query(lat, lng, radius_km):
    radius_m = radius_km * 1000
    query = f"""
    [out:json][timeout:180];
    (
      node["amenity"="cafe"](around:{radius_m},{lat},{lng});
      node["amenity"="bar"](around:{radius_m},{lat},{lng});
      node["amenity"="pub"](around:{radius_m},{lat},{lng});
      node["amenity"="restaurant"](around:{radius_m},{lat},{lng});
    );
    out body;
    """
    r = requests.post("https://overpass.kumi.systems/api/interpreter", data={"data": query}, headers={"User-Agent": "VibeSearch/1.0", "Accept": "application/json"}, timeout=180)
    r.raise_for_status()
    return r.json().get("elements", [])

def classify_place(name, tags):
    name_lower = (name or "").lower()
    cuisine = (tags.get("cuisine") or "").lower()
    amenity = (tags.get("amenity") or "").lower()
    
    bar_keywords = ["bar", "pub", "cocktail", "birra", "beer", "wine", "enoteca", "aperitivo", "lounge", "club", "nightclub", "biergarten"]
    restaurant_keywords = ["restaurant", "ristorante", "trattoria", "osteria", "pizzeria", "bistrot", "trattoria", "tavern", "steakhouse", "sushi", "chinese", "indian", "thai", "kebab", "fast_food"]
    
    if amenity in ["bar", "pub", "biergarten"]:
        return "bar"
    if amenity == "restaurant":
        return "restaurant"
    if amenity == "fast_food":
        return "restaurant"
    
    for kw in bar_keywords:
        if kw in name_lower or kw in cuisine:
            return "bar"
    for kw in restaurant_keywords:
        if kw in name_lower or kw in cuisine:
            return "restaurant"
    
    return "cafe"

def generate_descriptions(name, place_type, city_name):
    prompt = f"""You are a travel guide. Write a short description (2-3 sentences) for this place in Bologna, Italy.

Place: {name}
Type: {place_type} (cafe/bar/restaurant)
City: {city_name}

Write in 3 languages, format as JSON:
{{
  "summary_en": "English description",
  "summary_ru": "Russian description",
  "summary_it": "Italian description"
}}

Keep it concise, mention the vibe and what makes it special."""
    
    try:
        r = requests.post(
            "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent",
            json={"contents": [{"parts": [{"text": prompt}]}]},
            params={"key": GEMINI_KEY},
            timeout=30
        )
        r.raise_for_status()
        text = r.json()["candidates"][0]["content"]["parts"][0]["text"]
        import re
        match = re.search(r'\{[^}]+\}', text, re.DOTALL)
        if match:
            import json
            return json.loads(match.group())
    except Exception as e:
        print(f"  ⚠️  Gemini error: {e}")
    
    return {"summary_en": f"{name} is a local {place_type} in {city_name}.", "summary_ru": f"{name} — местное заведение типа {place_type} в {city_name}.", "summary_it": f"{name} è un {place_type} locale a {city_name}."}

def get_wikimedia_image(name):
    try:
        r = requests.get("https://en.wikipedia.org/w/api.php", params={
            "action": "query",
            "titles": name,
            "prop": "pageimages",
            "format": "json",
            "pithumbsize": 400
        }, timeout=10)
        pages = r.json().get("query", {}).get("pages", {})
        for page in pages.values():
            thumb = page.get("thumbnail", {}).get("source")
            if thumb:
                return thumb
    except:
        pass
    return None

def import_city(city):
    city_id = city["id"]
    lat = city["lat"]
    lng = city["lng"]
    radius = city["radius_km"]
    
    print(f"\n🌍 Importing {city_id} (lat={lat}, lng={lng}, radius={radius}km)...")
    
    # Get existing places for this city to avoid duplicates
    r = requests.get(f"{SUPABASE_URL}/rest/v1/places?select=id,name&city=eq.{city_id}", headers=HEADERS)
    existing = {p["name"].lower() for p in r.json()}
    
    # Query Overpass
    print("  📡 Querying Overpass API...")
    elements = overpass_query(lat, lng, radius)
    print(f"  📦 Got {len(elements)} places from Overpass")
    
    imported = 0
    skipped = 0
    
    for elem in elements:
        name = elem.get("tags", {}).get("name")
        if not name or len(name) < 3:
            continue
        
        if name.lower() in existing:
            skipped += 1
            continue
        
        place_type = classify_place(name, elem.get("tags", {}))
        address = elem.get("tags", {}).get("addr:street", "")
        if elem.get("tags", {}).get("addr:housenumber"):
            address += " " + elem["tags"]["addr:housenumber"]
        
        # Generate descriptions
        descriptions = generate_descriptions(name, place_type, city_id)
        
        # Get image
        image_url = get_wikimedia_image(name)
        
        # Insert into Supabase
        payload = {
            "name": name,
            "address": address,
            "latitude": elem["lat"],
            "longitude": elem["lon"],
            "place_type": place_type,
            "city": city_id,
            "image_url": image_url,
            "vibe_attributes": {
                "noise_level": 0.5,
                "laptop_friendly": 0.5,
                "romantic": 0.5,
                "summary": descriptions.get("summary_en", ""),
                "summary_ru": descriptions.get("summary_ru", ""),
                "summary_it": descriptions.get("summary_it", ""),
                "summary_en": descriptions.get("summary_en", "")
            }
        }
        
        try:
            r = requests.post(f"{SUPABASE_URL}/rest/v1/places", json=payload, headers=HEADERS)
            if r.status_code in (200, 201, 204):
                imported += 1
                existing.add(name.lower())
                print(f"  ✅ {name} ({place_type})")
            else:
                print(f"  ❌ {name}: {r.status_code}")
        except Exception as e:
            print(f"  ❌ {name}: {e}")
        
        time.sleep(0.3)  # Rate limit
    
    print(f"\n🎯 {city_id}: imported={imported}, skipped={skipped}")

if __name__ == "__main__":
    cities = get_cities()
    print(f"📋 Found {len(cities)} cities")
    
    for city in cities:
        if city["id"] == "bologna":
            print(f"\n⏭️  Skipping {city['id']} (already imported)")
            continue
        import_city(city)
        time.sleep(2)  # Pause between cities
    
    print("\n🎉 Import complete!")
