import httpx
import json

client = httpx.Client(base_url="http://localhost:8000", timeout=10.0)

print("--- 1. Testing Styles ---")
r = client.get("/api/styles")
assert r.status_code == 200, f"Styles failed: {r.status_code}"
styles = r.json()
print(f"Retrieved {len(styles)} art styles.")

print("\n--- 2. Testing New Game (Eldritch Dark Fantasy) ---")
new_payload = {
    "theme": "Eldritch Dark Fantasy",
    "art_style": "Dark Fantasy Graphic Novel",
    "player_name": "Morwenna",
    "player_archetype": "Occultist"
}
r = client.post("/api/game/new", json=new_payload)
assert r.status_code == 200, f"New game failed: {r.status_code}"
data = r.json()
session_id = data["session_id"]
print(f"Session ID: {session_id}")
print(f"Turn: {data['turn']} - {data['scene_title']}")
print(f"Location: {data['location']}")
print(f"Quest: {data['quest_update']['title']} ({data['quest_update']['stage']})")
print(f"Inventory: {[i['name'] for i in data['full_state']['inventory']]}")
print(f"Choices: {[c['text'] for c in data['choices']]}")

print("\n--- 3. Testing Turn Action via Choice ---")
choice_id = data["choices"][0]["id"]
action_payload = {
    "session_id": session_id,
    "choice_id": choice_id
}
r = client.post("/api/game/action", json=action_payload)
assert r.status_code == 200, f"Action choice failed: {r.status_code}"
t2_data = r.json()
print(f"Turn 2: {t2_data['scene_title']}")
print(f"Quest progress: {t2_data['quest_update']['progress_percent']}%")

print("\n--- 4. Testing Custom Freeform Action ---")
custom_payload = {
    "session_id": session_id,
    "custom_action": "I examine the ancient sigil inscribed on the wall with my arcane senses."
}
r = client.post("/api/game/action", json=custom_payload)
assert r.status_code == 200, f"Custom action failed: {r.status_code}"
t3_data = r.json()
print(f"Turn 3 (Custom Action): {t3_data['scene_title']}")
print(f"Narrative response: {t3_data['narrative'][:120]}...")

print("\n--- 5. Testing Item Usage ---")
inv = t3_data["full_state"]["inventory"]
if inv:
    item_to_use = inv[0]["id"]
    use_payload = {
        "session_id": session_id,
        "use_item_id": item_to_use
    }
    r = client.post("/api/game/action", json=use_payload)
    assert r.status_code == 200, f"Item use failed: {r.status_code}"
    t4_data = r.json()
    print(f"Turn 4 (Item Used: {item_to_use}): {t4_data['scene_title']}")

print("\n--- 6. Testing Character SVG ---")
r = client.get(f"/api/game/character-svg/{session_id}/Morwenna")
assert r.status_code == 200 and "image/svg+xml" in r.headers["content-type"], f"Char SVG failed: {r.status_code}"
print("Character SVG fetched OK (length:", len(r.text), "bytes)")

print("\n--- 7. Testing Scene SVG ---")
r = client.get(f"/api/game/scene-svg/{session_id}")
assert r.status_code == 200 and "image/svg+xml" in r.headers["content-type"], f"Scene SVG failed: {r.status_code}"
print("Scene SVG fetched OK (length:", len(r.text), "bytes)")

print("\n--- 8. Testing Chronicle Export ---")
r = client.get(f"/api/game/export/{session_id}")
assert r.status_code == 200 and "text/markdown" in r.headers["content-type"], f"Export failed: {r.status_code}"
print("Chronicle exported OK (length:", len(r.text), "bytes)")

print("\n--- 9. Testing Static Assets ---")
for path in ["/", "/style.css", "/audio.js", "/app.js"]:
    r = client.get(path)
    assert r.status_code == 200, f"Static {path} failed: {r.status_code}"
print("All static assets served successfully!")

print("\n===========================================")
print("  >>> ALL TESTS PASSED WITH 0 ERRORS! <<<")
print("===========================================")

print("\n--- 10. Testing Additional Genres (Cyberpunk & Cosmic) ---")
for genre, style in [("Cyberpunk Synthwave", "Cyberpunk Synthwave"), ("Cosmic Void Eldritch", "Cosmic Void Eldritch")]:
    r = client.post("/api/game/new", json={"theme": genre, "art_style": style, "player_name": "Zero", "player_archetype": "Specialist"})
    assert r.status_code == 200, f"Failed {genre}"
    d = r.json()
    print(f"Genre: {genre} -> Quest: {d['quest_update']['title']} | Seed: #{d['image_seed']}")
print("All genres verified successfully!")

print("\n--- 11. Testing Balanced Classes Integration ---")
for cls_name in ["Runic Scholar", "Ironclad Warden", "Shadow Stalker", "Silver-Tongue Envoy", "Alchemical Medic"]:
    r = client.post("/api/game/new", json={"theme": "Eldritch Dark Fantasy", "art_style": "Dark Fantasy Graphic Novel", "player_name": "TestHero", "player_archetype": cls_name})
    assert r.status_code == 200, f"Failed class {cls_name}"
    resp_data = r.json()
    p = resp_data["player_status"]
    inv = resp_data["full_state"]["inventory"]
    print(f"Class: {cls_name} -> HP: {p['health']}/{p['max_health']}, Energy: {p['energy']}/{p['max_energy']}, Cond: {p['conditions']}, Starter Item: {inv[0]['name']}")
print("All balanced classes tested successfully!")
