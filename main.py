"""
FastAPI Server for the Infinite Choose-Your-Own-Adventure Engine.
Hosts the game API, state management, procedural asset rendering, and static UI.
"""
import os
import uuid
from typing import Dict, Any
from fastapi import FastAPI, HTTPException, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from models import NewGameRequest, TurnActionRequest, TurnActionResponse, GameState
from narrative_engine import (
    ProceduralAdventureDirector, execute_turn, GAME_SESSIONS
)
from visual_engine import ART_STYLES, generate_svg_portrait, generate_svg_scene


app = FastAPI(
    title="Infinite CYOA Engine",
    description="Infinite emergent choose-your-own-adventure engine with consistent art generation and dynamic state tracking.",
    version="1.0.0"
)

# CORS middleware for cross-origin or local dev access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

STATIC_DIR = os.path.join(os.path.dirname(__file__), "static")
os.makedirs(STATIC_DIR, exist_ok=True)


@app.get("/api/styles")
def get_art_styles():
    """Returns available art styles with their descriptions and color accents."""
    return [
        {
            "name": name,
            "prefix": data["prefix"],
            "accent_color": data["accent_color"],
            "bg_color": data["bg_color"]
        }
        for name, data in ART_STYLES.items()
    ]


@app.post("/api/game/new", response_model=TurnActionResponse)
def start_new_game(req: NewGameRequest):
    """Initializes a new infinite adventure with consistent player DNA and opening quest."""
    session_id = str(uuid.uuid4())
    theme = req.custom_theme if req.theme == "Custom" and req.custom_theme else req.theme
    req.theme = theme
    return ProceduralAdventureDirector.generate_opening(req, session_id)


@app.post("/api/game/action", response_model=TurnActionResponse)
async def perform_action(req: TurnActionRequest):
    """Executes a player choice or custom action, mutating the plot, inventory, and quest."""
    try:
        return await execute_turn(req)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/api/game/state/{session_id}")
def get_state(session_id: str):
    """Fetches the full state of an active adventure."""
    state = GAME_SESSIONS.get(session_id)
    if not state:
        raise HTTPException(status_code=404, detail="Session not found")
    return state


@app.get("/api/game/character-svg/{session_id}/{character_name}")
def get_character_portrait_svg(session_id: str, character_name: str):
    """Returns an SVG procedural avatar for a character."""
    state = GAME_SESSIONS.get(session_id)
    if not state:
        raise HTTPException(status_code=404, detail="Session not found")

    target_dna = None
    if state.player.name.lower() == character_name.lower() and state.player.visual_dna:
        target_dna = state.player.visual_dna
    else:
        for c in state.characters:
            if c.name.lower() == character_name.lower() and c.visual_dna:
                target_dna = c.visual_dna
                break

    if not target_dna:
        raise HTTPException(status_code=404, detail="Character visual DNA not found")

    svg_content = generate_svg_portrait(target_dna, state.art_style)
    return Response(content=svg_content, media_type="image/svg+xml")


@app.get("/api/game/scene-svg/{session_id}")
def get_scene_svg(session_id: str):
    """Returns an instant widescreen procedural SVG scene illustration."""
    state = GAME_SESSIONS.get(session_id)
    if not state:
        raise HTTPException(status_code=404, detail="Session not found")

    chars = [state.player.visual_dna]
    for c in state.characters:
        if c.visual_dna:
            chars.append(c.visual_dna)

    svg_content = generate_svg_scene(
        scene_title=state.last_scene_title or "The Uncharted Path",
        location=state.last_location or "Unknown Expanse",
        art_style=state.art_style,
        characters=chars,
        seed=state.current_image_seed or 42
    )
    return Response(content=svg_content, media_type="image/svg+xml")


@app.get("/api/game/export/{session_id}")
def export_chronicle(session_id: str):
    """Exports the player's entire emergent story as a Markdown chronicle."""
    state = GAME_SESSIONS.get(session_id)
    if not state:
        raise HTTPException(status_code=404, detail="Session not found")

    lines = [
        f"# CHRONICLES OF {state.player.name.upper()}",
        f"**Theme:** {state.theme} | **Art Style:** {state.art_style}",
        f"**Archetype:** {state.player.archetype} | **Turns Lived:** {state.current_turn}",
        f"**Final Quest Status:** {state.current_quest.title if state.current_quest else 'None'} ({state.current_quest.stage if state.current_quest else ''})",
        "",
        "## INVENTORY DISCOVERED",
    ]
    for item in state.inventory:
        lines.append(f"- **{item.name}** ({item.category}): {item.description}")

    lines.append("")
    lines.append("## DRAMATIS PERSONAE")
    for char in state.characters:
        lines.append(f"- **{char.name}** ({char.role}): Affinity {char.affinity}%. {char.notes}")

    lines.append("")
    lines.append("## THE CHRONICLE OF TURNS")
    for node in state.history:
        lines.append(f"### Turn {node.turn}: {node.scene_title}")
        lines.append(f"*Location: {node.location}*")
        if node.choice_taken:
            lines.append(f"> **Choice Taken:** {node.choice_taken}")
        lines.append("")
        lines.append(node.narrative)
        lines.append("")

    return Response(content="\n".join(lines), media_type="text/markdown")


@app.get("/")
def serve_index():
    """Serves the main application UI."""
    index_path = os.path.join(STATIC_DIR, "index.html")
    if os.path.exists(index_path):
        return FileResponse(index_path)
    return {"message": "CYOA Engine Backend Online. Please ensure static files are installed."}


@app.get("/style.css")
def get_style_css():
    return FileResponse(os.path.join(STATIC_DIR, "style.css"))


@app.get("/audio.js")
def get_audio_js():
    return FileResponse(os.path.join(STATIC_DIR, "audio.js"))


@app.get("/app.js")
def get_app_js():
    return FileResponse(os.path.join(STATIC_DIR, "app.js"))


# Mount static assets
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


if __name__ == "__main__":
    import uvicorn
    print("\n" + "=" * 60)
    print("  INFINITE CHOOSE-YOUR-OWN-ADVENTURE ENGINE")
    print("  Consistent Art | Emergent Narrative | Dynamic Sidebar")
    print("  Serving at: http://localhost:8000")
    print("=" * 60 + "\n")
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
