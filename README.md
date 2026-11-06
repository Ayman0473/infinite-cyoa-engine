# Infinite Choose-Your-Own-Adventure Engine 🌌⚔️

An infinite, emergent choose-your-own-adventure engine with real-time consistent art generation, dynamic state mutation, and interactive HUD tracking.

![Python](https://img.shields.io/badge/Python-3.10%2B-blue?logo=python)
![FastAPI](https://img.shields.io/badge/FastAPI-0.110%2B-009688?logo=fastapi)
![License](https://img.shields.io/badge/License-MIT-green)

---

## ✨ Features

- **Emergent Branching Narrative**: Choices genuinely alter plot direction, NPC relationships, quests, and world conditions. No fixed rails or pre-scripted endings.
- **Custom Freeform Actions**: In addition to dynamic context choices, type any custom action (e.g., *"I inspect the ancient runes with my lens"* or *"I offer the guard a bribe"*).
- **Consistent Art Style & Character DNA**:
  - Persistent character visual tokens (hair, eyes, facial traits, gear, apparel).
  - Seed-anchored art styles: Dark Fantasy Graphic Novel, Cyberpunk Synthwave, High Fantasy Watercolor, Cosmic Void, Cinematic Anime, and Medieval Woodcut.
  - Zero-latency rendering pipeline with instant procedural SVG scene fallback and real-time AI image cross-fading.
- **Dynamic Sidebar HUD**:
  - **Current Quest**: Multi-stage tracking with auto-updating objectives and progress bar.
  - **Inventory Grid**: Slot-based management. Inspect lore or use items directly in the current scene.
  - **Character Codex**: Catalog of discovered NPCs with visual avatars and live affinity meters.
  - **Player Status**: Health, energy, and conditions (*Vigilant*, *Wounded*, *Ether-touched*).
- **Dual Engine Architecture**:
  - **Built-in Procedural Director**: Works 100% offline with zero configuration or API keys required.
  - **Live AI Mode**: Optional Gemini API key support via in-game settings modal (`⚙️`).
- **Tactile Procedural Audio**: Ambient synthesizers and feedback sound effects via Web Audio API.

---

## 🚀 Quick Start

### 1. Clone the Repository
```bash
git clone https://github.com/YOUR_USERNAME/infinite-cyoa-engine.git
cd infinite-cyoa-engine
```

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Run the Application
**On Windows:**
Double-click `run.bat` or run:
```bash
python main.py
```

Open your browser to:
**[http://localhost:8000](http://localhost:8000)**

---

## 📁 Project Structure

```
├── main.py                 # FastAPI backend, static mounting, SVG & chronicle export
├── narrative_engine.py     # Emergent narrative director & state mutation logic
├── visual_engine.py        # Consistent Art Style manager & procedural SVG generators
├── models.py               # Pydantic schemas (GameState, Quest, Inventory, Character)
├── requirements.txt        # Python package requirements
├── run.bat                 # One-click Windows startup script
├── .gitignore              # Ignored files
└── static/
    ├── index.html          # Cyber-Fantasy HUD interface
    ├── style.css           # Glassmorphism theme, animations & responsive layout
    ├── app.js              # Frontend state manager and event handling
    └── audio.js            # Procedural Web Audio engine
```

---

## 📜 License
MIT License. Free to use, modify, and distribute.
